"""Command Processor - Handles all Twitch commands with explicit DI."""

import asyncio
import time
import re
from typing import Optional
from loguru import logger

from main.config import (
    ADMIN_USERS,
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
    ADMIN_BLACKLIST_COMMAND,
    ADMIN_UNBLACKLIST_COMMAND,
    ADMIN_BLACKLIST_LIST_COMMAND,
    ADMIN_SKIP_COMMAND,
    ADMIN_REMOVE_QUEUE_COMMAND,
    ADMIN_CLEAR_QUEUE_COMMAND,
    ANALYTICS_STATS_COMMAND,
    ANALYTICS_TOP_SONGS_COMMAND,
    ANALYTICS_TOP_USERS_COMMAND,
    ANALYTICS_STORIA_COMMAND,
    MUSIC_VOLUME_COMMAND,
    MUSIC_PAUSE_COMMAND,
    MUSIC_RESUME_COMMAND,
    MUSIC_REPEAT_COMMAND,
    MUSIC_REPEAT_OFF_COMMAND,
    MUSIC_REPEAT_STOP_COMMAND,
    MUSIC_NEXT_COMMAND,
    MUSIC_QUEUE_INFO_COMMAND,
    MUSIC_DURATION_COMMAND,
    MUSIC_DURATA_COMMAND,
    MUSIC_WHEN_COMMAND,
    MUSIC_RANDOM_COMMAND,
    MUSIC_OPS_COMMAND,
    VOTE_SKIP_COMMAND,
    UTILITY_HELP_COMMAND,
    UTILITY_VERSION_COMMAND,
    UTILITY_UPTIME_COMMAND,
)
from main.services import CommandServices
from commands import admin_required


class CompiledPattern:
    """Wraps a compiled regex pattern for fast matching."""
    __slots__ = ("regex", "method_name")

    def __init__(self, pattern: str, method_name: str):
        self.regex = re.compile(pattern, re.IGNORECASE)
        self.method_name = method_name


class CommandProcessor:
    """Processes and handles all chat commands with explicit DI."""

    def __init__(self, services: CommandServices):
        self.services = services
        # Dynamically discover which cmd_* methods require admin permissions
        self._admin_methods: set[str] = self._build_admin_set()
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
        a_blacklist = re.escape(ADMIN_BLACKLIST_COMMAND)
        a_unblacklist = re.escape(ADMIN_UNBLACKLIST_COMMAND)
        a_blacklist_list = re.escape(ADMIN_BLACKLIST_LIST_COMMAND)
        a_skip = re.escape(ADMIN_SKIP_COMMAND)
        a_skip_alias = re.escape("skip")
        a_remove_queue = re.escape(ADMIN_REMOVE_QUEUE_COMMAND)
        a_clear_queue = re.escape(ADMIN_CLEAR_QUEUE_COMMAND)
        stat_stats = re.escape(ANALYTICS_STATS_COMMAND)
        stat_top_songs = re.escape(ANALYTICS_TOP_SONGS_COMMAND)
        stat_top_users = re.escape(ANALYTICS_TOP_USERS_COMMAND)
        stat_storia = re.escape(ANALYTICS_STORIA_COMMAND)
        mus_volume = re.escape(MUSIC_VOLUME_COMMAND)
        mus_pause = re.escape(MUSIC_PAUSE_COMMAND)
        mus_resume = re.escape(MUSIC_RESUME_COMMAND)
        mus_repeat = re.escape(MUSIC_REPEAT_COMMAND)
        mus_repeat_off = re.escape(MUSIC_REPEAT_OFF_COMMAND)
        mus_repeat_stop = re.escape(MUSIC_REPEAT_STOP_COMMAND)
        mus_next = re.escape(MUSIC_NEXT_COMMAND)
        mus_queue_info = re.escape(MUSIC_QUEUE_INFO_COMMAND)
        mus_duration = re.escape(MUSIC_DURATION_COMMAND)
        mus_durata = re.escape(MUSIC_DURATA_COMMAND)
        mus_when = re.escape(MUSIC_WHEN_COMMAND)
        mus_random = re.escape(MUSIC_RANDOM_COMMAND)
        mus_ops = re.escape(MUSIC_OPS_COMMAND)
        util_help = re.escape(UTILITY_HELP_COMMAND)
        util_version = re.escape(UTILITY_VERSION_COMMAND)
        util_uptime = re.escape(UTILITY_UPTIME_COMMAND)
        vote_skip = re.escape(VOTE_SKIP_COMMAND)

        raw_patterns = {
            rf"{prefix}{sr_prefix}\s+(.+)$": "cmd_sr",
            rf"{prefix}{p_create}\s+(\w+)$": "cmd_create",
            rf"{prefix}{p_view}(?:\s+(\w+)(?:\s+(\d+))?)?$": "cmd_playlist",
            rf"{prefix}{p_add}\s+(\w+)\s+(.+)$": "cmd_add",
            rf"{prefix}{p_remove}\s+(\w+)\s+(.+)$": "cmd_remove",
            rf"{prefix}{p_move}\s+(\w+)\s+(\d+)\s+(\d+)$": "cmd_move",
            rf"{prefix}{p_clear}\s+(\w+)$": "cmd_clear",
            rf"{prefix}{p_list}": "cmd_list_playlists",
            rf"{prefix}{p_pompa}(?:\s+(\w+)(?:\s+(\d+))?)?$": "cmd_pump",
            rf"{prefix}{a_blacklist}\s+(\w+)$": "cmd_blacklist",
            rf"{prefix}{a_unblacklist}\s+(\w+)$": "cmd_unblacklist",
            rf"{prefix}{a_blacklist_list}$": "cmd_blacklist_list",
            rf"{prefix}{a_skip}$": "cmd_skip",
            rf"{prefix}{a_skip_alias}$": "cmd_skip",
            rf"{prefix}{a_remove_queue}\s+(\d+)$": "cmd_remove_queue",
            rf"{prefix}{a_clear_queue}$": "cmd_clear_queue",
            rf"{prefix}{stat_stats}$": "cmd_stats",
            rf"{prefix}{stat_top_songs}(?:\s+(\d+))?$": "cmd_top_songs",
            rf"{prefix}{stat_top_users}(?:\s+(\d+))?$": "cmd_top_users",
            rf"{prefix}{mus_volume}\s+(\d+)$": "cmd_volume",
           rf"{prefix}{mus_pause}$": "cmd_pause",
            rf"{prefix}{mus_resume}$": "cmd_resume",
            rf"{prefix}{mus_repeat}(?:\s+(\d+))?$": "cmd_repeat",
            rf"{prefix}{mus_repeat_off}$": "cmd_repeat_off",
            rf"{prefix}{mus_repeat_stop}$": "cmd_stop_repeat",
           rf"{prefix}{mus_next}$": "cmd_next",
            rf"{prefix}{mus_queue_info}$": "cmd_queue_info",
            rf"{prefix}{mus_duration}\s+(.+)$": "cmd_duration",
            rf"{prefix}{mus_durata}\s+(\d+)$": "cmd_at",
            rf"{prefix}{mus_when}$": "cmd_when",
            rf"{prefix}{mus_random}(?:\s+(\d+))?$": "cmd_random",
            rf"{prefix}{mus_ops}$": "cmd_ops",
            rf"{prefix}{stat_storia}(?:\s+(\d+))?$": "cmd_history",
            rf"{prefix}{util_help}(?:\s+(\w+))?$": "cmd_help",
            rf"{prefix}{util_version}$": "cmd_version",
            rf"{prefix}{util_uptime}$": "cmd_uptime",
            rf"{prefix}{vote_skip}$": "cmd_vote",
        }

        self.compiled_commands: list[CompiledPattern] = [
            CompiledPattern(pattern, method) for pattern, method in raw_patterns.items()
        ]

    def _build_admin_set(self) -> set[str]:
        """Discover all cmd_* methods decorated with @admin_required."""
        admin_set: set[str] = set()
        for name in dir(self):
            if name.startswith("cmd_"):
                attr = getattr(self, name)
                if callable(attr) and getattr(attr, "_requires_admin", False):
                    admin_set.add(name)
        return admin_set

    def _is_admin(self, username: str) -> bool:
        """Checks if a user has admin permissions."""
        return username.lower() in [u.lower() for u in ADMIN_USERS]

    async def process(self, text: str, username: str, channel_id: str) -> bool:
        """Processes a chat message and responds if it is a command."""
        text_lower = text.lower().strip()

        for compiled in self.compiled_commands:
            match = compiled.regex.match(text_lower)

            if match:
                method_name = compiled.method_name
                method = getattr(self, method_name, None)

                if method:
                    # Check permissions for admin commands (discovered via @admin_required)
                    if method_name in self._admin_methods and not self._is_admin(username):
                        await self._send_public(channel_id, "⛔ You don't have permission to use this command.")
                        return True

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
                            f"Error in command {method_name}: {e}\n"
                            + traceback.format_exc()
                        )
                        try:
                            await self._send_public(
                                channel_id,
                                f"❌ Internal error ({type(e).__name__}: {e})",
                            )
                        except Exception:
                            pass

        return False

    async def _send_response(self, response, channel_id: str):
        """Sends response with rate limiting for message lists."""
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
        """Sends public message via Twitch."""
        if self.services.bot and hasattr(self.services.bot, "chat_message"):
            await self.services.bot.chat_message.send_public(channel_id, message)

    # =====================================================================
    # PLAYLIST COMMANDS
    # =====================================================================

    async def cmd_create(self, playlist_name: str, username: str, channel_id: str):
        """!create <name> - Creates a new playlist."""
        return await self.services.playlist_commands.cmd_create(username, playlist_name)

    async def cmd_playlist(self, nome: Optional[str], page_str: Optional[str], username: str, channel_id: str):
        """!playlist [nome] [pagina] - Mostra playlist o canzoni."""
        page = int(page_str) if page_str else 1
        if nome is None:
            nome = None
            page = 1
        return await self.services.playlist_commands.cmd_playlist(username, nome, page)

    async def cmd_add(
        self, playlist_name: str, query: str, username: str, channel_id: str
    ):
        """!add <playlist> - Add current song."""
        file_path = "unknown"

        return await self.services.playlist_commands.cmd_add(
            username, playlist_name, query, file_path, username
        )

    async def cmd_remove(
        self, playlist_name: str, index_or_name: str, username: str, channel_id: str
    ):
        """!remove <playlist> <position> - Remove song."""
        return await self.services.playlist_commands.cmd_remove(
            username, playlist_name, index_or_name
        )

    async def cmd_move(
        self, playlist_name: str, num1: str, num2: str, username: str, channel_id: str
    ):
        """!move <playlist> <pos1> <pos2> - Move songs."""
        return await self.services.playlist_commands.cmd_move(
            username, playlist_name, num1, num2
        )

    async def cmd_clear(self, playlist_name: str, username: str, channel_id: str):
        """!clear <playlist> - Clear playlist."""
        return await self.services.playlist_commands.cmd_clear(username, playlist_name)

    async def cmd_list_playlists(self, username: str, channel_id: str):
        """!list_playlists - Show all playlists."""
        return await self.services.playlist_commands.cmd_list_playlists(username)

    async def cmd_pump(
        self, playlist_name: Optional[str], n_str: Optional[str], username: str, channel_id: str
    ):
        """!pump [playlist] [n] - Pump N random songs from a playlist."""
        n = int(n_str) if n_str else 5
        return await self.services.playlist_commands.cmd_pump(username, playlist_name, n, channel_id)

    # =====================================================================
    # ADMIN COMMANDS
    # =====================================================================

    @admin_required
    async def cmd_blacklist(self, target_user: str, username: str, channel_id: str):
        """!blacklist <utente> - Aggiungi blacklist."""
        return await self.services.admin_commands.cmd_blacklist(username, target_user)

    @admin_required
    async def cmd_unblacklist(self, target_user: str, username: str, channel_id: str):
        """!unblacklist <utente> - Rimuovi blacklist."""
        return await self.services.admin_commands.cmd_unblacklist(username, target_user)

    @admin_required
    async def cmd_blacklist_list(self, username: str, channel_id: str):
        """!blacklist_list - Mostra blacklist."""
        return await self.services.admin_commands.cmd_blacklist_list(username)

    @admin_required
    async def cmd_skip(self, username: str, channel_id: str):
        """!skip - Skip song."""
        return await self.services.admin_commands.cmd_skip(username)

    @admin_required
    async def cmd_remove_queue(self, position: str, username: str, channel_id: str):
        """!remove_queue <pos> - Remove from queue."""
        return await self.services.admin_commands.cmd_remove_queue(username, position)

    @admin_required
    async def cmd_clear_queue(self, username: str, channel_id: str):
        """!clear_queue - Clear queue."""
        return await self.services.admin_commands.cmd_clear_queue(username)

    # =====================================================================
    # ANALYTICS COMMANDS
    # =====================================================================

    async def cmd_stats(self, username: str, channel_id: str):
        """!stats - Statistics."""
        return await self.services.analytics_commands.cmd_stats(username)

    async def cmd_top_songs(self, n: str, username: str, channel_id: str):
        """!top_songs [N] - Top songs."""
        n = int(n) if n else 10
        return await self.services.analytics_commands.cmd_top_songs(username, n)

    async def cmd_top_users(self, n: str, username: str, channel_id: str):
        """!top_users [N] - Top users."""
        n = int(n) if n else 10
        return await self.services.analytics_commands.cmd_top_users(username, n)

    # =====================================================================
    # MUSIC COMMANDS
    # =====================================================================



    async def cmd_pause(self, username: str, channel_id: str):
        """!pause - Pause."""
        return await self.services.music_commands.cmd_pause(username)

    async def cmd_resume(self, username: str, channel_id: str):
        """!resume - Resume."""
        return await self.services.music_commands.cmd_resume(username)

    # =====================================================================
    # ADMIN COMMANDS (repeat/volume moved here for permission control)
    # =====================================================================

    @admin_required
    async def cmd_repeat(self, count: str, username: str, channel_id: str):
        """!repeat [N] - Repeat song (N=1 or empty=infinite). Admin only."""
        if count is None:
            # No argument: infinite repeat
            return await self.services.music_commands.cmd_repeat(username, -1)
        else:
            count = int(count)
            if count == 0:
                return await self.services.music_commands.cmd_repeat_off(username)
            return await self.services.music_commands.cmd_repeat(username, count)

    @admin_required
    async def cmd_repeat_off(self, username: str, channel_id: str):
        """!repeat_off - Disable repeat. Admin only."""
        return await self.services.music_commands.cmd_repeat_off(username)

    @admin_required
    async def cmd_volume(self, level: str, username: str, channel_id: str):
        """!volume <0-100> - Set volume (admin)."""
        level = int(level)
        return await self.services.music_commands.cmd_volume(username, level)

    async def cmd_stop_repeat(self, username: str, channel_id: str):
        """!stop_repeat - Stop repeat."""
        return await self.services.music_commands.cmd_stop_repeat(username)

    async def cmd_next(self, username: str, channel_id: str):
        """!next - Next song."""
        return await self.services.music_commands.cmd_next(username)

    async def cmd_queue_info(self, username: str, channel_id: str):
        """!queue_info - Queue info."""
        return await self.services.utility_commands.cmd_queue_info(username, channel_id)

    async def cmd_duration(self, query: str, username: str, channel_id: str):
        """!duration <song> - Song duration."""
        return await self.services.music_commands.cmd_duration(username, query)

    async def cmd_at(self, position: str, username: str, channel_id: str):
        """!at <N> - Duration of song at position N in queue."""
        return await self.services.music_commands.cmd_at(position, username, channel_id)

    async def cmd_when(self, username: str, channel_id: str):
        """!when - Estimate when your next song will play."""
        return await self.services.music_commands.cmd_when(username, channel_id)

    async def cmd_random(self, n_str: Optional[str], username: str, channel_id: str):
        """!random [N] - Play N random songs from library."""
        n = int(n_str) if n_str else 1
        return await self.services.music_commands.cmd_random(username, n)

    async def cmd_ops(self, username: str, channel_id: str):
        """!ops - Remove the last song you added from the queue."""
        return await self.services.music_commands.cmd_ops(username)

    async def cmd_history(self, n_str: Optional[str], username: str, channel_id: str):
        """!history [N] - History of last N songs played."""
        n = int(n_str) if n_str else 10
        return await self.services.analytics_commands.cmd_history(username, n)

    # =====================================================================
    # UTILITY COMMANDS
    # =====================================================================

    async def cmd_help(self, *args):
        """!help [command] - Robust argument handling."""
        logger.debug(f"cmd_help called with args: {args}")

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
            f"Calling utility.cmd_help with username={username}, command='{captured_command}'"
        )

        return await self.services.utility_commands.cmd_help(username, captured_command)

    async def cmd_version(self, username: str, channel_id: str):
        """!version - Bot version."""
        return await self.services.utility_commands.cmd_version(username)

    async def cmd_uptime(self, username: str, channel_id: str):
        """!uptime - Uptime."""
        bot = self.services.bot
        if not bot or not hasattr(bot, "_start_time"):
            return await self.services.utility_commands.cmd_uptime(username)
        elapsed = time.time() - bot._start_time
        days = int(elapsed // 86400)
        hours = int((elapsed % 86400) // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        parts: list[str] = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or len(parts) == 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return f"⏱️ Bot has been running for: {' '.join(parts)}"

    # =====================================================================
    # VOTE TO SKIP
    # =====================================================================

    async def cmd_vote(self, username: str, channel_id: str):
        """!vote - Vote to skip the current song."""
        return await self.services.music_commands.cmd_vote(username)
