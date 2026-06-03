"""Configuration for Twitch Song Request Bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# ====================
# TWITCH CONFIGURATION
# ====================

# Client ID obtained from https://dev.twitch.tv/console
TWITCH_CLIENT_ID: str = os.getenv("TWITCH_CLIENT_ID", "")

# Client Secret obtained from https://dev.twitch.tv/console
TWITCH_CLIENT_SECRET: str = os.getenv("TWITCH_CLIENT_SECRET", "")

# Redirect URL for OAuth flow (must match the one configured in Twitch Dev Console)
OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:17563")

# Twitch channel to connect to (channel name WITHOUT #)
TARGET_CHANNEL: str = os.getenv("TARGET_CHANNEL", "")

# ====================
# COMMAND CONFIGURATION
# ====================

# Command prefix for song requests
CHAT_COMMAND_PREFIX: str = "!"

# Command to request a song
SONG_REQUEST_COMMAND: str = "sr"

# ====================
# SONG CONFIGURATION
# ====================

# Maximum song duration in seconds (15 minutes = 900 seconds)
MAX_DURATION_SECONDS: int = 900

# Desired audio quality (in kbps)
AUDIO_QUALITY: int = 192

# Audio format
AUDIO_FORMAT: str = "mp3"

# ====================
# DOWNLOAD CONFIGURATION
# ====================

# Download directory for audio files
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")

# ====================
# THREADING CONFIGURATION
# ====================

# Maximum number of concurrent threads
MAX_WORKERS: int = 5

# Timeout for download operations
DOWNLOAD_TIMEOUT: int = 60

# ====================
# YOUTUBE CONFIGURATION
# ====================

# Filtered category (only "Music")
YOUTUBE_CATEGORY: str = "Music"

# ====================
# LOGGING CONFIGURATION
# ====================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Log file
LOG_FILE: str = os.getenv("LOG_FILE", "twitch_sr.log")

# ====================
# QUEUE CONFIGURATION
# ====================

# Maximum queue size
MAX_QUEUE_SIZE: int = 50

# ====================
# EXTRA CONFIGURATION (Additional features)
# ====================

# Admin users (Twitch nicknames with special permissions)
# Configurable via ADMIN_USERS environment variable (e.g. "user1,user2,user3")
ADMIN_USERS: list[str] = [x.strip().lower() for x in os.getenv("ADMIN_USERS", "").split(",") if x.strip()]

# Whitelist users (can request even without following)
WHITELIST_USERS: list[str] = []

# Blacklist users (cannot use the bot)
BLACKLIST_USERS: list[str] = []

# ====================
# ADVANCED COMMAND CONFIGURATION
# ====================

# Playlist commands
PLAYLIST_CREATE_COMMAND: str = "create"
PLAYLIST_VIEW_COMMAND: str = "playlist"
PLAYLIST_ADD_COMMAND: str = "add"
PLAYLIST_REMOVE_COMMAND: str = "remove"
PLAYLIST_MOVE_COMMAND: str = "move"
PLAYLIST_CLEAR_COMMAND: str = "clear"
PLAYLIST_LIST_COMMAND: str = "list_playlists"
PLAYLIST_POMPA_COMMAND: str = "pump"

# Max songs per pump batch (sliding window)
MAX_POMPA_SONGS: int = 5

# Admin commands
ADMIN_WHITELIST_COMMAND: str = "whitelist"
ADMIN_BLACKLIST_COMMAND: str = "blacklist"
ADMIN_UNBLACKLIST_COMMAND: str = "unblacklist"
ADMIN_WHITELIST_LIST_COMMAND: str = "whitelist_list"
ADMIN_BLACKLIST_LIST_COMMAND: str = "blacklist_list"
ADMIN_SKIP_COMMAND: str = "skip"

ADMIN_REMOVE_QUEUE_COMMAND: str = "remove_queue"
ADMIN_CLEAR_QUEUE_COMMAND: str = "clear_queue"

# Analytics commands
ANALYTICS_STATS_COMMAND: str = "stats"
ANALYTICS_TOP_SONGS_COMMAND: str = "top_songs"
ANALYTICS_TOP_USERS_COMMAND: str = "top_users"
ANALYTICS_STORIA_COMMAND: str = "history_played"

# Music control commands
MUSIC_VOLUME_COMMAND: str = "volume"
MUSIC_PAUSE_COMMAND: str = "pause"
MUSIC_RESUME_COMMAND: str = "resume"
MUSIC_REPEAT_COMMAND: str = "repeat"
MUSIC_REPEAT_OFF_COMMAND: str = "repeat_off"
MUSIC_REPEAT_INFINITE_COMMAND: str = "repeat"
MUSIC_REPEAT_STOP_COMMAND: str = "stop_repeat"
MUSIC_NEXT_COMMAND: str = "next"
MUSIC_QUEUE_INFO_COMMAND: str = "queue_info"
MUSIC_DURATION_COMMAND: str = "duration"
MUSIC_DURATA_COMMAND: str = "at"
MUSIC_WHEN_COMMAND: str = "when"
MUSIC_RANDOM_COMMAND: str = "random"

# Utility commands
UTILITY_HELP_COMMAND: str = "help"
UTILITY_VERSION_COMMAND: str = "version"
UTILITY_UPTIME_COMMAND: str = "uptime"

# ====================
# RANDOM SONG COOLDOWN CONFIGURATION
# ====================

# Persistence file for random song cooldown
COOLDOWN_FILE: str = os.path.join("data", "random_cooldown.json")

# Cooldown duration for random songs in seconds (default: 1 hour)
RANDOM_COOLDOWN_SECONDS: int = 3600

# Maximum number of attempts to find a song not in cooldown
RANDOM_MAX_ATTEMPTS: int = 10
