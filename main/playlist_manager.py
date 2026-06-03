"""Playlist Manager - Manages user playlists."""

import json
import os
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PlaylistSong:
    """Represents a song in a playlist."""

    query: str
    file_path: str
    username_original: str
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlaylistSong":
        return cls(**data)


@dataclass
class Playlist:
    """Represents a user playlist."""

    id: str
    name: str
    songs: list[PlaylistSong] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    recently_pumped_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "songs": [c.to_dict() for c in self.songs],
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "recently_pumped_queries": self.recently_pumped_queries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Playlist":
        songs = [PlaylistSong.from_dict(c) for c in data.get("songs", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            songs=songs,
            created_at=data.get("created_at"),
            last_modified=data.get("last_modified"),
            recently_pumped_queries=data.get("recently_pumped_queries", []),
        )


class PlaylistManager:
    """Manages all user playlists."""

    def __init__(self, data_dir: str = "data/playlists"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._playlists: dict[
            str, dict[str, Playlist]
        ] = {}  # user -> {playlist_id: Playlist}

    def _get_user_file(self, username: str) -> Path:
        """Gets the JSON file path for a user."""
        return self.data_dir / f"{username}.json"

    def _load_user_playlists(self, username: str) -> dict[str, Playlist]:
        """Loads a user's playlists from disk."""
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
            print(f"Error loading playlists for {username}: {e}")
            return {}

    def _save_user_playlists(self, username: str):
        """Saves a user's playlists to disk."""
        user_file = self._get_user_file(username)

        if username not in self._playlists:
            return

        data = {}
        for playlist_id, playlist in self._playlists[username].items():
            data[playlist_id] = playlist.to_dict()

        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_playlist(self, username: str, name: str) -> Optional[Playlist]:
        """Creates a new playlist for a user."""
        if username not in self._playlists:
            self._playlists[username] = {}

        # Check if a playlist with this name already exists
        for playlist in self._playlists[username].values():
            if playlist.name.lower() == name.lower():
                return None

        import uuid

        playlist_id = str(uuid.uuid4().int)

        playlist = Playlist(id=playlist_id, name=name)

        self._playlists[username][playlist_id] = playlist
        self._save_user_playlists(username)

        return playlist

    def get_user_playlists(self, username: str) -> list[Playlist]:
        """Gets all playlists for a user."""
        if username not in self._playlists:
            self._playlists[username] = self._load_user_playlists(username)

        return list(self._playlists[username].values())

    def get_playlist(self, username: str, playlist_id: str) -> Optional[Playlist]:
        """Gets a specific playlist."""
        if username not in self._playlists:
            self._playlists[username] = self._load_user_playlists(username)

        return self._playlists[username].get(playlist_id)

    def get_playlist_by_name(self, username: str, name: str) -> Optional[Playlist]:
        """Gets a playlist by name."""
        playlists = self.get_user_playlists(username)

        for playlist in playlists:
            if playlist.name.lower() == name.lower():
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
        """Adds a song to a playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        song = PlaylistSong(
            query=query, file_path=file_path, username_original=original_user
        )

        playlist.songs.append(song)
        playlist.last_modified = datetime.now().isoformat()

        self._save_user_playlists(username)

        return True

    def remove_song_from_playlist(
        self, username: str, playlist_name: str, index_or_name: str
    ) -> bool:
        """Removes a song from a playlist by index or name."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        try:
            # Try to interpret as a number
            index = int(index_or_name) - 1

            if 0 <= index < len(playlist.songs):
                playlist.songs.pop(index)
                playlist.last_modified = datetime.now().isoformat()
                self._save_user_playlists(username)
                return True
            return False

        except ValueError:
            # Search by name/title
            for i, song in enumerate(playlist.songs):
                if index_or_name.lower() in song.query.lower():
                    playlist.songs.pop(i)
                    playlist.last_modified = datetime.now().isoformat()
                    self._save_user_playlists(username)
                    return True

            return False

    def swap_songs_in_playlist(
        self, username: str, playlist_name: str, index1: int, index2: int
    ) -> bool:
        """Swaps two songs in a playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        try:
            # Converts from 1-based to 0-based
            idx1 = int(index1) - 1
            idx2 = int(index2) - 1

            if 0 <= idx1 < len(playlist.songs) and 0 <= idx2 < len(playlist.songs):
                playlist.songs[idx1], playlist.songs[idx2] = (
                    playlist.songs[idx2],
                    playlist.songs[idx1],
                )

                playlist.last_modified = datetime.now().isoformat()
                self._save_user_playlists(username)
                return True

            return False

        except (ValueError, TypeError):
            return False

    def clear_playlist(self, username: str, playlist_name: str) -> bool:
        """Clears a playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return False

        playlist.songs.clear()
        playlist.last_modified = datetime.now().isoformat()

        self._save_user_playlists(username)

        return True

    def get_playlist_songs(
        self, username: str, playlist_name: str
    ) -> list[PlaylistSong]:
        """Gets all songs in a playlist."""
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return []

        return playlist.songs

    def pompa_songs(
        self, username: str, playlist_name: str, n: int = 5
    ) -> list[PlaylistSong]:
        """Selects N random songs from the playlist, excluding the last pumped ones.

        Sliding window: each call forgets the previous one and selects N new ones.
        If no songs are available (all used), resets the tracking.
        """
        playlist = self.get_playlist_by_name(username, playlist_name)

        if not playlist:
            return []

        if len(playlist.songs) == 0:
            return []

        # Filter songs not recently pumped
        excluded = set(playlist.recently_pumped_queries)
        available = [s for s in playlist.songs if s.query not in excluded]

        # If none available, reset tracking
        if not available:
            playlist.recently_pumped_queries = []
            available = list(playlist.songs)

        # Take up to N random songs
        count = min(n, len(available))
        selected = random.sample(available, count)

        # Update tracking with the selected songs' queries
        playlist.recently_pumped_queries = [s.query for s in selected]
        playlist.last_modified = datetime.now().isoformat()

        self._save_user_playlists(username)

        return selected
