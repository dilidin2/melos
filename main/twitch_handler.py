#!/usr/bin/env python3
"""
Twitch Handler Module

Gestisce la connessione alla chat di Twitch e l'ascolto dei comandi.
"""

import asyncio
import re
from typing import Optional, Callable
import os
import json

from twitchAPI.twitch import Twitch
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope

from main.config import (
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    OAUTH_REDIRECT_URI,
    TARGET_CHANNEL,
    CHAT_COMMAND_PREFIX,
    SONG_REQUEST_COMMAND,
)
from loguru import logger


class TwitchHandler:
    """Classe per gestire la connessione a Twitch e i comandi chat."""

    def __init__(self):
        """Inizializza il TwitchHandler."""
        self.twitch: Optional[Twitch] = None
        self.chat: Optional[Chat] = None
        self.command_callback: Optional[Callable] = None
        self.command_pattern: str = rf"{re.escape(CHAT_COMMAND_PREFIX)}{re.escape(SONG_REQUEST_COMMAND)}\s+(.+?)$"
        self.multiple_patterns: list[str] = []
        self._connected = False

        # Command processor (opzionale)
        self.command_processor = None

    def set_command_callback(self, callback: Callable, pattern: str = ""):
        """Imposta la callback per i comandi."""
        self.command_callback = callback
        self.command_pattern = (
            pattern
            or rf"{re.escape(CHAT_COMMAND_PREFIX)}{re.escape(SONG_REQUEST_COMMAND)}\s+(.+?)$"
        )

    def set_multiple_commands(self, patterns: list[str], callback: Callable):
        """Imposta multiple comandi con pattern diversi."""
        self.command_callback = callback
        self.multiple_patterns = patterns

    async def _handle_message(self, msg: ChatMessage):
        """Gestisce i messaggi della chat (solo messaggi NON-comando).

        I comandi (!) sono già gestiti da register_command → _handle_sr_command /
        _handle_other_command. Processarli anche qui causerebbe doppio invio.
        """
        text = msg.text.strip()
        if text.startswith(CHAT_COMMAND_PREFIX):
            return

    async def _handle_sr_command(self, cmd):
        """Gestisce il comando !sr che va in coda musicale."""
        query = cmd.parameter.strip() if cmd.parameter else ""
        if query and self.command_callback:
            room_id = cmd.room.room_id if cmd.room else ""
            logger.info(f"Comando ricevuto da {cmd.user.name}: !sr {query[:30]}")
            try:
                await self.command_callback(query, cmd.user.name, room_id)
            except Exception as e:
                logger.error(f"Errore nella callback del comando !sr: {e}")

    async def _handle_other_command(self, cmd):
        """Gestisce tutti gli altri comandi che vanno al command_processor."""
        if self.command_processor:
            text = (
                f"!{cmd.name} {cmd.parameter}".strip()
                if cmd.parameter
                else f"!{cmd.name}"
            )
            room_id = cmd.room.room_id if cmd.room else ""
            logger.info(f"Comando ricevuto da {cmd.user.name}: {text[:50]}")
            try:
                await self.command_processor.process(text, cmd.user.name, room_id)
            except Exception as e:
                logger.error(f"Errore nel command processor: {e}")

    async def connect(self) -> bool:
        """Connetti alla chat di Twitch con OAuth flow."""
        try:
            logger.info("Connessione a Twitch...")

            TOKEN_FILE = "tokens.json"

            # Inizializza l'API Twitch
            self.twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)

            target_scopes = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    t = json.load(f)
                try:
                    await self.twitch.set_user_authentication(
                        t["access_token"], target_scopes, t["refresh_token"]
                    )
                    logger.info("Accesso effettuato tramite tokens.json")
                except:
                    # Se i token nel file sono vecchi o non validi, forziamo il login
                    await self._do_fresh_login(target_scopes, TOKEN_FILE)
            else:
                # Se il file non esiste, primo login assoluto
                await self._do_fresh_login(target_scopes, TOKEN_FILE)

            # Crea l'istanza della chat
            self.chat = await Chat(self.twitch)

            # Aggiungi listener per i messaggi
            self.chat.register_event(ChatEvent.READY, self._on_ready)
            self.chat.register_event(ChatEvent.MESSAGE, self._handle_message)

            # Registra comandi Twitch
            # !sr va al callback per la coda musicale
            self.chat.register_command("sr", self._handle_sr_command)
            # Tutti gli altri vanno al command_processor
            self.chat.register_command("crea", self._handle_other_command)
            self.chat.register_command("playlist", self._handle_other_command)
            self.chat.register_command("aggiungi", self._handle_other_command)
            self.chat.register_command("rimuovi", self._handle_other_command)
            self.chat.register_command("sposta", self._handle_other_command)
            self.chat.register_command("svuota", self._handle_other_command)
            self.chat.register_command("lista_playlist", self._handle_other_command)
            self.chat.register_command("pompa", self._handle_other_command)
            # Admin commands
            self.chat.register_command("whitelist", self._handle_other_command)
            self.chat.register_command("blacklist", self._handle_other_command)
            self.chat.register_command("unblacklist", self._handle_other_command)
            self.chat.register_command("whitelist_list", self._handle_other_command)
            self.chat.register_command("blacklist_list", self._handle_other_command)
            self.chat.register_command("skippa", self._handle_other_command)
            self.chat.register_command("skip", self._handle_other_command)
            self.chat.register_command("rimuovi_coda", self._handle_other_command)
            self.chat.register_command("coda_info", self._handle_other_command)
            self.chat.register_command("clear_queue", self._handle_other_command)
            # Analytics commands
            self.chat.register_command("stats", self._handle_other_command)
            self.chat.register_command("top_canzoni", self._handle_other_command)
            self.chat.register_command("top_user", self._handle_other_command)
            self.chat.register_command("export_stats", self._handle_other_command)
            self.chat.register_command("storia", self._handle_other_command)
            # Music commands
            self.chat.register_command("volume", self._handle_other_command)
            self.chat.register_command("pausa", self._handle_other_command)
            self.chat.register_command("riprendi", self._handle_other_command)
            self.chat.register_command("repeat", self._handle_other_command)
            self.chat.register_command("repeat_off", self._handle_other_command)
            self.chat.register_command("ripeti", self._handle_other_command)
            self.chat.register_command("stop_ripeti", self._handle_other_command)
            self.chat.register_command("next", self._handle_other_command)
            self.chat.register_command("queue_info", self._handle_other_command)
            self.chat.register_command("duration", self._handle_other_command)
            self.chat.register_command("durata", self._handle_other_command)
            self.chat.register_command("quando", self._handle_other_command)
            self.chat.register_command("random", self._handle_other_command)
            # Utility commands
            self.chat.register_command("help", self._handle_other_command)
            self.chat.register_command("version", self._handle_other_command)
            self.chat.register_command("uptime", self._handle_other_command)

            # Avvia la chat
            self.chat.start()

            # Attendi che la chat sia pronta
            await asyncio.sleep(1)

            self._connected = True
            logger.info(f"Connesso al canale: {TARGET_CHANNEL}")
            return True

        except Exception as e:
            logger.error(f"Errore nella connessione Twitch: {e}")
            return False

    async def _do_fresh_login(self, scopes, token_file):
        authenticator = UserAuthenticator(
            self.twitch, scopes, url=OAUTH_REDIRECT_URI or "http://localhost:17563"
        )
        result = await authenticator.authenticate()

        if result:
            access_token, refresh_token = result
            # Salva i token per la prossima volta
            with open(token_file, "w") as f:
                json.dump(
                    {"access_token": access_token, "refresh_token": refresh_token}, f
                )

            await self.twitch.set_user_authentication(
                access_token, scopes, refresh_token
            )
            logger.info("Nuovi token salvati correttamente!")

    async def _on_ready(self, ready_event: EventData):
        """Gestisce l'evento READY quando la chat è pronta."""
        logger.info("Bot pronto, unisco il canale...")
        await ready_event.chat.join_room(TARGET_CHANNEL)

    async def send_message(self, channel_id: str, message: str) -> bool:
        """Invia un messaggio nella chat."""
        try:
            if self.chat:
                # twitchAPI.Chat.send_message vuole il NOME del canale, non l'ID numerico.
                # cmd.room.room_id restituisce un ID numerico tipo "123456789":
                # in quel caso (o se vuoto) usiamo TARGET_CHANNEL come fallback.
                room = (
                    TARGET_CHANNEL
                    if not channel_id or channel_id.isdigit()
                    else channel_id
                )
                await self.chat.send_message(room, message)
                return True
            return False
        except Exception as e:
            logger.error(f"Errore nell'invio messaggio: {e}")
            return False

    async def disconnect(self):
        """Disconnetti da Twitch."""
        try:
            if self.chat:
                self.chat.stop()
            if self.twitch:
                await self.twitch.close()
            self._connected = False
            logger.info("Disconnesso da Twitch")
        except Exception as e:
            logger.error(f"Errore nel disconnettersi: {e}")

    def is_connected(self) -> bool:
        """Ritorna True se connesso."""
        return self._connected
