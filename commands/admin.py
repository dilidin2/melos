"""Admin Commands - Administration and moderation commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from commands import admin_required

if TYPE_CHECKING:
    from main.admin_handler import AdminHandler
    from main.audio_player import AudioPlayer


class AdminCommands:
    """Handles all admin and moderation commands."""

    def __init__(
        self,
        admin_handler: AdminHandler | None = None,
        audio_player: AudioPlayer | None = None,
        request_queue=None,
        bot=None,
    ):
        self.admin_handler = admin_handler
        self.audio_player = audio_player
        self.request_queue = request_queue
        self._bot = bot  # Reference to bot for queue persistence

    @admin_required
    async def cmd_blacklist(self, username: str, target_user: str) -> str:
        """!blacklist <username> - Puts a user on the blacklist."""
        if not self.admin_handler:
            return "❌ Admin handler not available."

        if self.admin_handler.add_blacklist(target_user):
            return f"🚫 {target_user} added to blacklist."
        return f"❌ {target_user} is already on the blacklist."

    @admin_required
    async def cmd_unblacklist(self, username: str, target_user: str) -> str:
        """!unblacklist <username> - Removes a user from the blacklist."""
        if not self.admin_handler:
            return "❌ Admin handler not available."

        if self.admin_handler.remove_blacklist(target_user):
            return f"✅ {target_user} removed from blacklist."
        return f"❌ {target_user} was not on the blacklist."

    @admin_required
    async def cmd_blacklist_list(self, username: str) -> str:
        """!blacklist_list - Shows all blacklisted users."""
        if not self.admin_handler:
            return "❌ Admin handler not available."

        users = self.admin_handler.get_blacklist_list()

        if not users:
            return "📭 Blacklist is empty."

        lines = [f"🚫 Blacklist ({len(users)} users):"]
        for user in users:
            lines.append(f"  • {user}")

        return "\n".join(lines)

    @admin_required
    async def cmd_skip(self, username: str) -> str:
        """!skippa - Skips the current song."""
        if not self.audio_player or not self.audio_player.is_playing():
            return "❌ No song currently playing to skip."

        self.audio_player.stop()
        return "⏭️ Song skipped!"

    @admin_required
    async def cmd_remove_queue(self, username: str, position: str) -> str:
        """!rimuovi_coda <position> - Removes a position from the queue.

        Removes the song at the specified position (1-based) from the queue.
        Position 1 is the next song to play.
        """
        if not self.request_queue:
            return "❌ Unable to access the queue."

        try:
            pos = int(position)
        except ValueError:
            return "❌ Use !rimuovi_coda <number> (e.g.: !rimuovi_coda 3)"

        if pos < 1:
            return "❌ Position must be a positive number (minimum 1)."

        items = self.request_queue.get_items(count=1000)
        if pos > len(items):
            return f"❌ Invalid position. The queue only has {len(items)} songs."

        # Use the public API — mutates in-place, lock-protected
        removed_item = await self.request_queue.remove_by_index(pos - 1)
        if not removed_item:
            return f"❌ Unable to remove position {pos}."

        logger.info(
            f"Item removed from queue (position {pos}): "
            f"{removed_item.query} by @{removed_item.username}"
        )

        # Get the title for the message
        title = removed_item.query
        if self._bot and hasattr(self._bot, 'music_downloader'):
            song_info = self._bot.music_downloader.get_song_info(removed_item.query)
            if song_info:
                title = song_info.get("title", removed_item.query)

        # Persist the change
        if self._bot and hasattr(self._bot, '_persist_queue'):
            import asyncio
            try:
                asyncio.create_task(self._bot._persist_queue())
            except Exception:
                pass

        return f"🗑️ Removed **{title}** from queue (position {pos})"

    @admin_required
    async def cmd_volume(self, username: str, level: int) -> str:
        """!volume <0-100> - Set or show current volume."""
        if level < 0 or level > 100:
            return "❌ Volume level must be between 0 and 100."

        if self.audio_player:
            pygame_volume = level / 100.0
            import pygame
            pygame.mixer.music.set_volume(pygame_volume)
            logger.info(f"Volume set to {level}% by @{username}")

        return f"🔊 Volume set to {level}%"

    @admin_required
    async def cmd_clear_queue(self, username: str) -> str:
        """!clear_queue - Completely clears the queue.

        Removes all songs from the queue. This operation cannot
        be undone.
        """
        if not self.request_queue:
            return "❌ Unable to access the queue."

        items = self.request_queue.get_items(count=1000)
        count = len(items)

        if count == 0:
            return "📭 The queue is already empty."

        # Use the public API — mutates in-place, lock-protected
        await self.request_queue.clear()

        logger.info(f"Queue cleared by @{username}: {count} songs removed")

        # Persist the change
        if self._bot and hasattr(self._bot, '_persist_queue'):
            import asyncio
            try:
                asyncio.create_task(self._bot._persist_queue())
            except Exception:
                pass

        return f"🗑️ Queue cleared: **{count}** songs removed"


