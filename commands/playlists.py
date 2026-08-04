"""Playlist Commands - Commands for playlist management."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main.playlist_manager import PlaylistManager
    from main.main_core import RequestQueue, SongRequestBot


class PlaylistCommands:
    """Handles all playlist-related commands."""

    def __init__(self, playlist_manager: PlaylistManager, request_queue: RequestQueue, bot: SongRequestBot):
        self.playlist_manager = playlist_manager
        self.request_queue = request_queue
        self.bot = bot

    async def cmd_create(self, username: str, nome_playlist: str) -> str:
        """!crea <playlist_name> - Creates a new playlist."""
        playlist = self.playlist_manager.create_playlist(username, nome_playlist)

        if playlist is None:
            return f"❌ A playlist with the name '{nome_playlist}' already exists"

        return f"✅ Playlist '{nome_playlist}' created!"

    async def cmd_playlist(
        self, username: str, nome_playlist: Optional[str] = None, page: int = 1
    ) -> str:
        """!playlist [name] [page] - Shows playlists or songs."""
        if nome_playlist is None:
            playlists = self.playlist_manager.get_user_playlists(username)

            if not playlists:
                return "📭 You don't have any playlists."

            lines = [f"📋 Your playlists ({len(playlists)}):"]
            for p in playlists:
                lines.append(f"  • {p.name} ({len(p.songs)} songs)")

            return "\n".join(lines)
        else:
            songs = self.playlist_manager.get_playlist_songs(username, nome_playlist)

            if not songs:
                return f"❌ Playlist '{nome_playlist}' not found or empty."

            songs_per_page = 8
            total_pages = (len(songs) + songs_per_page - 1) // songs_per_page

            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages

            start = (page - 1) * songs_per_page
            end = start + songs_per_page
            page_songs = songs[start:end]

            lines = [f"🎵 Playlist '{nome_playlist}' ({page}/{total_pages}):"]
            for i, song in enumerate(page_songs, start + 1):
                lines.append(f"  {i}. {song.query}")

            return "\n".join(lines)

    async def cmd_add(
        self,
        username: str,
        nome_playlist: str,
        query: str,
        file_path: str,
        original_user: str,
    ) -> str:
        """!aggiungi <playlist_name> - Adds the current song to the playlist."""
        success = self.playlist_manager.add_song_to_playlist(
            username, nome_playlist, query, file_path, original_user
        )

        if not success:
            return f"❌ Playlist '{nome_playlist}' not found."

        return f"✅ Song added to '{nome_playlist}'"

    async def cmd_remove(
        self, username: str, nome_playlist: str, index_or_name: str
    ) -> str:
        """!rimuovi <playlist_name> <number_or_name> - Removes a song."""
        success = self.playlist_manager.remove_song_from_playlist(
            username, nome_playlist, index_or_name
        )

        if not success:
            return f"❌ Unable to remove the song from '{nome_playlist}'."

        return "✅ Song removed from playlist."

    async def cmd_move(
        self, username: str, nome_playlist: str, num1: str, num2: str
    ) -> str:
        """!sposta <playlist_name> <number1> <number2> - Moves/swaps a song."""
        success = self.playlist_manager.swap_songs_in_playlist(
            username, nome_playlist, num1, num2
        )

        if not success:
            return f"❌ Unable to swap songs in '{nome_playlist}'."

        return "✅ Songs swapped successfully."

    async def cmd_clear(self, username: str, nome_playlist: str) -> str:
        """!svuota <playlist_name> - Removes all songs from the playlist."""
        success = self.playlist_manager.clear_playlist(username, nome_playlist)

        if not success:
            return f"❌ Playlist '{nome_playlist}' not found."

        return "✅ Playlist cleared."

    async def cmd_pump(self, username: str, playlist_name: Optional[str], n: int, channel_id: str) -> str:
        """!pompa [playlist] [n] - Pumps N random songs from a playlist."""
        if playlist_name is None:
            playlists = self.playlist_manager.get_user_playlists(username)

            if not playlists:
                return "📭 You don't have playlists. Use !pompa <playlist_name> [n]."

            if len(playlists) == 1:
                playlist_name = playlists[0].name
            else:
                lines = ["🎯 You have multiple playlists. Specify a name:"]
                for p in playlists:
                    lines.append(f"  • {p.name}")
                return "\n".join(lines)

        songs, error_msg, still_in_queue = self.playlist_manager.pompa_songs(username, playlist_name, n)

        if error_msg:
            return error_msg

        if not songs:
            return f"❌ Playlist '{playlist_name}' not found or empty."

        # Try to find/download each song; remove from playlist if not available
        from main.music_downloader import (
            _SongTooLongError,
            _CategoryError,
            _NoValidCandidateError,
            _ChannelNotTrustedError,
        )
        queued: list[PlaylistSong] = []
        removed_queries: list[str] = []
        for song in songs:
            try:
                path = self.bot.music_downloader.download(song.query)
            except (_SongTooLongError, _CategoryError, _NoValidCandidateError, _ChannelNotTrustedError):
                path = None
            if not path:
                self.playlist_manager.remove_song_from_playlist(
                    username, playlist_name, song.query
                )
                removed_queries.append(song.query)
            else:
                # Update file_path in playlist if it was unknown
                if song.file_path == "unknown" or song.file_path != path:
                    playlist = self.playlist_manager.get_playlist_by_name(username, playlist_name)
                    if playlist:
                        for s in playlist.songs:
                            if s.query == song.query:
                                s.file_path = path
                        self.playlist_manager._save_user_playlists(username)

                request_id = self.request_queue._request_counter
                self.request_queue._request_counter += 1
                from main.main_core import SongRequest
                request = SongRequest(
                    query=path,
                    username=username,
                    channel_id=channel_id,
                    request_id=request_id,
                )
                await self.request_queue.put(request)
                queued.append(song)

        if not queued:
            msg = f"No songs available in '{playlist_name}'."
            if removed_queries:
                msg += f" Removed {len(removed_queries)} unavailable song(s): {', '.join(removed_queries)}"
            return f"❌ {msg}"

        lines = [f"🚰 Pumped {len(queued)} songs from '{playlist_name}':"]
        for i, song in enumerate(queued, 1):
            lines.append(f"  {i}. {song.query} (@{song.username_original})")
        if removed_queries:
            lines.append(f"🗑️ Removed {len(removed_queries)} unavailable song(s): {', '.join(removed_queries)}")

        return "\n".join(lines)
