"""Tests for services module."""

import pytest
from unittest.mock import MagicMock

from main.services import CommandServices


class TestCommandServices:
    """Tests for CommandServices class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.audio_player = MagicMock()
        bot.request_queue = MagicMock()
        return bot

    @pytest.fixture
    def mock_services(self):
        """Create mock service instances."""
        playlist_manager = MagicMock()
        admin_handler = MagicMock()
        analytics = MagicMock()
        music_downloader = MagicMock()
        playlist_commands = MagicMock()
        admin_commands = MagicMock()
        analytics_commands = MagicMock()
        music_commands = MagicMock()
        utility_commands = MagicMock()
        return {
            "bot": MagicMock(),
            "playlist_manager": playlist_manager,
            "admin_handler": admin_handler,
            "analytics": analytics,
            "music_downloader": music_downloader,
            "playlist_commands": playlist_commands,
            "admin_commands": admin_commands,
            "analytics_commands": analytics_commands,
            "music_commands": music_commands,
            "utility_commands": utility_commands,
        }

    def test_default_values(self):
        """Test default values for all services."""
        services = CommandServices()
        assert services.playlist_commands is None
        assert services.admin_commands is None
        assert services.analytics_commands is None
        assert services.music_commands is None
        assert services.utility_commands is None
        assert services.playlist_manager is None
        assert services.admin_handler is None
        assert services.analytics is None
        assert services.music_downloader is None
        assert services.audio_player is None
        assert services.request_queue is None
        assert services.bot is None

    def test_build_services(self, mock_services):
        """Test building services container."""
        services = CommandServices.build(**mock_services)
        assert services.playlist_commands == mock_services["playlist_commands"]
        assert services.admin_commands == mock_services["admin_commands"]
        assert services.analytics_commands == mock_services["analytics_commands"]
        assert services.music_commands == mock_services["music_commands"]
        assert services.utility_commands == mock_services["utility_commands"]
        assert services.playlist_manager == mock_services["playlist_manager"]
        assert services.admin_handler == mock_services["admin_handler"]
        assert services.analytics == mock_services["analytics"]
        assert services.music_downloader == mock_services["music_downloader"]
        assert services.bot == mock_services["bot"]

    def test_build_sets_audio_player_from_bot(self, mock_services):
        """Test build sets audio_player from bot."""
        bot = MagicMock()
        bot.audio_player = MagicMock()
        mock_services["bot"] = bot
        
        services = CommandServices.build(**mock_services)
        assert services.audio_player == bot.audio_player

    def test_build_sets_request_queue_from_bot(self, mock_services):
        """Test build sets request_queue from bot."""
        bot = MagicMock()
        bot.request_queue = MagicMock()
        mock_services["bot"] = bot
        
        services = CommandServices.build(**mock_services)
        assert services.request