"""Command Processor - Gestisce tutti i comandi Twitch con DI esplicita."""

import asyncio
import re
from typing import Optional
from loguru import logger

from main.config import (
    CHAT_COMMAND_PREFIX,
    SONG_REQUEST_COMMAND,
    PLAYLIST_CREATE_COMMAND,
    PLAYLIST_VIEW_COMMAND,
    PLAYLIST_ADD_COMMAND,
    PLAYLIST_REMOVE_COMMAND,
    PLAYLIST_MOVE_COMMAND,
    PLAYLIST_CLEAR_COMMAND,
    PLAYLIST_LIST_COMMAND,
    PLAYLIST_POMPA_COMMAND,
    ADMIN_WHITELIST_COMMAND,
    ADMIN_BLACKLIST_COMMAND,
    ADMIN_UNBLACKLIST_COMMAND,
    ADMIN_WHITELIST_LIST_COMMAND,
    ADMIN_BLACKLIST_LIST_COMMAND,
    ADMIN_SKIP_COMMAND,
    ADMIN_REMOVE_QUEUE_COMMAND,
    ADMIN_QUEUE_INFO_COMMAND,
    ADMIN_CLEAR_QUEUE_COMMAND,
    ANALYTICS_STATS_COMMAND,
    ANALYTICS_TOP_SONGS_COMMAND,
    ANALYTICS_TOP_USERS_COMMAND,
    ANALYTICS_EXPORT_COMMAND,
    ANALYTICS_STORIA_COMMAND,
    MUSIC_VOLUME_COMMAND,
    MUSIC_PAUSE_COMMAND,
    MUSIC_RESUME_COMMAND,
    MUSIC_REPEAT_COMMAND,
    MUSIC_REPEAT_OFF_COMMAND,
    MUSIC_REPEAT_INFINITE_COMMAND,
    MUSIC_REPEAT_STOP_COMMAND,
    MUSIC_NEXT_COMMAND,
    MUSIC_QUEUE_INFO_COMMAND,
    MUSIC_DURATION_COMMAND,
    MUSIC_DURATA_COMMAND,
    MUSIC_WHEN_COMMAND,
    MUSIC_RANDOM_COMMAND,
    UTILITY_HELP_COMMAND,
    UTILITY_VERSION_COMMAND,
    UTILITY_UPTIME_COMMAND,
)
from main.services import CommandServices


class CompiledPattern:
    """Wraps a compiled regex pattern for fast matching."""
    __slots__ = ("regex", "method_name")

    def __init__(self, pattern: str, method_name: str):
        self.regex = re.compile(pattern, re.IGNORECASE)
        self.method_name = method_name


class CommandProcessor:
    """Elabora e gestisce tutti i comandi chat con DI esplicita."""

    def __init__(self, services: CommandServices):
        self.services = services

        prefix = re.escape(CHAT_COMMAND_PREFIX)
        sr_prefix = re.escape(SONG_REQUEST_COMMAND)
        p_create = re.escape(PLAYLIST_CREATE_COMMAND)
        p_view = re.escape(PLAYLIST_VIEW_COMMAND)
        p_add = re.escape(PLAYLIST_ADD_COMMAND)
        p_remove = re.escape(PLAYLIST_REMOVE_COMMAND)
        p_move = re.escape(PLAYLIST_MOVE_COMMAND)
        p_clear = re.escape(PLAYLIST_CLEAR_COMMAND)
        p_list = re.escape(PLAYLIST_LIST_COMMAND)
        p_pompa = re.escape(PLAYLIST_POMPA_COMMAND)
        a_whitelist = re.escape(ADMIN_WHITELIST_COMMAND)
        a_blacklist = re.escape(ADMIN_BLACKLIST_COMMAND)
        a_unblacklist = re.escape(ADMIN_UNBLACKLIST_COMMAND)
        a_whitelist_list = re.escape(ADMIN_WHITELIST_LIST_COMMAND)
        a_blacklist_list = re.escape(ADMIN_BLACKLIST_LIST_COMMAND)
        a_skip = re.escape(ADMIN_SKIP_COMMAND)
        a_remove_queue = re.escape(ADMIN_REMOVE_QUEUE_COMMAND)
        a_queue_info = re.escape(ADMIN_QUEUE_INFO_COMMAND)
        a_clear_queue = re.escape(ADMIN_CLEAR_QUEUE_COMMAND)
        stat_stats = re.escape(ANALYTICS_STATS_COMMAND)
        stat_top_songs = re.escape(ANALYTICS_TOP_SONGS_COMMAND)
        stat_top_users = re.escape(ANALYTICS_TOP_USERS_COMMAND)
        stat_export = re.escape(ANALYTICS_EXPORT_COMMAND)
        stat_storia = re.escape(ANALYTICS_STORIA_COMMAND)
        mus_volume = re.escape(MUSIC_VOLUME_COMMAND)
        mus_pause = re.escape(MUSIC_PAUSE_COMMAND)
        mus_resume = re.escape(MUSIC_RESUME_COMMAND)
        mus_repeat = re.escape(MUSIC_REPEAT_COMMAND)
        mus_repeat_off = re.escape(MUSIC_REPEAT_OFF_COMMAND)
        mus_repeat_infinite = re.escape(MUSIC_REPEAT_INFINITE_COMMAND)
        mus_repeat_stop = re.escape(MUSIC_REPEAT_STOP_COMMAND)
        mus_next = re.escape(MUSIC_NEXT_COMMAND)
        mus_queue_info = re.escape(MUSIC_QUEUE_INFO_COMMAND)
        mus_duration = re.escape(MUSIC_DURATION_COMMAND)
        mus_durata = re.escape(MUSIC_DURATA_COMMAND)
        mus_when = re.escape(MUSIC_WHEN_COMMAND)
        mus_random = re.escape(MUSIC_RANDOM_COMMAND)
        util_help = re.escape(UTILITY_HELP_COMMAND)
        util_version = re.escape(UTILITY_VERSION_COMMAND)
        util_uptime = re.escape(UTILITY_UPTIME_COMMAND)

        raw_patterns = {
            rf"{prefix}{sr_prefix}\s+(.+)$": "cmd_sr",
            rf"{prefix}{p_create}\s+(\w+)$": "cmd_crea",
            rf"{prefix}{p_view}(?:\s+(.+))?$": "cmd_playlist",
            rf"{prefix}{p_add}\s+(\w+)\s+(.+)$": "cmd_aggiungi",
            rf"{prefix}{p_remove}\s+(\w+)\s+(.+)$": "cmd_rimuovi",
            rf"{prefix}{p_move}\s+(\w+)\s+(\d+)\s+(\d+)$": "cmd_sposta",
            rf"{prefix}{p_clear}\s+(\w+)$": "cmd_svuota",
            rf"{prefix}{p_list}": "cmd_lista_playlist",
            rf"{prefix}{p_pompa}(?:\s+(\w+)(?:\s+(\d+))?)?$": "cmd_pompa",
            rf"{prefix}{a_whitelist}\s+(\w+)$": "cmd_whitelist",
            rf"{prefix}{a_blacklist}\s+(\w+)$": "cmd_blacklist",
            rf"{prefix}{a_unblacklist}\s+(\w+)$": "cmd_unblacklist",
            rf"{prefix}{a_whitelist_list}$": "cmd_whitelist_list",
            rf"{prefix}{a_blacklist_list}$": "cmd_blacklist_list",
            rf"{prefix}{a_skip}$": "cmd_skippa",
            rf"{prefix}{a_remove_queue}\s+(\d+)$": "cmd_rimuovi_coda",
            rf"{prefix}{a_queue_info}$": "cmd_coda_info",
            rf"{prefix}{a_clear_queue}$": "cmd_clear_queue",
            rf"{prefix}{stat_stats}$": "cmd_stats",
            rf"{prefix}{stat_top_songs}(?:\s+(\d+))?$": "cmd_top_canzoni",
            rf"{prefix}{stat_top_users}(?:\s+(\d+))?$": "cmd_top_user",
            rf"{prefix}{stat_export}\s+(json|csv)$": "cmd_export_stats",
            rf"{prefix}{mus_volume}\s+(\d+)$": "cmd_volume",
           rf"{prefix}{mus_pause}$": "cmd_pausa",
            rf"{prefix}{mus_resume}$": "cmd_riprendi",
            rf"{prefix}{mus_repeat}(?:\s+(\d))?$": "cmd_repeat",
            rf"{prefix}{mus_repeat_off}$": "cmd_repeat_off",
            rf"{prefix}{mus_repeat_infinite}(?:\s+(\d+))?$": "cmd_ripeti",
            rf"{prefix}{mus_repeat_stop}$": "cmd_stop_ripeti",
           rf"{prefix}{mus_next}$": "cmd_next",
            rf"{prefix}{mus_queue_info}": "cmd_queue_info",
            rf"{prefix}{mus_duration}\s+(.+)$": "cmd_duration",
            rf"{prefix}{mus_durata}\s+(\d+)$": "cmd_durata",
            rf"{prefix}{mus_when}$": "cmd_quando",
            rf"{prefix}{mus_random}(?:\s+(\d+))?$": "cmd_random",
            rf"{prefix}{stat_storia}(?:\s+(\d+))?$": "cmd_storia",
            rf"{prefix}{util_help}(?:\s+(\w+))?$": "cmd_help",
            rf"{prefix}{util_version}$": "cmd_version",
            rf"{prefix}{util_uptime}$": "cmd_uptime",
        }

        self.compiled_commands: list[CompiledPattern] = [
            CompiledPattern(pattern, method) for pattern, method in raw_patterns.items()
        ]

    async def process(self, text: str, username: str, channel_id: str) -> bool:
        """Elabora un messaggio di chat e risponde se è un comando."""
        text_lower = text.lower().strip()

        for compiled in self.compiled_commands:
            match = compiled.regex.match(text_lower)

            if match:
                method_name = compiled.method_name
                method = getattr(self, method_name, None)

                if method:
                    args = list(match.groups())
                    args.append(username)
                    args.append(channel_id)

                    try:
                        response = await method(*args)
                        if response:
                            await self._send_response(response, channel_id)
                            return True
                    except Exception as e:
                        import traceback

                        logger.error(
                            f"Errore nel comando {method_name}: {e}\n"
                            + traceback.format_exc()
                        )
                        try:
                            await self._send_public(
                                channel_id,
                                f"❌ Errore interno ({type(e).__name__}: {e})",
                            )
                        except Exception:
                            pass

        return False

    async def _send_response(self, response, channel_id: str):
        """Invia risposta con rate limiting per liste di messaggi."""
        if isinstance(response, list):
            for i, msg in enumerate(response):
                try:
                    await self._send_public(channel_id, msg)
                    if i < len(response) - 1:
                        await asyncio.sleep(1.5)
                except Exception:
                    continue
        else:
            await self._send_public(channel_id, response)

    async def _send_public(self, channel_id: str, message: str):
        """Invia messaggio pubblico via Twitch."""
        if self.services.bot and hasattr(self.services.bot, "chat_message"):
            await self.services.bot.chat_message.send_public(channel_id, message)

    # =====================================================================
    # PLAYLIST COMMANDS
    # =====================================================================

    async def cmd_crea(self, nome_playlist: str, username: str, channel_id: str):
        """!crea <nome> - Crea una nuova playlist."""
        return await self.services.playlist_commands.cmd_crea(username, nome_playlist)

    async def cmd_playlist(self, nome: str, username: str, channel_id: str):
        """!playlist [nome] - Mostra playlist o canzoni."""
        if nome is None:
            nome = None
        return await self.services.playlist_commands.cmd_playlist(username, nome)

    async def cmd_aggiungi(
        self, nome_playlist: str, query: str, username: str, channel_id: str
    ):
        """!aggiungi <playlist> - Aggiungi canzone corrente."""
        file_path = "unknown"

        return await self.services.playlist_commands.cmd_aggiungi(
            username, nome_playlist, query, file_path, username
        )

    async def cmd_rimuovi(
        self, nome_playlist: str, index_or_name: str, username: str, channel_id: str
    ):
        """!rimuovi <playlist> <posizione> - Rimuovi canzone."""
        return await self.services.playlist_commands.cmd_rimuovi(
            username, nome_playlist, index_or_name
        )

    async def cmd_sposta(
        self, nome_playlist: str, num1: str, num2: str, username: str, channel_id: str
    ):
        """!sposta <playlist> <pos1> <pos2> - Sposta canzoni."""
        return await self.services.playlist_commands.cmd_sposta(
            username, nome_playlist, num1, num2
        )

    async def cmd_svuota(self, nome_playlist: str, username: str, channel_id: str):
        """!svuota <playlist> - Svuota playlist."""
        return await self.services.playlist_commands.cmd_svuota(username, nome_playlist)

    async def cmd_lista_playlist(self, username: str, channel_id: str):
        """!lista_playlist - Mostra tutte le playlist."""
        return await self.services.playlist_commands.cmd_lista_playlist(username)

    async def cmd_pompa(
        self, playlist_name: Optional[str], n_str: Optional[str], username: str, channel_id: str
    ):
        """!pompa [playlist] [n] - Pompa N canzoni random da una playlist."""
        n = int(n_str) if n_str else 5
        return await self.services.playlist_commands.cmd_pompa(username, playlist_name, n, channel_id)

    # =====================================================================
    # ADMIN COMMANDS
    # =====================================================================

    async def cmd_whitelist(self, target_user: str, username: str, channel_id: str):
        """!whitelist <utente> - Aggiungi whitelist."""
        return await self.services.admin_commands.cmd_whitelist(username, target_user)

    async def cmd_blacklist(self, target_user: str, username: str, channel_id: str):
        """!blacklist <utente> - Aggiungi blacklist."""
        return await self.services.admin_commands.cmd_blacklist(username, target_user)

    async def cmd_unblacklist(self, target_user: str, username: str, channel_id: str):
        """!unblacklist <utente> - Rimuovi blacklist."""
        return await self.services.admin_commands.cmd_unblacklist(username, target_user)

    async def cmd_whitelist_list(self, username: str, channel_id: str):
        """!whitelist_list - Mostra whitelist."""
        return await self.services.admin_commands.cmd_whitelist_list(username)

    async def cmd_blacklist_list(self, username: str, channel_id: str):
        """!blacklist_list - Mostra blacklist."""
        return await self.services.admin_commands.cmd_blacklist_list(username)

    async def cmd_skippa(self, username: str, channel_id: str):
        """!skippa - Salta canzone."""
        return await self.services.admin_commands.cmd_skippa(username)

    async def cmd_rimuovi_coda(self, position: str, username: str, channel_id: str):
        """!rimuovi_coda <pos> - Rimuovi dalla coda."""
        return await self.services.admin_commands.cmd_rimuovi_coda(username, position)

    async def cmd_coda_info(self, username: str, channel_id: str):
        """!coda_info - Info coda."""
        return await self.services.admin_commands.cmd_coda_info(username)

    async def cmd_clear_queue(self, username: str, channel_id: str):
        """!clear_queue - Svuota coda."""
        return await self.services.admin_commands.cmd_clear_queue(username)

    # =====================================================================
    # ANALYTICS COMMANDS
    # =====================================================================

    async def cmd_stats(self, username: str, channel_id: str):
        """!stats - Statistiche."""
        return await self.services.analytics_commands.cmd_stats(username)

    async def cmd_top_canzoni(self, n: str, username: str, channel_id: str):
        """!top_canzoni [N] - Top canzoni."""
        n = int(n) if n else 10
        return await self.services.analytics_commands.cmd_top_canzoni(username, n)

    async def cmd_top_user(self, n: str, username: str, channel_id: str):
        """!top_user [N] - Top utenti."""
        n = int(n) if n else 10
        return await self.services.analytics_commands.cmd_top_user(username, n)

    async def cmd_export_stats(self, format: str, username: str, channel_id: str):
        """!export_stats <formato> - Esporta stats."""
        return await self.services.analytics_commands.cmd_export_stats(username, format)

    # =====================================================================
    # MUSIC COMMANDS
    # =====================================================================

    async def cmd_volume(self, level: str, username: str, channel_id: str):
        """!volume <0-100> - Imposta volume."""
        level = int(level)
        return await self.services.music_commands.cmd_volume(username, level)

    async def cmd_pausa(self, username: str, channel_id: str):
        """!pausa - Metti in pausa."""
        return await self.services.music_commands.cmd_pausa(username)

    async def cmd_riprendi(self, username: str, channel_id: str):
        """!riprendi - Riprendi."""
        return await self.services.music_commands.cmd_riprendi(username)

    async def cmd_repeat(self, count: str, username: str, channel_id: str):
        """!repeat [N] - Ripeti."""
        if count is None:
            count = 1
        else:
            count = int(count)

        if count == 0:
            return await self.services.music_commands.cmd_repeat_off(username)

        return await self.services.music_commands.cmd_repeat(username, count)

    async def cmd_repeat_off(self, username: str, channel_id: str):
        """!repeat_off - Disattiva repeat."""
        return await self.services.music_commands.cmd_repeat_off(username)

    async def cmd_ripeti(self, count: str, username: str, channel_id: str):
        """!ripeti [N] - Ripeti canzone (N=1 o vuoto=infinito)."""
        if count is None:
            # Nessun argomento: repeat infinito
            return await self.services.music_commands.cmd_repeat(username, -1)
        else:
            count = int(count)
            if count == 0:
                return await self.services.music_commands.cmd_repeat_off(username)
            return await self.services.music_commands.cmd_repeat(username, count)

    async def cmd_stop_ripeti(self, username: str, channel_id: str):
        """!stop_ripeti - Ferma il repeat."""
        return await self.services.music_commands.cmd_stop_repeat(username)

    async def cmd_next(self, username: str, channel_id: str):
        """!next - Prossima canzone."""
        return await self.services.music_commands.cmd_next(username)

    async def cmd_queue_info(self, username: str, channel_id: str):
        """!queue_info - Info coda."""
        return await self.services.utility_commands.cmd_queue_info(username, channel_id)

    async def cmd_duration(self, query: str, username: str, channel_id: str):
        """!duration <canzone> - Durata canzone."""
        return await self.services.music_commands.cmd_duration(username, query)

    async def cmd_durata(self, position: str, username: str, channel_id: str):
        """!durata <N> - Durata canzone in posizione N nella coda."""
        return await self.services.music_commands.cmd_durata(position, username, channel_id)

    async def cmd_quando(self, username: str, channel_id: str):
        """!quando - Stima quando partirà la tua prossima canzone."""
        return await self.services.music_commands.cmd_quando(username, channel_id)

    async def cmd_random(self, n_str: Optional[str], username: str, channel_id: str):
        """!random [N] - Riproduci N canzoni casuali dalla libreria."""
        n = int(n_str) if n_str else 1
        return await self.services.music_commands.cmd_random(username, n)

    async def cmd_storia(self, n_str: Optional[str], username: str, channel_id: str):
        """!storia [N] - Cronologia ultime N canzoni riprodotte."""
        n = int(n_str) if n_str else 10
        return await self.services.analytics_commands.cmd_storia(username, n)

    # =====================================================================
    # UTILITY COMMANDS
    # =====================================================================

    async def cmd_help(self, *args):
        """!help [comando] - Gestione robusta degli argomenti."""
        logger.debug(f"cmd_help chiamato con args: {args}")

        if len(args) >= 3:
            captured_command, username, channel_id = args[0], args[1], args[2]
        elif len(args) == 2:
            captured_command, username, channel_id = "", args[0], args[1]
        else:
            captured_command, username, channel_id = "", "unknown", "unknown"

        if captured_command is None:
            captured_command = ""

        if captured_command and captured_command.lower() == username.lower():
            captured_command = ""

        logger.debug(
            f"Chiamo utility.cmd_help con username={username}, command='{captured_command}'"
        )

        return await self.services.utility_commands.cmd_help(username, captured_command)

    async def cmd_version(self, username: str, channel_id: str):
        """!version - Versione bot."""
        return await self.services.utility_commands.cmd_version(username)

    async def cmd_uptime(self, username: str, channel_id: str):
        """!uptime - Tempo attività."""
        return await self.services.utility_commands.cmd_uptime(username)
