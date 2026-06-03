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

    async def cmd_crea(self, username: str, nome_playlist: str) -> str:
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
                lines.append(f"  • {p.nome} ({len(p.canzoni)} songs)")

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

    async def cmd_aggiungi(
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

    async def cmd_rimuovi(
        self, username: str, nome_playlist: str, index_or_name: str
    ) -> str:
        """!rimuovi <playlist_name> <number_or_name> - Removes a song."""
        success = self.playlist_manager.remove_song_from_playlist(
            username, nome_playlist, index_or_name
        )

        if not success:
            return f"❌ Unable to remove the song from '{nome_playlist}'."

        return "✅ Song removed from playlist."

    async def cmd_sposta(
        self, username: str, nome_playlist: str, num1: str, num2: str
    ) -> str:
        """!sposta <playlist_name> <number1> <number2> - Moves/swaps a song."""
        success = self.playlist_manager.swap_songs_in_playlist(
            username, nome_playlist, num1, num2
        )

        if not success:
            return f"❌ Unable to swap songs in '{nome_playlist}'."

        return "✅ Songs swapped successfully."

    async def cmd_svuota(self, username: str, nome_playlist: str) -> str:
        """!svuota <playlist_name> - Removes all songs from the playlist."""
        success = self.playlist_manager.clear_playlist(username, nome_playlist)

        if not success:
            return f"❌ Playlist '{nome_playlist}' not found."

        return "✅ Playlist cleared."

    async def cmd_lista_playlist(self, username: str) -> str:
        """!lista_playlist - Shows all available playlists."""
        playlists = self.playlist_manager.get_user_playlists(username)

        if not playlists:
            return "📭 No playlists found."

        lines = [f"📚 Your playlists ({len(playlists)}):"]
        for p in playlists:
            lines.append(f"  • {p.nome} ({len(p.canzoni)} songs)")

        return "\n".join(lines)

    async def cmd_pompa(self, username: str, playlist_name: Optional[str], n: int, channel_id: str) -> str:
        """!pompa [playlist] [n] - Pumps N random songs from a playlist."""
        if playlist_name is None:
            playlists = self.playlist_manager.get_user_playlists(username)

            if not playlists:
                return "📭 You don't have playlists. Use !pompa <playlist_name> [n]."

            if len(playlists) == 1:
                playlist_name = playlists[0].nome
            else:
                lines = ["🎯 You have multiple playlists. Specify a name:"]
                for p in playlists:
                    lines.append(f"  • {p.nome}")
                return "\n".join(lines)

        songs = self.playlist_manager.pompa_songs(username, playlist_name, n)

        if not songs:
            return f"❌ Playlist '{playlist_name}' not found or empty."

        for song in songs:
            request_id = self.request_queue._request_counter
            self.request_queue._request_counter += 1
            from main.main_core import SongRequest
            request = SongRequest(
                query=song.query,
                username=username,
                channel_id=channel_id,
                request_id=request_id,
            )
            await self.request_queue.put(request)

        lines = [f"🚰 Pumped {len(songs)} songs from '{playlist_name}':"]
        for i, song in enumerate(songs, 1):
            lines.append(f"  {i}. {song.query} (@{song.username_original})")

        return "\n".join(lines)
