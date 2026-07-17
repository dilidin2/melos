#!/usr/bin/env python3
"""
Twitch Handler Module

Manages the connection to Twitch chat and command listening.
Uses Device Code Flow (DCF) for OAuth — no client secret required.
"""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Callable, Optional

import aiohttp
from twitchAPI.chat import Chat, ChatEvent, ChatMessage, EventData
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from loguru import logger

from main.config import (
    TWITCH_CLIENT_ID,
    TARGET_CHANNEL,
    CHAT_COMMAND_PREFIX,
    SONG_REQUEST_COMMAND,
)

TOKEN_PATH = Path("tokens.json")
REQUIRED_SCOPES = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

DEVICE_CODE_URL = "https://id.twitch.tv/oauth2/device"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def _save_tokens(access_token: str, refresh_token: str) -> None:
    """Persist OAuth tokens to tokens.json."""
    with open(TOKEN_PATH, "w") as f:
        json.dump({"access_token": access_token, "refresh_token": refresh_token}, f)
    logger.debug("Tokens saved to tokens.json")


def _load_tokens() -> Optional[dict]:
    """Load OAuth tokens from tokens.json."""
    if TOKEN_PATH.exists():
        try:
            with open(TOKEN_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load tokens.json: {e}")
    return None


class TwitchHandler:
    """Class to manage the Twitch connection and chat commands."""

    def __init__(self):
        """Initializes the TwitchHandler."""
        self.twitch: Optional[Twitch] = None
        self.chat: Optional[Chat] = None
        self.command_callback: Optional[Callable] = None
        self.command_pattern: str = (
            rf"{re.escape(CHAT_COMMAND_PREFIX)}"
            rf"{re.escape(SONG_REQUEST_COMMAND)}\s+(.+?)$"
        )
        self.multiple_patterns: list[str] = []
        self._connected = False

        # Command processor (opzionale)
        self.command_processor = None

    # ── Auth helpers ──────────────────────────────────────────────────────────

    async def _on_token_refresh(self, token: str, refresh_token: str) -> None:
        """
        Called automatically by twitchAPI whenever the OAuth token is refreshed.
        Persisting new tokens here prevents silent expiry after ~4 hours.
        """
        logger.info("OAuth token refreshed — saving new tokens to tokens.json")
        _save_tokens(token, refresh_token)

    async def _get_device_code(self, scopes: list) -> dict:
        """Request a device code from Twitch."""
        scope_str = " ".join(
            s.value if hasattr(s, "value") else str(s) for s in scopes
        )
        data = {"client_id": TWITCH_CLIENT_ID, "scope": scope_str}
        async with aiohttp.ClientSession() as session:
            async with session.post(DEVICE_CODE_URL, data=data) as resp:
                return await resp.json()

    async def _poll_for_token(
        self, device_code: str, interval: int, scopes: list
    ) -> tuple[str, str]:
        """
        Poll Twitch for the user token after they authorize.
        Raises TimeoutError on expired code, RuntimeError on denial.
        """
        current_interval = interval
        scope_str = " ".join(
            s.value if hasattr(s, "value") else str(s) for s in scopes
        )
        async with aiohttp.ClientSession() as session:
            while True:
                data = {
                    "client_id": TWITCH_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "scope": scope_str,
                }
                async with session.post(TOKEN_URL, data=data) as resp:
                    result = await resp.json()

                if resp.status == 200:
                    return result["access_token"], result["refresh_token"]

                error = result.get("error")
                if error == "authorization_pending":
                    pass  # keep polling
                elif error == "slow_down":
                    logger.warning("Twitch OAuth: slow_down — increasing poll interval")
                    current_interval += 5
                elif error == "expired_token":
                    raise TimeoutError(
                        "Device code expired — user did not authorize in time"
                    )
                elif error == "access_denied":
                    raise RuntimeError("User denied authorization")

                await asyncio.sleep(current_interval)

    async def _do_device_auth(self, scopes: list) -> tuple[str, str]:
        """
        Execute the Device Code Flow (blocking).
        Returns (access_token, refresh_token).
        """
        device_info = await self._get_device_code(scopes)
        user_code = device_info["user_code"]
        verification_uri = device_info["verification_uri"]
        expires_in = device_info["expires_in"]
        interval = device_info["interval"]

        logger.info(
            f"Twitch Device Code Flow — go to {verification_uri} "
            f"and enter code: {user_code}"
        )
        logger.info(f"Code expires in {expires_in}s, polling every {interval}s")

        return await self._poll_for_token(
            device_info["device_code"], interval, scopes
        )

    async def _do_fresh_login(self, scopes: list) -> None:
        """Perform a fresh OAuth login via Device Code Flow."""
        logger.info("Starting Device Code Flow authentication...")
        access_token, refresh_token = await self._do_device_auth(scopes)
        _save_tokens(access_token, refresh_token)

        await self.twitch.set_user_authentication(
            access_token, scopes, refresh_token
        )
        logger.info("✓ New tokens saved and authenticated successfully!")

    # ── Command handlers ──────────────────────────────────────────────────────

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

    # ── Connection ────────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Connect to Twitch chat with OAuth flow (Device Code Flow)."""
        try:
            logger.info("Connecting to Twitch...")

            # Initialize Twitch API (no client secret needed for DCF)
            self.twitch = Twitch(
                app_id=TWITCH_CLIENT_ID, app_secret="", authenticate_app=False
            )

            # Register the refresh callback BEFORE setting any token, so the
            # library can transparently persist renewed tokens on every refresh.
            self.twitch.user_auth_refresh_callback = self._on_token_refresh

            cached = _load_tokens()
            if cached:
                try:
                    await self.twitch.set_user_authentication(
                        cached["access_token"], REQUIRED_SCOPES, cached["refresh_token"]
                    )
                    logger.info("✓ Logged in via tokens.json")
                except Exception as e:
                    logger.warning(
                        f"Tokens expired/invalid ({e}) — starting Device Code Flow for re-authentication"
                    )
                    await self._do_fresh_login(REQUIRED_SCOPES)
            else:
                # First login ever — no tokens cached
                await self._do_fresh_login(REQUIRED_SCOPES)

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
            self.chat.register_command("pump", self._handle_other_command)
            # Admin commands
            self.chat.register_command("blacklist", self._handle_other_command)
            self.chat.register_command("unblacklist", self._handle_other_command)
            self.chat.register_command("blacklist_list", self._handle_other_command)
            self.chat.register_command("trust_channel", self._handle_other_command)
            self.chat.register_command("untrust_channel", self._handle_other_command)
            self.chat.register_command("trusted_channels", self._handle_other_command)
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
            self.chat.register_command("ops", self._handle_other_command)
            # Vote to skip
            self.chat.register_command("vote", self._handle_other_command)
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

    async def _on_ready(self, ready_event: EventData):
        """Handles the READY event when the chat is ready."""
        logger.info("Bot ready, joining channel...")
        await ready_event.chat.join_room(TARGET_CHANNEL)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_command_callback(self, callback: Callable, pattern: str = ""):
        """Sets the callback for commands."""
        self.command_callback = callback
        self.command_pattern = (
            pattern
            or rf"{re.escape(CHAT_COMMAND_PREFIX)}"
               rf"{re.escape(SONG_REQUEST_COMMAND)}\s+(.+?)$"
        )

    def set_multiple_commands(self, patterns: list[str], callback: Callable):
        """Sets multiple commands with different patterns."""
        self.command_callback = callback
        self.multiple_patterns = patterns

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
