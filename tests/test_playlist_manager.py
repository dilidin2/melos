"""Tests for playlist_manager module."""

import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from main.playlist_manager import Playlist, PlaylistSong, PlaylistManager


class TestPlaylistSong:
    """Tests for PlaylistSong dataclass."""

    def test_create_playlist_song(self):
        """Test creating a PlaylistSong."""
        song = PlaylistSong(
            query="Test Song",
            file_path="/path/to/song.mp3",
            username_original="testuser"
        )
        assert song.query == "Test Song"
        assert song.file_path == "/path/to/song.mp3"
        assert song.username_original == "testuser"
        assert song.aggiunta_al is not None

    def test_to_dict(self):
        """Test converting PlaylistSong to dict."""
        song = PlaylistSong(
            query="Test Song",
            file_path="/path/to/song.mp3",
            username_original="testuser",
            aggiunta_al="2025-01-01T00:00:00"
        )
        d = song.to_dict()
        assert d["query"] == "Test Song"
        assert d["file_path"] == "/path/to/song.mp3"
        assert d["username_original"] == "testuser"

    def test_from_dict(self):
        """Test creating PlaylistSong from dict."""
        data = {
            "query": "Test Song",
            "file_path": "/path/to/song.mp3",
            "username_original": "testuser",
            "aggiunta_al": "2025-01-01T00:00:00"
        }
        song = PlaylistSong.from_dict(data)
        assert song.query == "Test Song"
        assert song.file_path == "/path/to/song.mp3"
        assert song.username_original == "testuser"


class TestPlaylist:
    """Tests for Playlist dataclass."""

    def test_create_playlist(self):
        """Test creating a Playlist."""
        playlist = Playlist(id="123", name="Test Playlist")
        assert playlist.id == "123"
        assert playlist.name == "Test Playlist"
        assert playlist.songs == []
        assert playlist.created_at is not None

    def test_to_dict(self):
        """Test converting Playlist to dict."""
        song = PlaylistSong("Song", "/path", "user")
        playlist = Playlist(id="123", name="Test", songs=[song])
        d = playlist.to_dict()
        assert d["id"] == "123"
        assert d["name"] == "Test"
        assert len(d["songs"]) == 1
        assert d["recently_pumped_queries"] == []

    def test_from_dict(self):
        """Test creating Playlist from dict."""
        data = {
            "id": "123",
            "name": "Test",
            "songs": [{"query": "Song", "file_path": "/path", "username_original": "user"}],
            "created_at": "2025-01-01",
            "last_modified": "2025-01-02",
            "recently_pumped_queries": []
        }
        playlist = Playlist.from_dict(data)
        assert playlist.id == "123"
        assert playlist.name == "Test"
        assert len(playlist.songs) == 1
        assert playlist.songs[0].query == "Song"


class TestPlaylistManager:
    """Tests for PlaylistManager class."""

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a PlaylistManager with temp dir."""
        return PlaylistManager(data_dir=os.path.join(temp_dir, "playlists"))

    def test_init_creates_data_dir(self, temp_dir):
        """Test init creates data directory."""
        data_dir = os.path.join(temp_dir, "test_playlists")
        manager = PlaylistManager(data_dir=data_dir)
        assert os.path.exists(data_dir)

    def test_create_playlist(self, manager):
        """Test creating a playlist."""
        playlist = manager.create_playlist("testuser", "My Playlist")
        assert playlist is not None
        assert playlist.name == "My Playlist"
        assert playlist.id is not None

    def test_create_duplicate_playlist(self, manager):
        """Test creating a playlist with duplicate name."""
        manager.create_playlist("testuser", "My Playlist")
        duplicate = manager.create_playlist("testuser", "my playlist")
        assert duplicate is None

    def test_create_playlist_case_insensitive_name(self, manager):
        """Test duplicate detection is case insensitive."""
        manager.create_playlist("testuser", "My Playlist")
        duplicate = manager.create_playlist("testuser", "MY PLAYLIST")
        assert duplicate is None

    def test_get_user_playlists_empty(self, manager):
        """Test getting playlists for user with no playlists."""
        playlists = manager.get_user_playlists("emptyuser")
        assert playlists == []

    def test_get_user_playlists(self, manager):
        """Test getting playlists for user with playlists."""
        manager.create_playlist("testuser", "Playlist 1")
        manager.create_playlist("testuser", "Playlist 2")
        playlists = manager.get_user_playlists("testuser")
        assert len(playlists) == 2

    def test_get_playlist_by_id(self, manager):
        """Test getting a playlist by ID."""
        playlist = manager.create_playlist("testuser", "My Playlist")
        retrieved = manager.get_playlist("testuser", playlist.id)
        assert retrieved is not None
        assert retrieved.name == "My Playlist"

    def test_get_playlist_not_found(self, manager):
        """Test getting a non-existent playlist."""
        retrieved = manager.get_playlist("testuser", "nonexistent-id")
        assert retrieved is None

    def test_get_playlist_by_name(self, manager):
        """Test getting a playlist by name."""
        manager.create_playlist("testuser", "My Playlist")
        retrieved = manager.get_playlist_by_name("testuser", "My Playlist")
        assert retrieved is not None
        assert retrieved.name == "My Playlist"

    def test_get_playlist_by_name_case_insensitive(self, manager):
        """Test getting playlist by name is case insensitive."""
        manager.create_playlist("testuser", "My Playlist")
        retrieved = manager.get_playlist_by_name("testuser", "MY PLAYLIST")
        assert retrieved is not None

    def test_get_playlist_by_name_not_found(self, manager):
        """Test getting non-existent playlist by name."""
        retrieved = manager.get_playlist_by_name("testuser", "Nonexistent")
        assert retrieved is None

    def test_add_song_to_playlist(self, manager):
        """Test adding a song to a playlist."""
        manager.create_playlist("testuser", "My Playlist")
        success = manager.add_song_to_playlist(
            "testuser", "My Playlist", "Test Song", "/path.mp3", "original_user"
        )
        assert success is True
        songs = manager.get_playlist_songs("testuser", "My Playlist")
        assert len(songs) == 1
        assert songs[0].query == "Test Song"

    def test_add_song_to_nonexistent_playlist(self, manager):
        """Test adding song to non-existent playlist."""
        success = manager.add_song_to_playlist(
            "testuser", "Nonexistent", "Test Song", "/path.mp3", "user"
        )
        assert success is False

    def test_remove_song_by_index(self, manager):
        """Test removing a song by index."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 2", "/p2.mp3", "u2")
        
        success = manager.remove_song_from_playlist("testuser", "My Playlist", "1")
        assert success is True
        songs = manager.get_playlist_songs("testuser", "My Playlist")
        assert len(songs) == 1
        assert songs[0].query == "Song 2"

    def test_remove_song_by_name(self, manager):
        """Test removing a song by name."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Test Song", "/p.mp3", "u")
        
        success = manager.remove_song_from_playlist("testuser", "My Playlist", "Test Song")
        assert success is True
        songs = manager.get_playlist_songs("testuser", "My Playlist")
        assert len(songs) == 0

    def test_remove_song_invalid_index(self, manager):
        """Test removing song with invalid index."""
        manager.create_playlist("testuser", "My Playlist")
        success = manager.remove_song_from_playlist("testuser", "My Playlist", "999")
        assert success is False

    def test_swap_songs(self, manager):
        """Test swapping two songs in a playlist."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 2", "/p2.mp3", "u2")
        
        success = manager.swap_songs_in_playlist("testuser", "My Playlist", "1", "2")
        assert success is True
        songs = manager.get_playlist_songs("testuser", "My Playlist")
        assert songs[0].query == "Song 2"
        assert songs[1].query == "Song 1"

    def test_swap_songs_invalid_indices(self, manager):
        """Test swapping with invalid indices."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        
        success = manager.swap_songs_in_playlist("testuser", "My Playlist", "1", "2")
        assert success is False

    def test_clear_playlist(self, manager):
        """Test clearing a playlist."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 2", "/p2.mp3", "u2")
        
        success = manager.clear_playlist("testuser", "My Playlist")
        assert success is True
        songs = manager.get_playlist_songs("testuser", "My Playlist")
        assert len(songs) == 0

    def test_clear_nonexistent_playlist(self, manager):
        """Test clearing non-existent playlist."""
        success = manager.clear_playlist("testuser", "Nonexistent")
        assert success is False

    def test_get_playlist_songs(self, manager):
        """Test getting songs from a playlist."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 2", "/p2.mp3", "u2")
        
        songs = manager.get_playlist_songs("testuser", "My Playlist")
        assert len(songs) == 2

    def test_get_playlist_songs_nonexistent(self, manager):
        """Test getting songs from non-existent playlist."""
        songs = manager.get_playlist_songs("testuser", "Nonexistent")
        assert songs == []

    def test_pompa_songs(self, manager):
        """Test pumping random songs from playlist."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 2", "/p2.mp3", "u2")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 3", "/p3.mp3", "u3")
        
        songs = manager.pompa_songs("testuser", "My Playlist", n=2)
        assert len(songs) == 2

    def test_pompa_songs_empty_playlist(self, manager):
        """Test pumping from empty playlist."""
        manager.create_playlist("testuser", "My Playlist")
        songs = manager.pompa_songs("testuser", "My Playlist", n=5)
        assert songs == []

    def test_pompa_songs_nonexistent_playlist(self, manager):
        """Test pumping from non-existent playlist."""
        songs = manager.pompa_songs("testuser", "Nonexistent", n=5)
        assert songs == []

    def test_pompa_songs_excludes_recently_pumped(self, manager):
        """Test pompa excludes recently pumped queries."""
        manager.create_playlist("testuser", "My Playlist")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 1", "/p1.mp3", "u1")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 2", "/p2.mp3", "u2")
        manager.add_song_to_playlist("testuser", "My Playlist", "Song 3", "/p3.mp3", "u3")
        
        # First pump
        songs1 = manager.pompa_songs("testuser", "My Playlist", n=3)
        assert len(songs1) == 3
        
        # Second pump should reset since all songs used
        songs2 = manager.pompa_songs("testuser", "My Playlist", n=3)
        assert len(songs2) == 3

    def test_persist_playlist_to_disk(self, manager):
        """Test playlist is saved to disk."""
        manager.create_playlist("testuser", "My Playlist")
        user_file = manager._get_user_file("testuser")
        assert user_file.exists()
        
        with open(user_file) as f:
            data = json.load(f)
        assert len(data) == 1
        assert "My Playlist" in data

    def test_load_playlist_from_disk(self, temp_dir):
        """Test loading playlists from disk."""
        data_dir = os.path.join(temp_dir, "playlists")
        manager = PlaylistManager(data_dir=data_dir)
        
        # Create a playlist file manually
        user_file = manager._get_user_file("testuser")
        test_data = {
            "playlist1": {
                "id": "123",
                "name": "Test Playlist",
                "songs": [],
                "created_at": "2025-01-01",
                "last_modified": "2025-01-01",
                "recently_pumped_queries": []
            }
        }
        with open(user_file, "w") as f:
            json.dump(test_data, f)
        
        playlists = manager.get_user_playlists("testuser")
        assert len(playlists) == 1
        assert playlists[0].name == "Test Playlist"

    def test_load_invalid_json(self, temp_dir):
        """Test loading invalid JSON file."""
        data_dir = os.path.join(temp_dir, "playlists")
        manager = PlaylistManager(data_dir=data_dir)
        
        user_file = manager._get_user_file("testuser")
        with open(user_file, "w") as f:
            f.write("invalid json")
        
        playlists = manager.get_user_playlists("testuser")
        assert playlists == []
