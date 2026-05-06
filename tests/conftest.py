"""Pytest configuration and fixtures for Twitch-SR tests."""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock

# Ensure main modules can be imported
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_request_queue():
    """Create a mock RequestQueue."""
    queue = MagicMock()
    queue.get_next = AsyncMock(return_value=None)
    queue.put = AsyncMock(return_value=True)
    queue.get_all = MagicMock(return_value=[])
    queue.get_by_index = MagicMock(return_value=None)
    queue.remove_by_index = MagicMock(return_value=True)
    queue.clear = MagicMock()
    queue.get_size = MagicMock(return_value=0)
    return queue


@pytest.fixture
def mock_audio_player():
    """Create a mock AudioPlayer."""
    player = MagicMock()
    player.is_playing = MagicMock(return_value=False)
    player.is_paused = MagicMock(return_value=False)
    player.play = MagicMock(return_value=True)
    player.pause = MagicMock()
    player.resume = MagicMock()
    player.stop = MagicMock()
    return player


@pytest.fixture
def mock_music_downloader():
    """Create a mock MusicDownloader."""
    downloader = MagicMock()
    downloader.get_video_info = MagicMock(return_value={
        "title": "Test Song",
        "duration": 240,
        "categories": ["Music"],
    })
    downloader.get_song_info = MagicMock(return_value={
        "title": "Test Song",
        "duration": 240,
    })
    downloader.download = MagicMock(return_value="/path/to/song.mp3")
    downloader.get_random_downloaded_file = MagicMock(return_value=None)
    return downloader


@pytest.fixture
def mock_playlist_manager():
    """Create a mock PlaylistManager."""
    manager = MagicMock()
    manager.create_playlist = MagicMock(return_value=MagicMock(id="123", nome="Test"))
    manager.get_user_playlists = MagicMock(return_value=[])
    manager.get_playlist = MagicMock(return_value=None)
    manager.get_playlist_by_name = MagicMock(return_value=None)
    manager.add_song_to_playlist = MagicMock(return_value=True)
    manager.remove_song_from_playlist = MagicMock(return_value=True)
    manager.swap_songs_in_playlist = MagicMock(return_value=True)
    manager.clear_playlist = MagicMock(return_value=True)
    manager.get_playlist_songs = MagicMock(return_value=[])
    manager.pompa_songs = MagicMock(return_value=[])
    return manager


@pytest.fixture
def mock_admin_handler():
    """Create a mock AdminHandler."""
    handler = MagicMock()
    handler.add_whitelist = MagicMock(return_value=True)
    handler.remove_whitelist = MagicMock(return_value=True)
    handler.add_blacklist = MagicMock(return_value=True)
    handler.remove_blacklist = MagicMock(return_value=True)
    handler.get_whitelist_list = MagicMock(return_value=[])
    handler.get_blacklist_list = MagicMock(return_value=[])
    handler.is_whitelisted = MagicMock(return_value=False)
    handler.is_blacklisted = MagicMock(return_value=False)
    return handler


@pytest.fixture
def mock_analytics():
    """Create a mock Analytics instance."""
    analytics = MagicMock()
    analytics.get_stats_today = MagicMock(return_value={
        "total_requests_today": 0,
        "unique_users_today": 0,
    })
    analytics.get_stats_week = MagicMock(return_value={
        "total_requests_week": 0,
        "period": "last_7_days",
    })
    analytics.get_stats_month = MagicMock(return_value={
        "total_requests_month": 0,
        "period": "last_30_days",
    })
    analytics.get_top_songs = MagicMock(return_value=[])
    analytics.get_top_users = MagicMock(return_value=[])
    analytics.export_stats = MagicMock(return_value="{}")
    return analytics


@pytest.fixture
def mock_twitch_handler():
    """Create a mock TwitchHandler."""
    handler = MagicMock()
    handler.send_message = AsyncMock(return_value=True)
    handler.is_connected = MagicMock(return_value=False)
    handler.connect = AsyncMock(return_value=False)
    handler.disconnect = AsyncMock(return_value=None)
    return handler


@pytest.fixture
def mock_command_services():
    """Create a mock CommandServices instance."""
    services = MagicMock()
    services.bot = MagicMock()
    services.bot.config = MagicMock()
    services.bot.config.volume = 50
    services.bot.config.version = "1.0.0"
    services.bot.config.retry_attempts = 3
    services.bot.config.retry_delay = 2
    services.bot.config.max_duration = 900
    services.bot.uptime_start = asyncio.get_event_loop().time()
    services.bot.audio_player = MagicMock()
    services.bot.request_queue = MagicMock()
    services.playlist_commands = MagicMock()
    services.admin_commands = MagicMock()
    services.analytics_commands = MagicMock()
    services.music_commands = MagicMock()
    services.utility_commands = MagicMock()
    services.playlist_manager = MagicMock()
    services.admin_handler = MagicMock()
    services.analytics = MagicMock()
    services.music_downloader = MagicMock()
    services.audio_player = MagicMock()
    services.request_queue = MagicMock()
    return services


def _make_patches(patch_dict):
    """Helper to create multiple patches."""
    patches = []
    for attr, value in patch_dict.items():
        patches.append(patch(f"main.config.{attr}", value))
    return patches


@pytest.fixture(autouse=True)
def mock_config():
    """Mock config module to use test values."""
    # Only patch attributes that actually exist in main.config
    config_mocks = {
        "TWITCH_CLIENT_ID": "test_client_id",
        "TWITCH_CLIENT_SECRET": "test_client_secret",
        "OAUTH_REDIRECT_URI": "http://localhost:17563",
        "TARGET_CHANNEL": "testchannel",
        "DOWNLOAD_DIR": "/tmp/test_downloads",
        "MAX_DURATION_SECONDS": 900,
        "AUDIO_QUALITY": 192,
        "AUDIO_FORMAT": "mp3",
        "DOWNLOAD_TIMEOUT": 60,
        "MAX_WORKERS": 5,
        "YOUTUBE_CATEGORY": "Music",
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "test.log",
        "MAX_QUEUE_SIZE": 50,
        "CHAT_COMMAND_PREFIX": "!",
        "SONG_REQUEST_COMMAND": "sr",
        "PLAYLIST_CREATE_COMMAND": "crea",
        "PLAYLIST_VIEW_COMMAND": "playlist",
        "PLAYLIST_ADD_COMMAND": "aggiungi",
        "PLAYLIST_REMOVE_COMMAND": "rimuovi",
        "PLAYLIST_MOVE_COMMAND": "sposta",
        "PLAYLIST_CLEAR_COMMAND": "svuota",
        "PLAYLIST_LIST_COMMAND": "lista_playlist",
        "PLAYLIST_POMPA_COMMAND": "pompa",
        "MAX_POMPA_SONGS": 5,
        "ADMIN_WHITELIST_COMMAND": "whitelist",
        "ADMIN_BLACKLIST_COMMAND": "blacklist",
        "ADMIN_UNBLACKLIST_COMMAND": "unblacklist",
        "ADMIN_WHITELIST_LIST_COMMAND": "whitelist_list",
        "ADMIN_BLACKLIST_LIST_COMMAND": "blacklist_list",
        "ADMIN_SKIP_COMMAND": "skippa",
        "ADMIN_REMOVE_QUEUE_COMMAND": "rimuovi_coda",
        "ADMIN_QUEUE_INFO_COMMAND": "coda_info",
        "ADMIN_CLEAR_QUEUE_COMMAND": "clear_queue",
        "ANALYTICS_STATS_COMMAND": "stats",
        "ANALYTICS_TOP_SONGS_COMMAND": "top_canzoni",
        "ANALYTICS_TOP_USERS_COMMAND": "top_user",
        "ANALYTICS_EXPORT_COMMAND": "export_stats",
        "MUSIC_VOLUME_COMMAND": "volume",
        "MUSIC_PAUSE_COMMAND": "pausa",
        "MUSIC_RESUME_COMMAND": "riprendi",
        "MUSIC_REPEAT_COMMAND": "repeat",
        "MUSIC_REPEAT_OFF_COMMAND": "repeat_off",
        "MUSIC_REPEAT_INFINITE_COMMAND": "ripeti",
        "MUSIC_REPEAT_STOP_COMMAND": "stop_ripeti",
        "MUSIC_NEXT_COMMAND": "next",
        "MUSIC_QUEUE_INFO_COMMAND": "queue_info",
        "MUSIC_DURATION_COMMAND": "duration",
        "MUSIC_DURATA_COMMAND": "durata",
        "MUSIC_WHEN_COMMAND": "quando",
        "UTILITY_HELP_COMMAND": "help",
        "UTILITY_VERSION_COMMAND": "version",
        "UTILITY_UPTIME_COMMAND": "uptime",
    }
    
    patches = _make_patches(config_mocks)
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()
