"""Tests for trusted channels (YouTube channel whitelist) feature."""

import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open

from main.admin_handler import AdminHandler


class TestAdminHandlerTrustedChannels:
    """Tests for AdminHandler trusted channel methods."""

    @pytest.fixture
    def handler(self, temp_dir):
        """Create an AdminHandler instance."""
        return AdminHandler(data_dir=temp_dir)

    def test_init_empty_trusted_channels(self, handler):
        """Test init creates empty trusted channels dict."""
        assert handler.get_trusted_channels() == {}

    def test_add_trusted_channel(self, handler):
        """Test adding a channel to trusted list."""
        result = handler.add_trusted_channel("UC123", "Music Channel")
        assert result is True
        assert handler.is_trusted_channel("UC123") is True
        channels = handler.get_trusted_channels()
        assert channels["UC123"] == "Music Channel"

    def test_add_trusted_channel_duplicate(self, handler):
        """Test adding duplicate channel returns False."""
        handler.add_trusted_channel("UC123", "Music Channel")
        result = handler.add_trusted_channel("UC123", "Other Name")
        assert result is False
        # Name should not have changed
        assert handler.get_trusted_channels()["UC123"] == "Music Channel"

    def test_remove_trusted_channel(self, handler):
        """Test removing a channel from trusted list."""
        handler.add_trusted_channel("UC123", "Music Channel")
        result = handler.remove_trusted_channel("UC123")
        assert result is True
        assert handler.is_trusted_channel("UC123") is False
        assert len(handler.get_trusted_channels()) == 0

    def test_remove_trusted_channel_not_found(self, handler):
        """Test removing non-existent channel returns False."""
        result = handler.remove_trusted_channel("UC999")
        assert result is False

    def test_is_trusted_channel_case_sensitive(self, handler):
        """Test channel_id check is case-sensitive."""
        handler.add_trusted_channel("UC123", "Music Channel")
        assert handler.is_trusted_channel("UC123") is True
        assert handler.is_trusted_channel("uc123") is False

    def test_get_trusted_channels_returns_copy(self, handler):
        """Test get_trusted_channels returns a copy."""
        handler.add_trusted_channel("UC123", "Music Channel")
        channels = handler.get_trusted_channels()
        channels["UC456"] = "Hacked"
        assert "UC456" not in handler.get_trusted_channels()

    def test_persist_trusted_channels(self, temp_dir):
        """Test trusted channels are persisted to disk."""
        handler = AdminHandler(data_dir=temp_dir)
        handler.add_trusted_channel("UC123", "Music Channel")

        tc_file = os.path.join(temp_dir, "trusted_channels.json")
        assert os.path.exists(tc_file)

        with open(tc_file) as f:
            data = json.load(f)
        assert data["channels"]["UC123"] == "Music Channel"

    def test_load_trusted_channels_from_disk(self, temp_dir):
        """Test loading trusted channels from disk."""
        tc_file = os.path.join(temp_dir, "trusted_channels.json")
        with open(tc_file, "w") as f:
            json.dump({"channels": {"UC123": "Music Channel", "UC456": "Beats"}}, f)

        handler = AdminHandler(data_dir=temp_dir)
        channels = handler.get_trusted_channels()
        assert len(channels) == 2
        assert channels["UC123"] == "Music Channel"
        assert channels["UC456"] == "Beats"

    def test_load_invalid_trusted_channels_json(self, temp_dir):
        """Test loading invalid JSON gracefully."""
        tc_file = os.path.join(temp_dir, "trusted_channels.json")
        with open(tc_file, "w") as f:
            f.write("invalid json")

        handler = AdminHandler(data_dir=temp_dir)
        assert handler.get_trusted_channels() == {}

    def test_multiple_channels(self, handler):
        """Test adding and listing multiple channels."""
        handler.add_trusted_channel("UC1", "Channel 1")
        handler.add_trusted_channel("UC2", "Channel 2")
        handler.add_trusted_channel("UC3", "Channel 3")

        channels = handler.get_trusted_channels()
        assert len(channels) == 3

        handler.remove_trusted_channel("UC2")
        channels = handler.get_trusted_channels()
        assert len(channels) == 2
        assert "UC2" not in channels


class TestMusicDownloaderChannelWhitelist:
    """Tests for MusicDownloader channel whitelist validation."""

    @pytest.fixture
    def downloader_with_handler(self, temp_dir):
        """Create a MusicDownloader with an AdminHandler."""
        from main.admin_handler import AdminHandler
        admin = AdminHandler(data_dir=temp_dir)
        with patch("main.music_downloader.os.makedirs"):
            with patch("main.music_downloader.yt_dlp.YoutubeDL"):
                from main.music_downloader import MusicDownloader
                dl = MusicDownloader(admin_handler=admin)
                return dl, admin

    def test_validate_song_ignores_whitelist_when_disabled(self, downloader_with_handler):
        """Test that channel whitelist is ignored when CHANNEL_WHITELIST_ENABLED=False."""
        dl, admin = downloader_with_handler
        info = {
            "duration": 240,
            "categories": ["Music"],
            "channel_id": "UCunknown",
            "channel": "Unknown Channel",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", False):
            is_valid, error = dl._validate_song(info)
            assert is_valid is True
            assert error == ""

    def test_validate_song_rejects_untrusted_channel(self, downloader_with_handler):
        """Test that untrusted channel is rejected when whitelist is enabled."""
        dl, admin = downloader_with_handler
        info = {
            "duration": 240,
            "categories": ["Music"],
            "channel_id": "UCunknown",
            "channel": "Unknown Channel",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            assert is_valid is False
            assert "non è nella whitelist" in error

    def test_validate_song_accepts_trusted_channel(self, downloader_with_handler):
        """Test that trusted channel passes validation when whitelist is enabled."""
        dl, admin = downloader_with_handler
        admin.add_trusted_channel("UCtrusted", "Trusted Channel")
        info = {
            "duration": 240,
            "categories": ["Music"],
            "channel_id": "UCtrusted",
            "channel": "Trusted Channel",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            assert is_valid is True
            assert error == ""

    def test_validate_song_no_channel_id(self, downloader_with_handler):
        """Test validation when channel_id is missing."""
        dl, admin = downloader_with_handler
        info = {
            "duration": 240,
            "categories": ["Music"],
            "channel": "Some Channel",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            assert is_valid is False
            assert "non ci sono ID disponibili" in error

    def test_validate_song_uses_uploader_id_fallback(self, downloader_with_handler):
        """Test that uploader_id is used as fallback for channel_id."""
        dl, admin = downloader_with_handler
        admin.add_trusted_channel("UCfallback", "Fallback Channel")
        info = {
            "duration": 240,
            "categories": ["Music"],
            "uploader_id": "UCfallback",
            "channel": "Fallback Channel",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            assert is_valid is True

    def test_validate_song_no_admin_handler(self):
        """Test that missing admin_handler skips whitelist check."""
        with patch("main.music_downloader.os.makedirs"):
            with patch("main.music_downloader.yt_dlp.YoutubeDL"):
                from main.music_downloader import MusicDownloader
                dl = MusicDownloader(admin_handler=None)

        info = {
            "duration": 240,
            "categories": ["Music"],
            "channel_id": "UCunknown",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            # Should pass because admin_handler is None (no whitelist enforcement)
            assert is_valid is True

    def test_validate_song_duration_still_checked_before_whitelist(self, downloader_with_handler):
        """Test that duration check runs before channel whitelist."""
        dl, admin = downloader_with_handler
        info = {
            "duration": 2000,
            "categories": ["Music"],
            "channel_id": "UCunknown",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            assert is_valid is False
            # Duration check comes first, so error should be about duration
            assert "too long" in error or "Song too long" in error

    def test_validate_song_category_still_checked_before_whitelist(self, downloader_with_handler):
        """Test that category check runs before channel whitelist."""
        dl, admin = downloader_with_handler
        info = {
            "duration": 240,
            "categories": ["Gaming"],
            "channel_id": "UCunknown",
        }
        with patch("main.config.CHANNEL_WHITELIST_ENABLED", True):
            is_valid, error = dl._validate_song(info)
            assert is_valid is False
            # Category check comes before whitelist, so error should be about category
            assert "category" in error.lower()
