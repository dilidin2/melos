"""Playlist Manager - Gestisce le playlist degli utenti."""

import json
import os
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PlaylistSong:
    """Rappresenta una canzone in una playlist."""

    query: str
    file_path: str
    username_original: str
    aggiunta_al: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlaylistSong":
        return cls(**data)


@dataclass
class Playlist:
    """Rappresenta una playlist utente."""

    id: str
    nome: str
    canzoni: list[PlaylistSong] = field(default_factory=list)
    creata_al: str = field(default_factory=lambda: datetime.now().isoformat())
    ultima_modificata: str = field(default_factory=lambda: datetime.now().isoformat())
    recently_pumped_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "canzoni": [c.to_dict() for c in self.canzoni],
            "creata_al": self.creata_al,
            "ultima_modificata": self.ultima_modificata,
            "recently_pumped_queries": self.recently_pumped_queries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Playlist":
        canzoni = [PlaylistSong.from_dict(c) for c in data.get("canzoni", [])]
        return cls(
            id=data["id"],
            nome=data["nome"],
            canzoni=canzoni,
            creata_al=data.get("creata_al"),
            ultima_modificata=data.get("ultima_modificata"),
            recently_pumped_queries=data.get("recently_pumped_queries", []),
        )


class PlaylistManager:
    """Gestisce tutte le playlist degli utenti."""

    def __init__(self, data_dir: str = "data/playlists"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._playlists: dict[
            str, dict[str, Playlist]
        ] = {}  # user -> {playlist_id: Playlist}

    def _get_user_file(self, username: str) -> Path:
        """Ottieni il percorso del file JSON per un utente."""
        return self.data_dir / f"{username}.json"

    def _load_user_playlists(self, username: str) -> dict[str, Playlist]:
        """Carica le playlist di un utente dal disco."""
        user_file = self._get_user_file(username)

        if not user_file.exists():
            return {}

        try:
            with open(user_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            playlists = {}
            for playlist_id, playlist_data in data.items():
                playlists[playlist_id] = Playlist.from_dict(playlist_data)

            return playlists

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Errore nel caricamento playlist per {username}: {e}")
            return {}

    def _save_user_playlists(self, username: str):
        """Salva le playlist di un utente sul disco."""
        user_file = self._get_user_file(username)

        if username not in self._playlists:
            return

        data = {}
        for playlist_id, playlist in self._playlists[username].items():
            data[playlist_id] = playlist.to_dict()

        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_playlist(self, username: str, nome: str) -> Optional[Playlist]:
        """Crea una nuova playlist per un utente."""
        if username not in self._playlists:
            self._playlists[username] = {}

        # Controlla se esiste già una playlist con questo nome
        for playlist in self._playlists[username].values():
            if playlist.nome.lower() == nome.lower():
                return None

        import uuid

        playlist_id = str(uuid.uuid4().int)

        playlist = Playlist(id=playlist_id, nome=nome)

        self._playlists[username][playlist_id] = playlist
        self._save_user_playlists(username)

        return playlist

    def get_user_playlists(self, username: str) -> list[Playlist]:
        """Ottieni tutte le playlist di un utente."""
        if username not in self._playlists:
            self._playlists[username] = self._load_user_playlists(username)

        return list(self._playlists[username].values())

    def get_playlist(self, username: str, playlist_id: str) -> Optional[Playlist]:
        """Ottieni una playlist specifica."""
        if username not in self._playlists:
            self._playlists[username] = self._load_user_playlists(username)

        return self._playlists[username].get(playlist_id)

    def get_playlist_by_name(self, username: str, nome: str) -> Optional[Playlist]:
        """Ottieni una playlist per nome."""
        playlists = self.get_user_playlists(username)

        for playlist in playlists:
            if playlist.nome.lower() == nome.lower():
                return playlist

        return None

    def add_song_to_playlist(
        self,
        username: str,
        playlist_name: str,
        query: str,
        file_path: str,
        original_user: str,
    ) -> bool:
        """Aggiunge una canzone a una playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        song = PlaylistSong(
            query=query, file_path=file_path, username_original=original_user
        )

        playlist.canzoni.append(song)
        playlist.ultima_modificata = datetime.now().isoformat()

        self._save_user_playlists(username)

        return True

    def remove_song_from_playlist(
        self, username: str, playlist_name: str, index_or_name: str
    ) -> bool:
        """Rimuove una canzone da una playlist per indice o nome."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        try:
            # Prova a interpretare come numero
            index = int(index_or_name) - 1

            if 0 <= index < len(playlist.canzoni):
                playlist.canzoni.pop(index)
                playlist.ultima_modificata = datetime.now().isoformat()
                self._save_user_playlists(username)
                return True
            return False

        except ValueError:
            # Cerca per nome/titolo
            for i, song in enumerate(playlist.canzoni):
                if index_or_name.lower() in song.query.lower():
                    playlist.canzoni.pop(i)
                    playlist.ultima_modificata = datetime.now().isoformat()
                    self._save_user_playlists(username)
                    return True

            return False

    def swap_songs_in_playlist(
        self, username: str, playlist_name: str, index1: int, index2: int
    ) -> bool:
        """Scambia due canzoni in una playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        try:
            # Converte da 1-based a 0-based
            idx1 = int(index1) - 1
            idx2 = int(index2) - 1

            if 0 <= idx1 < len(playlist.canzoni) and 0 <= idx2 < len(playlist.canzoni):
                playlist.canzoni[idx1], playlist.canzoni[idx2] = (
                    playlist.canzoni[idx2],
                    playlist.canzoni[idx1],
                )

                playlist.ultima_modificata = datetime.now().isoformat()
                self._save_user_playlists(username)
                return True

            return False

        except (ValueError, TypeError):
            return False

    def clear_playlist(self, username: str, playlist_name: str) -> bool:
        """Svuota una playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        playlist.canzoni.clear()
        playlist.ultima_modificata = datetime.now().isoformat()

        self._save_user_playlists(username)

        return True

    def get_playlist_songs(
        self, username: str, playlist_name: str
    ) -> list[PlaylistSong]:
        """Ottiene tutte le canzoni di una playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return []

        return playlist.canzoni

    def pompa_songs(
        self, username: str, playlist_name: str, n: int = 5
    ) -> list[PlaylistSong]:
        """Seleziona N canzoni random dalla playlist, escludendo le ultime pompate.
        
        Sliding window: ogni chiamata dimentica la precedente e ne seleziona N nuove.
        Se non ci sono canzoni disponibili (tutte usate), resetta il tracking.
        """
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return []

        if len(playlist.canzoni) == 0:
            return []

        # Filtra le canzoni non recentemente pompate
        excluded = set(playlist.recently_pumped_queries)
        available = [s for s in playlist.canzoni if s.query not in excluded]

        # Se nessuna disponibile, resetta il tracking
        if not available:
            playlist.recently_pumped_queries = []
            available = list(playlist.canzoni)

        # Prendi fino a N canzoni random
        count = min(n, len(available))
        selected = random.sample(available, count)

        # Aggiorna il tracking con le query delle canzoni selezionate
        playlist.recently_pumped_queries = [s.query for s in selected]
        playlist.ultima_modificata = datetime.now().isoformat()

        self._save_user_playlists(username)

        return selected
