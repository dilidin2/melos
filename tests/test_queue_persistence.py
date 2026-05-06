"""Tests for queue_persistence module."""

import pytest
import json
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from main.queue_persistence import QueuePersistence, SongRequestPersistence


class TestQueuePersistence:
    """Tests for QueuePersistence class."""

    @pytest.fixture
    def persistence(self, temp_dir):
        """Create a QueuePersistence instance."""
        return QueuePersistence(queue_file=os.path.join(temp_dir, "queue.json"))

    def test_init_creates_parent_dir(self, temp_dir):
        """Test init creates parent directory."""
        persistence = QueuePersistence(queue_file=os.path.join(temp_dir, "sub", "queue.json"))
        assert os.path.exists(os.path.join(temp_dir, "sub"))

    def test_load_no_file(self, persistence):
        """Test loading when no file exists."""
        result = asyncio.run(persistence.load())
        assert result == []

    @pytest.mark.asyncio
    async def test_load_existing_file(self, persistence):
        """Test loading existing file."""
        queue_file = Path(persistence.queue_file)
        data = {
            "version": 1,
            "last_updated": "2025-01-01T00:00:00",
            "songs": [
                {"query": "Song 1", "username": "user1", "channel_id": "ch1", "request_id": 1},
                {"query": "Song 2", "username": "user2", "channel_id": "ch1", "request_id": 2},
            ]
        }
        queue_file.write_text(json.dumps(data))
        
        result = await persistence.load()
        assert len(result) == 2
        assert result[0]["query"] == "Song 1"

    @pytest.mark.asyncio
    async def test_load_invalid_json(self, persistence):
        """Test loading invalid JSON."""
        queue_file = Path(persistence.queue_file)
        queue_file.write_text("invalid json")
        
        result = await persistence.load()
        assert result == []

    @pytest.mark.asyncio
    async def test_save(self, persistence):
        """Test saving queue."""
        songs = [
            {"query": "Song 1", "username": "user1", "channel_id": "ch1"},
        ]
        result = await persistence.save(songs)
        assert result is True
        
        # Verify file exists and has correct content
        queue_file = Path(persistence.queue_file)
        data = json.loads(queue_file.read_text())
        assert data["songs"] == songs
        assert "version" in data
        assert "last_updated" in data

    @pytest.mark.asyncio
    async def test_save_creates_temp_file(self, persistence):
        """Test save creates temp file first."""
        songs = [{"query": "Test", "username": "user", "channel_id": "ch"}]
        await persistence.save(songs)
        
        queue_file = Path(persistence.queue_file)
        assert queue_file.exists()
        # Temp file should be gone after atomic rename
        assert not queue_file.with_suffix(".tmp").exists()

    @pytest.mark.asyncio
    async def test_backup(self, persistence):
        """Test creating backup."""
        queue_file = Path(persistence.queue_file)
        queue_file.write_text('{"songs": []}')
        
        backup_path = await persistence.backup()
        assert backup_path is not None
        assert backup_path.suffix == ".bak"
        assert backup_path.exists()

    @pytest.mark.asyncio
    async def test_backup_no_file(self, persistence):
        """Test backup when no file exists."""
        backup_path = await persistence.backup()
        assert backup_path is None


class TestSongRequestPersistence:
    """Tests for SongRequestPersistence class."""

    @pytest.fixture
    def song_persistence(self, temp_dir):
        """Create a SongRequestPersistence instance."""
        return SongRequestPersistence(downloads_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_validate_song_exists(self, song_persistence):
        """Test validating existing song file."""
        test_file = os.path.join(song_persistence.downloads_dir, "testuser - Test Song.mp3")
        Path(test_file).touch()
        
        result = await song_persistence.validate_song_exists("Test Song", "testuser")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_song_not_exists(self, song_persistence):
        """Test validating non-existing song file."""
        result = await song_persistence.validate_song_exists("Nonexistent", "testuser")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_song_different_extensions(self, song_persistence):
        """Test validating different file extensions."""
        test_file = os.path.join(song_persistence.downloads_dir, "testuser - Test Song.m4a")
        Path(test_file).touch()
        
        result = await song_persistence.validate_song_exists("Test Song", "testuser")
        assert result is True
