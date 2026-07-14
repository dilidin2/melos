"""Music Commands - Commands for playback control."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from loguru import logger

from main.config import VOTE_REQUIRED_COUNT

if TYPE_CHECKING:
    from main.audio_player import AudioPlayer
    from main.main_core import RequestQueue
    from main.music_downloader import MusicDownloader


class MusicCommands:
    """Handles all advanced music commands."""

    def __init__(
        self,
        audio_player: "AudioPlayer" | None = None,
        request_queue: "RequestQueue" | None = None,
        music_downloader: "MusicDownloader" | None = None,
        bot=None,
    ):
        self.audio_player = audio_player
        self._request_queue = request_queue
        self._music_downloader = music_downloader
        self._bot = bot  # Reference to bot to access repeat settings

    async def cmd_pause(self, username: str) -> str:
        """!pause - Pauses playback."""
        if not self.audio_player or not self.audio_player.is_playing():
            return "❌ No song currently playing."

        self.audio_player.pause()
        return "⏸️ Playback paused."

    async def cmd_resume(self, username: str) -> str:
        """!resume - Resumes playback."""
        if not self.audio_player or not self.audio_player.is_paused():
            return "❌ No song currently paused."

        self.audio_player.resume()
        return "▶️ Playback resumed."

    async def cmd_repeat(self, username: str, count: int = 1) -> str:
        """!repeat [number] - Repeats the current song N times.

        If count < 0, repeat is infinite.
        If count == 0, disables repeat.
        """
        # Update bot state if available
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            if count < 0:
                self._bot.repeat_mode = 'infinite'
                self._bot.repeat_remaining = 0  # 0 = infinite for the processor
                return "🔁 Repeat enabled (infinite)"
            elif count == 0:
                self._bot.repeat_mode = 'off'
                self._bot.repeat_remaining = 0
                return "🔁 Repeat mode disabled"
            else:
                self._bot.repeat_mode = 'count'
                self._bot.repeat_count = count
                self._bot.repeat_remaining = count  # Initialize counter
                return f"🔁 Repeat enabled ({count} times)"

        # Fallback if bot doesn't have repeat_mode field
        if count < 0:
            return "🔁 Repeat enabled (infinite)"
        if count == 0:
            return "🔁 Repeat mode disabled"
        return f"🔁 Repeat enabled ({count} times)"

    async def cmd_repeat_off(self, username: str) -> str:
        """!repeat_off - Disables repeat."""
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            self._bot.repeat_mode = 'off'
            self._bot.repeat_remaining = 0
            return "🔁 Repeat mode disabled"
        return "🔁 Repeat mode disabled"

    async def cmd_stop_repeat(self, username: str) -> str:
        """!stop_repeat - Stops repeat and returns to normal flow.

        Disables current repeat and lets the bot proceed
        with the queue normally.
        """
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            self._bot.repeat_mode = 'off'
            logger.info(f"Repeat disabled by @{username}")

        return "🔁 Repeat disabled"

    async def cmd_next(self, username: str) -> str:
        """!next - Shows the next song in the queue."""
        if not self._request_queue:
            return "❌ Unable to access the queue."

        items = self._request_queue.get_items(count=1)
        if not items:
            return "⏭️ No songs in the queue."

        request = items[0]
        if self._music_downloader:
            song_info = self._music_downloader.get_song_info(request.query)
            if song_info:
                title = song_info.get("title", request.query)
            else:
                title = request.query
        else:
            title = request.query

        return f"⏭️ Next song: **{title}** (requested by @{request.username})"

    async def cmd_queue_info(self, username: str) -> str:
        """!queue_info - Shows complete queue info.

        Includes: number of songs in queue, next song,
        estimated total duration and repeat status.
        """
        if not self._request_queue:
            return "❌ Unable to access the queue."

        items = self._request_queue.get_items(count=10)
        if not items:
            return "📊 Queue info: Queue is empty."

        # Calculate estimated total duration
        total_duration = 0
        for item in items:
            if self._music_downloader:
                song_info = self._music_downloader.get_song_info(item.query)
                if song_info and song_info.get("duration", 0) > 0:
                    total_duration += song_info["duration"]
            # If we don't have info, use 4 minutes as average
            if total_duration == 0:
                total_duration += 240  # 4 minutes

        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60

        # Repeat status
        repeat_status = "Disabled"
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            if self._bot.repeat_mode == 'infinite':
                repeat_status = "Infinite"
            elif self._bot.repeat_mode == 'count':
                repeat_status = f"{self._bot.repeat_count} times"
            else:
                repeat_status = "Disabled"

        lines = [
            f"📊 **Queue Info:**",
            f"  • Songs in queue: {len(items)}",
            f"  • Estimated duration: {hours}h {minutes}m",
            f"  • Repeat: {repeat_status}",
            f"  • Next: **{items[0].query}**",
        ]

        return "\n".join(lines)

    async def cmd_duration(self, username: str, query: str) -> str:
        """!duration <song> - Shows the duration of a song.

        Searches for the song in the local database or on YouTube.
        """
        if not self._music_downloader:
            return "❌ Unable to access the downloader."

        song_info = self._music_downloader.get_song_info(query)
        if song_info:
            title = song_info.get("title", query)
            duration_seconds = song_info.get("duration", 0)
            if duration_seconds > 0:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/D"
            return f"⏱️ **{title}**: {duration_str}"
        else:
            return f"⏱️ Duration of '{query}': not found in local database"

    async def cmd_at(self, position_str: str, username: str, channel_id: str) -> str:
        """!durata <N> - Shows duration of song at position N in the queue."""
        try:
            position = int(position_str)
        except ValueError:
            return "❌ Use !durata <number> (e.g.: !durata 3)"

        if position < 1:
            return "❌ Position must be a positive number (minimum 1)."

        if not self._request_queue or not self._music_downloader:
            return "❌ Unable to access the queue."

        items = self._request_queue.get_items(count=position)
        if len(items) < position:
            return f"❌ The queue only has {len(items)} songs. Use a smaller or equal number."

        request = items[position - 1]  # 1-based
        song_info = self._music_downloader.get_song_info(request.query)

        if song_info:
            duration_seconds = song_info.get("duration", 0)
            if duration_seconds > 0:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/D"
            title = song_info.get("title", request.query)
        else:
            title = request.query
            duration_str = "N/D"

        return f"⏱️ Song #{position}: **'{title}'** - Duration: {duration_str}"

    async def cmd_when(self, username: str, channel_id: str) -> str:
        """!quando - Estimates when your next song will play in the queue."""
        if not self._request_queue:
            return "❌ Unable to access the queue."

        items = self._request_queue.get_items(count=50)  # Check up to 50 songs

        # Find the first request from the current user in the queue
        user_request = None
        user_position = -1
        for i, request in enumerate(items):
            if request.username == username:
                user_request = request
                user_position = i
                break

        if user_request is None:
            return "❌ You don't have any songs in the queue."

        # Calculate estimated time (average duration 4 minutes per song)
        avg_duration_seconds = 4 * 60  # 4 minutes
        songs_before = user_position
        estimated_seconds = songs_before * avg_duration_seconds

        if estimated_seconds >= 3600:
            hours = estimated_seconds // 3600
            remaining_minutes = (estimated_seconds % 3600) // 60
            time_str = f"{hours}:{remaining_minutes:02d}"
        else:
            minutes = estimated_seconds // 60
            seconds = estimated_seconds % 60
            time_str = f"{minutes}:{seconds:02d}"

        # Get the song title
        song_info = self._music_downloader.get_song_info(user_request.query)
        if song_info:
            title = song_info.get("title", user_request.query)
        else:
            title = user_request.query

        if songs_before == 0:
            return f"🕐 Your next song (**'{title}'**) will play **now!**"
        else:
            return f"🕐 Your next song (**'{title}'**) will play in about {time_str} ({songs_before} songs)"

    async def cmd_random(self, username: str, n: int = 1) -> str:
        """!random [N] - Plays N random songs from the downloaded library."""
        import os
        import random as random_module
        from main.config import DOWNLOAD_DIR, VOTE_REQUIRED_COUNT
        from main.main_core import SongRequest

        try:
            files = os.listdir(DOWNLOAD_DIR)
            audio_files = [
                f for f in files if f.lower().endswith((".mp3", ".wav", ".m4a"))
            ]
        except Exception as e:
            logger.error(f"Error reading downloads directory: {e}")
            return "❌ Unable to read the music library."

        if not audio_files:
            return "📭 No songs downloaded in the library. Download something first with !sr!"

        # Avoid repeating the same song twice in a row
        last_song = getattr(self._bot, 'last_random_song', None)
        available = [f for f in audio_files if f != last_song] if last_song else audio_files

        count = min(n, len(available))
        selected = random_module.sample(available, count)

        if count == 0:
            return "📭 Library empty or no tracks available."

        for song_file in selected:
            request_id = self._request_queue._request_counter
            self._request_queue._request_counter += 1
            # Pass the full path so download() finds it right away without searching on YouTube
            full_path = os.path.join(DOWNLOAD_DIR, song_file)
            request = SongRequest(
                query=full_path,
                username=username,
                channel_id="",
                request_id=request_id,
            )
            await self._request_queue.put(request)

            # Update tracking to avoid consecutive repetitions
            if self._bot and hasattr(self._bot, 'last_random_song'):
                self._bot.last_random_song = song_file

        song_names = [os.path.splitext(f)[0] for f in selected]
        if n == 1:
            return f"🎲 Random song from library: **{song_names[0]}**"
        else:
            lines = [f"🎲 {count} random songs from library:"]
            for i, name in enumerate(song_names, 1):
                lines.append(f"  {i}. {name}")
            return "\n".join(lines)

    async def cmd_ops(self, username: str) -> str:
        """!ops - Remove the last song you added from the queue."""
        if not self._request_queue:
            return "❌ Unable to access the queue."

        queue_list = self._request_queue.queue._queue
        # Search from the end to find the LAST song by this user
        user_request = None
        for i in range(len(queue_list) - 1, -1, -1):
            if queue_list[i].username == username:
                user_request = queue_list[i]
                del queue_list[i]
                break

        if user_request is None:
            return "❌ You don't have any songs in the queue."

        # Use the user's original query — no online lookup needed
        title = user_request.query

        # Persist the change
        if self._bot and hasattr(self._bot, '_persist_queue'):
            import asyncio
            try:
                asyncio.create_task(self._bot._persist_queue())
            except Exception:
                pass

        return f"🗑️ Removed **{title}** from the queue (your last song)."

    async def cmd_vote(self, username: str) -> str:
        """!vote - Vote to skip the current song (needs N voters)."""
        if not self._bot or not hasattr(self._bot, 'audio_player'):
            return "❌ Bot not available."

        if not self._bot.audio_player.is_playing():
            return "❌ No song is currently playing."

        if not self._bot._vote_active:
            return "❌ No song currently accepting votes."

        triggered = self._bot.process_vote(username)
        voter_count = len(self._bot._vote_skip_voters)

        if triggered:
            self._bot.audio_player.stop()
            self._bot.reset_votes()
            voters_list = ', '.join(sorted(self._bot._vote_skip_voters))
            return f"⏭️ Song skipped! ({VOTE_REQUIRED_COUNT}/{VOTE_REQUIRED_COUNT} votes: {voters_list})"
        else:
            remaining = VOTE_REQUIRED_COUNT - voter_count
            return f"🗳️ Vote registered for @{username} ({voter_count}/{VOTE_REQUIRED_COUNT}). {remaining} more needed."
