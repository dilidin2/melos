"""Playlist Commands - Comandi per la gestione delle playlist."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main.playlist_manager import PlaylistManager
    from main.main_core import RequestQueue, SongRequestBot


class PlaylistCommands:
    """Gestisce tutti i comandi relativi alle playlist."""

    def __init__(self, playlist_manager: PlaylistManager, request_queue: RequestQueue, bot: SongRequestBot):
        self.playlist_manager = playlist_manager
        self.request_queue = request_queue
        self.bot = bot

    async def cmd_crea(self, username: str, nome_playlist: str) -> str:
        """!crea <nome_playlist> - Crea una nuova playlist."""
        playlist = self.playlist_manager.create_playlist(username, nome_playlist)

        if playlist is None:
            return f"❌ Esisti già una playlist con questo nome '{nome_playlist}'"

        return f"✅ Playlist '{nome_playlist}' creata!"

    async def cmd_playlist(
        self, username: str, nome_playlist: Optional[str] = None
    ) -> str:
        """!playlist [nome] - Mostra playlist o canzoni."""
        if nome_playlist is None:
            playlists = self.playlist_manager.get_user_playlists(username)

            if not playlists:
                return "📭 Non hai playlist create."

            lines = [f"📋 Le tue playlist ({len(playlists)}):"]
            for p in playlists:
                lines.append(f"  • {p.nome} ({len(p.canzoni)} canzoni)")

            return "\n".join(lines)
        else:
            songs = self.playlist_manager.get_playlist_songs(username, nome_playlist)

            if not songs:
                return f"❌ Playlist '{nome_playlist}' non trovata o vuota."

            lines = [f"🎵 Playlist '{nome_playlist}':"]
            for i, song in enumerate(songs, 1):
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
        """!aggiungi <nome_playlist> - Aggiunge la canzone corrente alla playlist."""
        success = self.playlist_manager.add_song_to_playlist(
            username, nome_playlist, query, file_path, original_user
        )

        if not success:
            return f"❌ Playlist '{nome_playlist}' non trovata."

        return f"✅ Canzone aggiunta a '{nome_playlist}'"

    async def cmd_rimuovi(
        self, username: str, nome_playlist: str, index_or_name: str
    ) -> str:
        """!rimuovi <nome_playlist> <numero_o_nome> - Rimuove una canzone."""
        success = self.playlist_manager.remove_song_from_playlist(
            username, nome_playlist, index_or_name
        )

        if not success:
            return f"❌ Impossibile rimuovere la canzone da '{nome_playlist}'."

        return "✅ Canzone rimossa dalla playlist."

    async def cmd_sposta(
        self, username: str, nome_playlist: str, num1: str, num2: str
    ) -> str:
        """!sposta <nome_playlist> <numero1> <numero2> - Sposta una canzone."""
        success = self.playlist_manager.swap_songs_in_playlist(
            username, nome_playlist, num1, num2
        )

        if not success:
            return f"❌ Impossibile spostare le canzoni in '{nome_playlist}'."

        return "✅ Canzoni spostate con successo."

    async def cmd_svuota(self, username: str, nome_playlist: str) -> str:
        """!svuota <nome_playlist> - Rimuove tutte le canzoni dalla playlist."""
        success = self.playlist_manager.clear_playlist(username, nome_playlist)

        if not success:
            return f"❌ Playlist '{nome_playlist}' non trovata."

        return "✅ Playlist svuotata."

    async def cmd_lista_playlist(self, username: str) -> str:
        """!lista_playlist - Mostra tutte le playlist disponibili."""
        playlists = self.playlist_manager.get_user_playlists(username)

        if not playlists:
            return "📭 Nessuna playlist trovata."

        lines = [f"📚 Le tue playlist ({len(playlists)}):"]
        for p in playlists:
            lines.append(f"  • {p.nome} ({len(p.canzoni)} canzoni)")

        return "\n".join(lines)

    async def cmd_pompa(self, username: str, playlist_name: Optional[str], n: int, channel_id: str) -> str:
        """!pompa [playlist] [n] - Pompa N canzoni random da una playlist."""
        if playlist_name is None:
            playlists = self.playlist_manager.get_user_playlists(username)

            if not playlists:
                return "📭 Non hai playlist. Usa !pompa <nome_playlist> [n]."

            if len(playlists) == 1:
                playlist_name = playlists[0].nome
            else:
                lines = ["🎯 Hai multiple playlist. Specifica un nome:"]
                for p in playlists:
                    lines.append(f"  • {p.nome}")
                return "\n".join(lines)

        songs = self.playlist_manager.pompa_songs(username, playlist_name, n)

        if not songs:
            return f"❌ Playlist '{playlist_name}' non trovata o vuota."

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

        lines = [f"🚰 Pompate {len(songs)} canzoni da '{playlist_name}':"]
        for i, song in enumerate(songs, 1):
            lines.append(f"  {i}. {song.query} (@{song.username_original})")

        return "\n".join(lines)
