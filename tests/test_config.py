"""Tests for config module."""

import pytest
from unittest.mock import patch

from main.config import (
    TWITCH_CLIENT_ID,
    TARGET_CHANNEL,
    CHAT_COMMAND_PREFIX,
    SONG_REQUEST_COMMAND,
    MAX_DURATION_SECONDS,
    AUDIO_QUALITY,
    AUDIO_FORMAT,
    DOWNLOAD_TIMEOUT,
    MAX_WORKERS,
    YOUTUBE_CATEGORY,
    LOG_LEVEL,
    LOG_FILE,
    MAX_QUEUE_SIZE,
    DOWNLOAD_DIR,
    ADMIN_USERS,
    BLACKLIST_USERS,
    PLAYLIST_CREATE_COMMAND,
    PLAYLIST_VIEW_COMMAND,
    PLAYLIST_ADD_COMMAND,
    PLAYLIST_REMOVE_COMMAND,
    PLAYLIST_MOVE_COMMAND,
    PLAYLIST_CLEAR_COMMAND,
    PLAYLIST_LIST_COMMAND,
    PLAYLIST_POMPA_COMMAND,
    MAX_POMPA_SONGS,
    ADMIN_BLACKLIST_COMMAND,
    ADMIN_UNBLACKLIST_COMMAND,
    ADMIN_BLACKLIST_LIST_COMMAND,
    ADMIN_SKIP_COMMAND,
    ADMIN_REMOVE_QUEUE_COMMAND,
    ADMIN_CLEAR_QUEUE_COMMAND,
    ANALYTICS_STATS_COMMAND,
    ANALYTICS_TOP_SONGS_COMMAND,
    ANALYTICS_TOP_USERS_COMMAND,
    MUSIC_VOLUME_COMMAND,
    MUSIC_PAUSE_COMMAND,
    MUSIC_RESUME_COMMAND,
    MUSIC_REPEAT_COMMAND,
    MUSIC_REPEAT_OFF_COMMAND,
    MUSIC_REPEAT_INFINITE_COMMAND,
    MUSIC_NEXT_COMMAND,
    MUSIC_QUEUE_INFO_COMMAND,
    MUSIC_DURATION_COMMAND,
    MUSIC_DURATA_COMMAND,
    MUSIC_WHEN_COMMAND,
    UTILITY_HELP_COMMAND,
    UTILITY_VERSION_COMMAND,
    UTILITY_UPTIME_COMMAND,
)


class TestConstants:
    """Tests for configuration constants."""

    # Twitch constants
    def test_twitch_client_id(self):
        """Test TWITCH_CLIENT_ID is a string."""
        assert isinstance(TWITCH_CLIENT_ID, str)

    def test_target_channel(self):
        """Test TARGET_CHANNEL is a string."""
        assert isinstance(TARGET_CHANNEL, str)

    # Command constants
    def test_chat_command_prefix(self):
        """Test CHAT_COMMAND_PREFIX is '!'. """
        assert CHAT_COMMAND_PREFIX == "!"

    def test_song_request_command(self):
        """Test SONG_REQUEST_COMMAND is 'sr'."""
        assert SONG_REQUEST_COMMAND == "sr"

    # Song constants
    def test_max_duration(self):
        """Test MAX_DURATION_SECONDS is 900."""
        assert MAX_DURATION_SECONDS == 900

    def test_audio_quality(self):
        """Test AUDIO_QUALITY is 192."""
        assert AUDIO_QUALITY == 192

    def test_audio_format(self):
        """Test AUDIO_FORMAT is 'mp3'."""
        assert AUDIO_FORMAT == "mp3"

    # Download constants
    def test_download_timeout(self):
        """Test DOWNLOAD_TIMEOUT is 60."""
        assert DOWNLOAD_TIMEOUT == 60

    def test_max_workers(self):
        """Test MAX_WORKERS is 5."""
        assert MAX_WORKERS == 5

    def test_youtube_category(self):
        """Test YOUTUBE_CATEGORY is 'Music'."""
        assert YOUTUBE_CATEGORY == "Music"

    # Logging constants
    def test_log_level(self):
        """Test LOG_LEVEL is 'INFO'."""
        assert LOG_LEVEL == "INFO"

    def test_log_file(self):
        """Test LOG_FILE is 'twitch_sr.log'."""
        assert LOG_FILE == "twitch_sr.log"

    # Queue constants
    def test_max_queue_size(self):
        """Test MAX_QUEUE_SIZE is 50."""
        assert MAX_QUEUE_SIZE == 50

    # Admin constants
    def test_admin_users_is_list(self):
        """Test ADMIN_USERS is a list."""
        assert isinstance(ADMIN_USERS, list)

    def test_blacklist_users_is_list(self):
        """Test BLACKLIST_USERS is a list."""
        assert isinstance(BLACKLIST_USERS, list)

    # Playlist constants
    def test_playlist_create_command(self):
        """Test PLAYLIST_CREATE_COMMAND is 'crea'."""
        assert PLAYLIST_CREATE_COMMAND == "crea"

    def test_playlist_view_command(self):
        """Test PLAYLIST_VIEW_COMMAND is 'playlist'."""
        assert PLAYLIST_VIEW_COMMAND == "playlist"

    def test_playlist_add_command(self):
        """Test PLAYLIST_ADD_COMMAND is 'aggiungi'."""
        assert PLAYLIST_ADD_COMMAND == "aggiungi"

    def test_playlist_remove_command(self):
        """Test PLAYLIST_REMOVE_COMMAND is 'rimuovi'."""
        assert PLAYLIST_REMOVE_COMMAND == "rimuovi"

    def test_playlist_move_command(self):
        """Test PLAYLIST_MOVE_COMMAND is 'sposta'."""
        assert PLAYLIST_MOVE_COMMAND == "sposta"

    def test_playlist_clear_command(self):
        """Test PLAYLIST_CLEAR_COMMAND is 'svuota'."""
        assert PLAYLIST_CLEAR_COMMAND == "svuota"

    def test_playlist_list_command(self):
        """Test PLAYLIST_LIST_COMMAND is 'lista_playlist'."""
        assert PLAYLIST_LIST_COMMAND == "lista_playlist"

    def test_playlist_pompa_command(self):
        """Test PLAYLIST_POMPA_COMMAND is 'pompa'."""
        assert PLAYLIST_POMPA_COMMAND == "pompa"

    def test_max_pompa_songs(self):
        """Test MAX_POMPA_SONGS is 5."""
        assert MAX_POMPA_SONGS == 5

    # Admin command constants
    def test_admin_blacklist_command(self):
        """Test ADMIN_BLACKLIST_COMMAND is 'blacklist'."""
        assert ADMIN_BLACKLIST_COMMAND == "blacklist"

    def test_admin_unblacklist_command(self):
        """Test ADMIN_UNBLACKLIST_COMMAND is 'unblacklist'."""
        assert ADMIN_UNBLACKLIST_COMMAND == "unblacklist"

    def test_admin_blacklist_list_command(self):
        """Test ADMIN_BLACKLIST_LIST_COMMAND is 'blacklist_list'."""
        assert ADMIN_BLACKLIST_LIST_COMMAND == "blacklist_list"

    def test_admin_skip_command(self):
        """Test ADMIN_SKIP_COMMAND is 'skippa'."""
        assert ADMIN_SKIP_COMMAND == "skippa"

    def test_admin_remove_queue_command(self):
        """Test ADMIN_REMOVE_QUEUE_COMMAND is 'rimuovi_coda'."""
        assert ADMIN_REMOVE_QUEUE_COMMAND == "rimuovi_coda"

    def test_admin_clear_queue_command(self):
        """Test ADMIN_CLEAR_QUEUE_COMMAND is 'clear_queue'."""
        assert ADMIN_CLEAR_QUEUE_COMMAND == "clear_queue"

    # Analytics command constants
    def test_analytics_stats_command(self):
        """Test ANALYTICS_STATS_COMMAND is 'stats'."""
        assert ANALYTICS_STATS_COMMAND == "stats"

    def test_analytics_top_songs_command(self):
        """Test ANALYTICS_TOP_SONGS_COMMAND is 'top_canzoni'."""
        assert ANALYTICS_TOP_SONGS_COMMAND == "top_canzoni"

    def test_analytics_top_users_command(self):
        """Test ANALYTICS_TOP_USERS_COMMAND is 'top_user'."""
        assert ANALYTICS_TOP_USERS_COMMAND == "top_user"

    # Music command constants
    def test_music_volume_command(self):
        """Test MUSIC_VOLUME_COMMAND is 'volume'."""
        assert MUSIC_VOLUME_COMMAND == "volume"

    def test_music_pause_command(self):
        """Test MUSIC_PAUSE_COMMAND is 'pausa'."""
        assert MUSIC_PAUSE_COMMAND == "pausa"

    def test_music_resume_command(self):
        """Test MUSIC_RESUME_COMMAND is 'riprendi'."""
        assert MUSIC_RESUME_COMMAND == "riprendi"

    def test_music_repeat_command(self):
        """Test MUSIC_REPEAT_COMMAND is 'repeat'."""
        assert MUSIC_REPEAT_COMMAND == "repeat"

    def test_music_repeat_off_command(self):
        """Test MUSIC_REPEAT_OFF_COMMAND is 'repeat_off'."""
        assert MUSIC_REPEAT_OFF_COMMAND == "repeat_off"

    def test_music_repeat_infinite_command(self):
        """Test MUSIC_REPEAT_INFINITE_COMMAND is 'ripeti'."""
        assert MUSIC_REPEAT_INFINITE_COMMAND == "ripeti"

    def test_music_next_command(self):
        """Test MUSIC_NEXT_COMMAND is 'next'."""
        assert MUSIC_NEXT_COMMAND == "next"

    def test_music_queue_info_command(self):
        """Test MUSIC_QUEUE_INFO_COMMAND is 'queue_info'."""
        assert MUSIC_QUEUE_INFO_COMMAND == "queue_info"

    def test_music_duration_command(self):
        """Test MUSIC_DURATION_COMMAND is 'duration'."""
        assert MUSIC_DURATION_COMMAND == "duration"

    def test_music_durata_command(self):
        """Test MUSIC_DURATA_COMMAND is 'durata'."""
        assert MUSIC_DURATA_COMMAND == "durata"

    def test_music_when_command(self):
        """Test MUSIC_WHEN_COMMAND is 'quando'."""
        assert MUSIC_WHEN_COMMAND == "quando"

    # Utility command constants
    def test_utility_help_command(self):
        """Test UTILITY_HELP_COMMAND is 'help'."""
        assert UTILITY_HELP_COMMAND == "help"

    def test_utility_version_command(self):
        """Test UTILITY_VERSION_COMMAND is 'version'."""
        assert UTILITY_VERSION_COMMAND == "version"

    def test_utility_uptime_command(self):
        """Test UTILITY_UPTIME_COMMAND is 'uptime'."""
        assert UTILITY_UPTIME_COMMAND == "uptime"
