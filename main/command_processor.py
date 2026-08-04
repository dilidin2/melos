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
    PLAYLIST_POMPA_COMMAND,
    ADMIN_BLACKLIST_COMMAND,
    ADMIN_UNBLACKLIST_COMMAND,
    ADMIN_BLACKLIST_LIST_COMMAND,
    ADMIN_SKIP_COMMAND,
    ADMIN_TRUST_CHANNEL_COMMAND,
    ADMIN_UNTRUST_CHANNEL_COMMAND,
    ADMIN_TRUSTED_CHANNELS_LIST_COMMAND,
    ADMIN_REMOVE_QUEUE_COMMAND,
    ADMIN_CLEAR_QUEUE_COMMAND,
    ADMIN_DELETE_COMMAND,
    ANALYTICS_STATS_COMMAND,
    ANALYTICS_TOP_SONGS_COMMAND,
    ANALYTICS_TOP_USERS_COMMAND,
    ANALYTICS_STORIA_COMMAND,
    MUSIC_VOLUME_COMMAND,
    MUSIC_PAUSE_COMMAND,
    MUSIC_RESUME_COMMAND,
    MUSIC_REPEAT_COMMAND,
    MUSIC_REPEAT_OFF_COMMAND,
    MUSIC_NEXT_COMMAND,
    MUSIC_QUEUE_INFO_COMMAND,
    MUSIC_DURATION_COMMAND,
    MUSIC_WHEN_COMMAND,
    MUSIC_RANDOM_COMMAND,
    MUSIC_OPS_COMMAND,
    VOTE_SKIP_COMMAND,
    UTILITY_HELP_COMMAND,
    UTILITY_VERSION_COMMAND,
    UTILITY_UPTIME_COMMAND,
)


class CommandProcessor:
    """Processes and handles all chat commands."""

    def __init__(
        self,
        bot,
        playlist_commands,
        admin_commands,
        analytics_commands,
        music_commands,
        utility_commands,
        music_downloader,
    ):
        self.bot = bot
        self._playlist = playlist_commands
        self._admin = admin_commands
        self._analytics = analytics_commands
        self._music = music_commands
        self._utility = utility_commands
        self._downloader = music_downloader

        # Discover which handler methods require admin via @admin_required marker
        self._admin_methods: set[str] = set()
        for obj in (playlist_commands, admin_commands, analytics_commands, music_commands, utility_commands):
            for name in dir(obj):
                if name.startswith("cmd_"):
                    attr = getattr(obj, name)
                    if callable(attr) and getattr(attr, "_requires_admin", False):
                        self._admin_methods.add(name)

        # Build dispatch registry: method_name -> (callable, needs_admin)
        prefix = re.escape(CHAT_COMMAND_PREFIX)

        def h(fn):
            """Wrap a handler, returning (callable, is_admin)."""
            return (fn, fn.__name__ in self._admin_methods)

        def cmd(fn):
            return fn

        # ── Handlers: each takes (groups, username, channel_id) ──

        @cmd
        async def h_create(g, u, c):
            return await self._playlist.cmd_create(u, g[0])

        @cmd
        async def h_playlist(g, u, c):
            nome, page_str = g[0], g[1]
            page = int(page_str) if page_str else 1
            if nome is None:
                nome, page = None, 1
            return await self._playlist.cmd_playlist(u, nome, page)

        @cmd
        async def h_add(g, u, c):
            playlist_name = g[0]
            raw = g[1]

            songs = [s.strip() for s in raw.split(",") if s.strip()]
            if not songs:
                return "❌ No songs provided."

            playlist = self._playlist.playlist_manager.get_playlist_by_name(u, playlist_name)
            if not playlist:
                return f"❌ Playlist '{playlist_name}' not found."

            added = []
            failed = []
            for song in songs:
                fp = "unknown"
                if self._downloader:
                    match = self._downloader._find_matching_file(song)
                    if match:
                        fp = match
                result = await self._playlist.cmd_add(u, playlist_name, song, fp, u)
                if "✅" in result:
                    added.append(song)
                else:
                    failed.append(song)

            if not added:
                return "❌ Couldn't add any songs."
            elif not failed:
                return f"✅ Added {len(added)} song(s) to '{playlist_name}'!"
            else:
                if len(failed) > 5:
                    failed_list = ", ".join(failed[:5]) + f" and {len(failed) - 5} more"
                else:
                    failed_list = ", ".join(failed)
                return f"✅ Added {len(added)} song(s), but couldn't add: {failed_list}"

        @cmd
        async def h_remove(g, u, c):
            return await self._playlist.cmd_remove(u, g[0], g[1])

        @cmd
        async def h_move(g, u, c):
            return await self._playlist.cmd_move(u, g[0], g[1], g[2])

        @cmd
        async def h_clear(g, u, c):
            return await self._playlist.cmd_clear(u, g[0])

        @cmd
        async def h_pump(g, u, c):
            n = int(g[1]) if g[1] else 5
            return await self._playlist.cmd_pump(u, g[0], n, c)

        @cmd
        async def h_blacklist(g, u, c):
            return await self._admin.cmd_blacklist(u, g[0])

        @cmd
        async def h_unblacklist(g, u, c):
            return await self._admin.cmd_unblacklist(u, g[0])

        @cmd
        async def h_blacklist_list(g, u, c):
            return await self._admin.cmd_blacklist_list(u)

        @cmd
        async def h_skip(g, u, c):
            return await self._admin.cmd_skip(u)

        @cmd
        async def h_trust_channel(g, u, c):
            return await self._admin.cmd_trust_channel(u, g[0])

        @cmd
        async def h_untrust_channel(g, u, c):
            return await self._admin.cmd_untrust_channel(u, g[0])

        @cmd
        async def h_trusted_channels_list(g, u, c):
            return await self._admin.cmd_trusted_channels_list(u)

        @cmd
        async def h_remove_queue(g, u, c):
            return await self._admin.cmd_remove_queue(u, g[0])

        @cmd
        async def h_clear_queue(g, u, c):
            return await self._admin.cmd_clear_queue(u)

        @cmd
        async def h_delete(g, u, c):
            return await self._admin.cmd_delete(u, g[0])

        @cmd
        async def h_stats(g, u, c):
            return await self._analytics.cmd_stats(u)

        @cmd
        async def h_top_songs(g, u, c):
            n = int(g[0]) if g[0] else 10
            return await self._analytics.cmd_top_songs(u, n)

        @cmd
        async def h_top_users(g, u, c):
            n = int(g[0]) if g[0] else 10
            return await self._analytics.cmd_top_users(u, n)

        @cmd
        async def h_history(g, u, c):
            n = int(g[0]) if g[0] else 10
            return await self._analytics.cmd_history(u, n)

        @cmd
        async def h_pause(g, u, c):
            return await self._music.cmd_pause(u)

        @cmd
        async def h_resume(g, u, c):
            return await self._music.cmd_resume(u)

        @cmd
        async def h_repeat(g, u, c):
            count = g[0]
            if count is None:
                return await self._music.cmd_repeat(u, -1)
            count = int(count)
            if count == 0:
                return await self._music.cmd_repeat_off(u)
            return await self._music.cmd_repeat(u, count)

        @cmd
        async def h_repeat_off(g, u, c):
            return await self._music.cmd_repeat_off(u)

        @cmd
        async def h_volume(g, u, c):
            return await self._music.cmd_volume(u, int(g[0]))

        @cmd
        async def h_next(g, u, c):
            return await self._music.cmd_next(u)

        @cmd
        async def h_queue_info(g, u, c):
            return await self._utility.cmd_queue_info(u, c)

        @cmd
        async def h_duration(g, u, c):
            return await self._music.cmd_duration(u, g[0])

        @cmd
        async def h_when(g, u, c):
            return await self._music.cmd_when(u, c)

        @cmd
        async def h_random(g, u, c):
            n = int(g[0]) if g[0] else 1
            return await self._music.cmd_random(u, n)

        @cmd
        async def h_ops(g, u, c):
            return await self._music.cmd_ops(u)

        @cmd
        async def h_help(g, u, c):
            command = g[0] if g[0] else ""
            return await self._utility.cmd_help(u, command)

        @cmd
        async def h_version(g, u, c):
            return await self._utility.cmd_version(u)

        @cmd
        async def h_uptime(g, u, c):
            bot = self.bot
            if bot and hasattr(bot, "_start_time"):
                elapsed = time.time() - bot._start_time
                days = int(elapsed // 86400)
                hours = int((elapsed % 86400) // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                parts = []
                if days > 0:
                    parts.append(f"{days}d")
                if hours > 0:
                    parts.append(f"{hours}h")
                if minutes > 0 or not parts:
                    parts.append(f"{minutes}m")
                parts.append(f"{seconds}s")
                return f"⏱️ Bot has been running for: {' '.join(parts)}"
            return await self._utility.cmd_uptime(u)

        @cmd
        async def h_vote(g, u, c):
            return await self._music.cmd_vote(u)

        # Registry: (compiled_regex, handler, needs_admin)
        sr_prefix = re.escape(SONG_REQUEST_COMMAND)
        p_create = re.escape(PLAYLIST_CREATE_COMMAND)
        p_view = re.escape(PLAYLIST_VIEW_COMMAND)
        p_add = re.escape(PLAYLIST_ADD_COMMAND)
        p_remove = re.escape(PLAYLIST_REMOVE_COMMAND)
        p_move = re.escape(PLAYLIST_MOVE_COMMAND)
        p_clear = re.escape(PLAYLIST_CLEAR_COMMAND)
        p_pompa = re.escape(PLAYLIST_POMPA_COMMAND)
        a_blacklist = re.escape(ADMIN_BLACKLIST_COMMAND)
        a_unblacklist = re.escape(ADMIN_UNBLACKLIST_COMMAND)
        a_blacklist_list = re.escape(ADMIN_BLACKLIST_LIST_COMMAND)
        a_skip = re.escape(ADMIN_SKIP_COMMAND)
        a_skip_alias = re.escape("skip")
        a_trust_channel = re.escape(ADMIN_TRUST_CHANNEL_COMMAND)
        a_untrust_channel = re.escape(ADMIN_UNTRUST_CHANNEL_COMMAND)
        a_trusted_channels_list = re.escape(ADMIN_TRUSTED_CHANNELS_LIST_COMMAND)
        a_remove_queue = re.escape(ADMIN_REMOVE_QUEUE_COMMAND)
        a_clear_queue = re.escape(ADMIN_CLEAR_QUEUE_COMMAND)
        d_delete = re.escape(ADMIN_DELETE_COMMAND)
        stat_stats = re.escape(ANALYTICS_STATS_COMMAND)
        stat_top_songs = re.escape(ANALYTICS_TOP_SONGS_COMMAND)
        stat_top_users = re.escape(ANALYTICS_TOP_USERS_COMMAND)
        stat_storia = re.escape(ANALYTICS_STORIA_COMMAND)
        mus_volume = re.escape(MUSIC_VOLUME_COMMAND)
        mus_pause = re.escape(MUSIC_PAUSE_COMMAND)
        mus_resume = re.escape(MUSIC_RESUME_COMMAND)
        mus_repeat = re.escape(MUSIC_REPEAT_COMMAND)
        mus_repeat_off = re.escape(MUSIC_REPEAT_OFF_COMMAND)
        mus_next = re.escape(MUSIC_NEXT_COMMAND)
        mus_queue_info = re.escape(MUSIC_QUEUE_INFO_COMMAND)
        mus_duration = re.escape(MUSIC_DURATION_COMMAND)
        mus_when = re.escape(MUSIC_WHEN_COMMAND)
        mus_random = re.escape(MUSIC_RANDOM_COMMAND)
        mus_ops = re.escape(MUSIC_OPS_COMMAND)
        util_help = re.escape(UTILITY_HELP_COMMAND)
        util_version = re.escape(UTILITY_VERSION_COMMAND)
        util_uptime = re.escape(UTILITY_UPTIME_COMMAND)
        vote_skip = re.escape(VOTE_SKIP_COMMAND)

        self._commands: list[tuple[re.Pattern, callable, bool]] = [
            (re.compile(rf"{prefix}{sr_prefix}\s+(.+)$", re.IGNORECASE), h_create, False),  # placeholder, never hit (sr goes to callback)
        ]
        # Overwrite with actual commands
        self._commands = [
            (re.compile(rf"{prefix}{p_create}\s+(\w+)$", re.IGNORECASE), h_create, False),
            (re.compile(rf"{prefix}{p_view}(?:\s+(\w+)(?:\s+(\d+))?)?$", re.IGNORECASE), h_playlist, False),
            (re.compile(rf"{prefix}{p_add}\s+(\w+)\s+(.+)$", re.IGNORECASE), h_add, False),
            (re.compile(rf"{prefix}{p_remove}\s+(\w+)\s+(.+)$", re.IGNORECASE), h_remove, False),
            (re.compile(rf"{prefix}{p_move}\s+(\w+)\s+(\d+)\s+(\d+)$", re.IGNORECASE), h_move, False),
            (re.compile(rf"{prefix}{p_clear}\s+(\w+)$", re.IGNORECASE), h_clear, False),
            (re.compile(rf"{prefix}{p_pompa}(?:\s+(\w+)(?:\s+(\d+))?)?$", re.IGNORECASE), h_pump, False),
            (re.compile(rf"{prefix}{a_blacklist}\s+(\w+)$", re.IGNORECASE), h_blacklist, True),
            (re.compile(rf"{prefix}{a_unblacklist}\s+(\w+)$", re.IGNORECASE), h_unblacklist, True),
            (re.compile(rf"{prefix}{a_blacklist_list}$", re.IGNORECASE), h_blacklist_list, True),
            (re.compile(rf"{prefix}{a_skip}$", re.IGNORECASE), h_skip, True),
            (re.compile(rf"{prefix}{a_skip_alias}$", re.IGNORECASE), h_skip, True),
            (re.compile(rf"{prefix}{a_trust_channel}\s+(.+)$", re.IGNORECASE), h_trust_channel, True),
            (re.compile(rf"{prefix}{a_untrust_channel}\s+(\w+)$", re.IGNORECASE), h_untrust_channel, True),
            (re.compile(rf"{prefix}{a_trusted_channels_list}$", re.IGNORECASE), h_trusted_channels_list, True),
            (re.compile(rf"{prefix}{a_remove_queue}\s+(\d+)$", re.IGNORECASE), h_remove_queue, True),
            (re.compile(rf"{prefix}{a_clear_queue}$", re.IGNORECASE), h_clear_queue, True),
            (re.compile(rf"{prefix}{d_delete}\s+(.+)$", re.IGNORECASE), h_delete, True),
            (re.compile(rf"{prefix}{stat_stats}$", re.IGNORECASE), h_stats, False),
            (re.compile(rf"{prefix}{stat_top_songs}(?:\s+(\d+))?$", re.IGNORECASE), h_top_songs, False),
            (re.compile(rf"{prefix}{stat_top_users}(?:\s+(\d+))?$", re.IGNORECASE), h_top_users, False),
            (re.compile(rf"{prefix}{stat_storia}(?:\s+(\d+))?$", re.IGNORECASE), h_history, False),
            (re.compile(rf"{prefix}{mus_volume}\s+(\d+)$", re.IGNORECASE), h_volume, True),
            (re.compile(rf"{prefix}{mus_pause}$", re.IGNORECASE), h_pause, True),
            (re.compile(rf"{prefix}{mus_resume}$", re.IGNORECASE), h_resume, True),
            (re.compile(rf"{prefix}{mus_repeat}(?:\s+(\d+))?$", re.IGNORECASE), h_repeat, True),
            (re.compile(rf"{prefix}{mus_repeat_off}$", re.IGNORECASE), h_repeat_off, True),
            (re.compile(rf"{prefix}{mus_next}$", re.IGNORECASE), h_next, False),
            (re.compile(rf"{prefix}{mus_queue_info}$", re.IGNORECASE), h_queue_info, False),
            (re.compile(rf"{prefix}{mus_duration}\s+(.+)$", re.IGNORECASE), h_duration, False),
            (re.compile(rf"{prefix}{mus_when}$", re.IGNORECASE), h_when, False),
            (re.compile(rf"{prefix}{mus_random}(?:\s+(\d+))?$", re.IGNORECASE), h_random, False),
            (re.compile(rf"{prefix}{mus_ops}$", re.IGNORECASE), h_ops, False),
            (re.compile(rf"{prefix}{util_help}(?:\s+(\w+))?$", re.IGNORECASE), h_help, False),
            (re.compile(rf"{prefix}{util_version}$", re.IGNORECASE), h_version, False),
            (re.compile(rf"{prefix}{util_uptime}$", re.IGNORECASE), h_uptime, False),
            (re.compile(rf"{prefix}{vote_skip}$", re.IGNORECASE), h_vote, False),
        ]

    def _is_admin(self, username: str) -> bool:
        """Checks if a user has admin permissions. ADMIN_USERS is already lowercase."""
        return username.lower() in ADMIN_USERS

    async def process(self, text: str, username: str, channel_id: str) -> bool:
        """Processes a chat message and responds if it is a command."""
        text_lower = text.lower().strip()

        for pattern, handler, needs_admin in self._commands:
            match = pattern.match(text_lower)
            if match:
                if needs_admin and not self._is_admin(username):
                    await self._send_public(channel_id, "⛔ You don't have permission to use this command.")
                    return True

                try:
                    response = await handler(list(match.groups()), username, channel_id)
                    if response:
                        await self._send_response(response, channel_id)
                        return True
                except Exception as e:
                    import traceback
                    logger.error(f"Error in command: {e}\n" + traceback.format_exc())
                    try:
                        await self._send_public(channel_id, f"❌ Internal error ({type(e).__name__}: {e})")
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
        if self.bot and hasattr(self.bot, "twitch_handler"):
            await self.bot.twitch_handler.send_message(channel_id, message)
