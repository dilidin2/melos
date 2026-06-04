#!/usr/bin/env python3
"""
Twitch Handler Module

Manages the connection to Twitch chat and command listening.
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
    """Class to manage the Twitch connection and chat commands."""

    def __init__(self):
        """Initializes the TwitchHandler."""
        self.twitch: Optional[Twitch] = None
        self.chat: Optional[Chat] = None
        self.command_callback: Optional[Callable] = None
        self.command_pattern: str = rf"{re.escape(CHAT_COMMAND_PREFIX)}{re.escape(SONG_REQUEST_COMMAND)}\s+(.+?)$"
        self.multiple_patterns: list[str] = []
        self._connected = False

        # Command processor (opzionale)
        self.command_processor = None

    def set_command_callback(self, callback: Callable, pattern: str = ""):
        """Sets the callback for commands."""
        self.command_callback = callback
        self.command_pattern = (
            pattern
            or rf"{re.escape(CHAT_COMMAND_PREFIX)}{re.escape(SONG_REQUEST_COMMAND)}\s+(.+?)$"
        )

    def set_multiple_commands(self, patterns: list[str], callback: Callable):
        """Sets multiple commands with different patterns."""
        self.command_callback = callback
        self.multiple_patterns = patterns

    async def _handle_message(self, msg: ChatMessage):
        """Handles chat messages (only NON-command messages).

        Commands (!) are already handled by register_command → _handle_sr_command /
        _handle_other_command. Processing them here too would cause double sending.
        """
        text = msg.text.strip()
        if text.startswith(CHAT_COMMAND_PREFIX):
            return

    async def _handle_sr_command(self, cmd):
        """Handles the !sr command that goes to the music queue."""
        query = cmd.parameter.strip() if cmd.parameter else ""
        if query and self.command_callback:
            room_id = cmd.room.room_id if cmd.room else ""
            logger.info(f"Command received from {cmd.user.name}: !sr {query[:30]}")
            try:
                await self.command_callback(query, cmd.user.name, room_id)
            except Exception as e:
                logger.error(f"Error in !sr command callback: {e}")

    async def _handle_other_command(self, cmd):
        """Handles all other commands that go to the command_processor."""
        if self.command_processor:
            text = (
                f"!{cmd.name} {cmd.parameter}".strip()
                if cmd.parameter
                else f"!{cmd.name}"
            )
            room_id = cmd.room.room_id if cmd.room else ""
            logger.info(f"Command received from {cmd.user.name}: {text[:50]}")
            try:
                await self.command_processor.process(text, cmd.user.name, room_id)
            except Exception as e:
                logger.error(f"Error in command processor: {e}")

    async def connect(self) -> bool:
        """Connect to Twitch chat with OAuth flow."""
        try:
            logger.info("Connecting to Twitch...")

            TOKEN_FILE = "tokens.json"

            # Initialize Twitch API
            self.twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)

            target_scopes = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    t = json.load(f)
                try:
                    await self.twitch.set_user_authentication(
                        t["access_token"], target_scopes, t["refresh_token"]
                    )
                    logger.info("Logged in via tokens.json")
                except:
                    # If tokens in the file are old or invalid, force login
                    await self._do_fresh_login(target_scopes, TOKEN_FILE)
            else:
                # If the file doesn't exist, first login ever
                await self._do_fresh_login(target_scopes, TOKEN_FILE)

            # Crea l'istanza della chat
            self.chat = await Chat(self.twitch)

            # Aggiungi listener per i messaggi
            self.chat.register_event(ChatEvent.READY, self._on_ready)
            self.chat.register_event(ChatEvent.MESSAGE, self._handle_message)

            # Register Twitch commands
            # !sr goes to the callback for the music queue
            self.chat.register_command("sr", self._handle_sr_command)
            # All others go to the command_processor
            self.chat.register_command("create", self._handle_other_command)
            self.chat.register_command("playlist", self._handle_other_command)
            self.chat.register_command("add", self._handle_other_command)
            self.chat.register_command("remove", self._handle_other_command)
            self.chat.register_command("move", self._handle_other_command)
            self.chat.register_command("clear", self._handle_other_command)
            self.chat.register_command("list_playlists", self._handle_other_command)
            self.chat.register_command("pump", self._handle_other_command)
            # Admin commands
            self.chat.register_command("blacklist", self._handle_other_command)
            self.chat.register_command("unblacklist", self._handle_other_command)
            self.chat.register_command("blacklist_list", self._handle_other_command)
            self.chat.register_command("skip", self._handle_other_command)
            self.chat.register_command("remove_queue", self._handle_other_command)
            self.chat.register_command("queue_info", self._handle_other_command)
            self.chat.register_command("clear_queue", self._handle_other_command)
            # Analytics commands
            self.chat.register_command("stats", self._handle_other_command)
            self.chat.register_command("top_songs", self._handle_other_command)
            self.chat.register_command("top_users", self._handle_other_command)
            self.chat.register_command("history", self._handle_other_command)
            # Music commands
            self.chat.register_command("volume", self._handle_other_command)
            self.chat.register_command("pause", self._handle_other_command)
            self.chat.register_command("resume", self._handle_other_command)
            self.chat.register_command("repeat", self._handle_other_command)
            self.chat.register_command("repeat_off", self._handle_other_command)
            self.chat.register_command("next", self._handle_other_command)
            self.chat.register_command("queue_info", self._handle_other_command)
            self.chat.register_command("duration", self._handle_other_command)
            self.chat.register_command("when", self._handle_other_command)
            self.chat.register_command("random", self._handle_other_command)
            # Utility commands
            self.chat.register_command("help", self._handle_other_command)
            self.chat.register_command("version", self._handle_other_command)
            self.chat.register_command("uptime", self._handle_other_command)

            # Start the chat
            self.chat.start()

            # Wait for the chat to be ready
            await asyncio.sleep(1)

            self._connected = True
            logger.info(f"Connected to channel: {TARGET_CHANNEL}")
            return True

        except Exception as e:
            logger.error(f"Error in Twitch connection: {e}")
            return False

    async def _do_fresh_login(self, scopes, token_file):
        authenticator = UserAuthenticator(
            self.twitch, scopes, url=OAUTH_REDIRECT_URI or "http://localhost:17563"
        )
        result = await authenticator.authenticate()

        if result:
            access_token, refresh_token = result
            # Save tokens for next time
            with open(token_file, "w") as f:
                json.dump(
                    {"access_token": access_token, "refresh_token": refresh_token}, f
                )

            await self.twitch.set_user_authentication(
                access_token, scopes, refresh_token
            )
            logger.info("New tokens saved successfully!")

    async def _on_ready(self, ready_event: EventData):
        """Handles the READY event when the chat is ready."""
        logger.info("Bot ready, joining channel...")
        await ready_event.chat.join_room(TARGET_CHANNEL)

    async def send_message(self, channel_id: str, message: str) -> bool:
        """Sends a message in the chat."""
        try:
            if self.chat:
                # twitchAPI.Chat.send_message wants the channel NAME, not the numeric ID.
                # cmd.room.room_id returns a numeric ID like "123456789":
                # in that case (or if empty) we use TARGET_CHANNEL as fallback.
                room = (
                    TARGET_CHANNEL
                    if not channel_id or channel_id.isdigit()
                    else channel_id
                )
                await self.chat.send_message(room, message)
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Twitch."""
        try:
            if self.chat:
                self.chat.stop()
            if self.twitch:
                await self.twitch.close()
            self._connected = False
            logger.info("Disconnected from Twitch")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """Returns True if connected."""
        return self._connected
