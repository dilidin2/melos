"""Configuration for Twitch Song Request Bot.

Priority order:
  1. config.json (primary configuration file)
  2. Hardcoded default (fallback)

Environment variables are NOT loaded via dotenv — config.json is the source of truth.
"""

import json
import os
from pathlib import Path

# ── Load config.json ──

_CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"
_config: dict = {}

if _CONFIG_FILE.exists():
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            _config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[config] Warning: could not load config.json: {e}")


def _get(path: str, default=None):
    """Get a nested value from config.json by dot-separated path."""
    value = _config
    for key in path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        if value is None:
            return default
    return value


# ====================
# TWITCH CONFIGURATION
# ====================

TWITCH_CLIENT_ID: str = "7uyqomgf325fb3j3bztn9o1p51m85t"

TARGET_CHANNEL: str = _get("twitch.target_channel", "")

ADMIN_USERS: list[str] = _get("twitch.admin_users", []) or []

# ====================
# COMMAND CONFIGURATION
# ====================

CHAT_COMMAND_PREFIX: str = "!"
SONG_REQUEST_COMMAND: str = "sr"

# ====================
# SONG CONFIGURATION
# ====================

MAX_DURATION_SECONDS: int = int(_get("song.max_duration_seconds", 900))

AUDIO_QUALITY: int = int(_get("song.audio_quality", 192))

AUDIO_FORMAT: str = _get("song.audio_format", "mp3")

# ====================
# DOWNLOAD CONFIGURATION
# ====================

DOWNLOAD_DIR: str = _get("download.download_dir", "./downloads")

MAX_WORKERS: int = 5
DOWNLOAD_TIMEOUT: int = 60

YOUTUBE_CATEGORY: str = _get("download.youtube_category", "Music")

CHANNEL_WHITELIST_ENABLED: bool = bool(_get("download.channel_whitelist_enabled", False))

TRUSTED_CHANNELS_FILE: str = os.path.join("data", "trusted_channels.json")

# ====================
# LOGGING CONFIGURATION
# ====================

LOG_LEVEL: str = _get("logging.level", "INFO")

LOG_FILE: str = _get("logging.file", "twitch_sr.log")

# ====================
# QUEUE CONFIGURATION
# ====================

MAX_QUEUE_SIZE: int = int(_get("queue.max_size", 50))

# ====================
# VOTE TO SKIP CONFIGURATION
# ====================

VOTE_SKIP_COMMAND: str = "vote"

VOTE_REQUIRED_COUNT: int = int(_get("vote.required_count", 3))

# ====================
# PLAYLIST CONFIGURATION
# ====================

PLAYLIST_CREATE_COMMAND: str = "create"
PLAYLIST_VIEW_COMMAND: str = "playlist"
PLAYLIST_ADD_COMMAND: str = "add"
PLAYLIST_REMOVE_COMMAND: str = "remove"
PLAYLIST_MOVE_COMMAND: str = "move"
PLAYLIST_CLEAR_COMMAND: str = "clear"
PLAYLIST_POMPA_COMMAND: str = "pump"

MAX_POMPA_SONGS: int = int(_get("playlist.max_pompa_songs", 5))

PUMP_COOLDOWN_MINUTES: int = int(_get("playlist.pompa_cooldown_minutes", 15))

# ====================
# ADMIN COMMANDS
# ====================

ADMIN_BLACKLIST_COMMAND: str = "blacklist"
ADMIN_UNBLACKLIST_COMMAND: str = "unblacklist"
ADMIN_BLACKLIST_LIST_COMMAND: str = "blacklist_list"
ADMIN_SKIP_COMMAND: str = "skip"
ADMIN_TRUST_CHANNEL_COMMAND: str = "trust_channel"
ADMIN_UNTRUST_CHANNEL_COMMAND: str = "untrust_channel"
ADMIN_TRUSTED_CHANNELS_LIST_COMMAND: str = "trusted_channels"
ADMIN_REMOVE_QUEUE_COMMAND: str = "remove_queue"
ADMIN_CLEAR_QUEUE_COMMAND: str = "clear_queue"
ADMIN_DELETE_COMMAND: str = "delete"

# ====================
# ANALYTICS COMMANDS
# ====================

ANALYTICS_STATS_COMMAND: str = "stats"
ANALYTICS_TOP_SONGS_COMMAND: str = "top_songs"
ANALYTICS_TOP_USERS_COMMAND: str = "top_users"
ANALYTICS_STORIA_COMMAND: str = "history"

# ====================
# MUSIC CONTROL COMMANDS
# ====================

MUSIC_VOLUME_COMMAND: str = "volume"
MUSIC_PAUSE_COMMAND: str = "pause"
MUSIC_RESUME_COMMAND: str = "resume"
MUSIC_REPEAT_COMMAND: str = "repeat"
MUSIC_REPEAT_OFF_COMMAND: str = "repeat_off"
MUSIC_NEXT_COMMAND: str = "next"
MUSIC_QUEUE_INFO_COMMAND: str = "queue_info"
MUSIC_DURATION_COMMAND: str = "duration"
MUSIC_WHEN_COMMAND: str = "when"
MUSIC_RANDOM_COMMAND: str = "random"
MUSIC_OPS_COMMAND: str = "ops"

# ====================
# UTILITY COMMANDS
# ====================

UTILITY_HELP_COMMAND: str = "help"
UTILITY_VERSION_COMMAND: str = "version"
UTILITY_UPTIME_COMMAND: str = "uptime"

# ====================
# RANDOM SONG COOLDOWN
# ====================

COOLDOWN_FILE: str = os.path.join("data", "random_cooldown.json")
RANDOM_COOLDOWN_SECONDS: int = 3600
RANDOM_MAX_ATTEMPTS: int = 10

# ====================
# DASHBOARD CONFIGURATION
# ====================

DASHBOARD_ENABLED: bool = bool(_get("dashboard.enabled", True))

DASHBOARD_PORT: int = int(_get("dashboard.port", 8080))

DASHBOARD_HOST: str = _get("dashboard.host", "0.0.0.0")
