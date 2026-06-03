"""Configuration for Twitch Song Request Bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# ====================
# CONFIGURAZIONE TWITCH
# ====================

# Client ID ottenuto da https://dev.twitch.tv/console
TWITCH_CLIENT_ID: str = os.getenv("TWITCH_CLIENT_ID", "")

# Client Secret ottenuto da https://dev.twitch.tv/console
TWITCH_CLIENT_SECRET: str = os.getenv("TWITCH_CLIENT_SECRET", "")

# Redirect URL per OAuth flow (deve corrispondere a quello configurato in Twitch Dev Console)
OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:17563")

# Canale Twitch a cui connettersi (nome del canale SENZA #)
TARGET_CHANNEL: str = os.getenv("TARGET_CHANNEL", "")

# ====================
# CONFIGURAZIONE COMANDI
# ====================

# Prefix del comando per richiedere canzoni
CHAT_COMMAND_PREFIX: str = "!"

# Comando per richiedere una canzone
SONG_REQUEST_COMMAND: str = "sr"

# ====================
# CONFIGURAZIONE CANZONI
# ====================

# Durata massima della canzone in secondi (15 minuti = 900 secondi)
MAX_DURATION_SECONDS: int = 900

# Qualità audio desiderata (in kbps)
AUDIO_QUALITY: int = 192

# Formato audio
AUDIO_FORMAT: str = "mp3"

# ====================
# CONFIGURAZIONE DOWNLOAD
# ====================

# Directory di download per i file audio
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")

# ====================
# CONFIGURAZIONE THREADING
# ====================

# Numero massimo di thread concorrenti
MAX_WORKERS: int = 5

# Timeout per le operazioni di download
DOWNLOAD_TIMEOUT: int = 60

# ====================
# CONFIGURAZIONE YOUTUBE
# ====================

# Categoria filtrata (solo "Music")
YOUTUBE_CATEGORY: str = "Music"

# ====================
# CONFIGURAZIONE LOGGING
# ====================

# Livello di log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# File di log
LOG_FILE: str = os.getenv("LOG_FILE", "twitch_sr.log")

# ====================
# CONFIGURAZIONE QUEUE
# ====================

# Dimensione massima della coda
MAX_QUEUE_SIZE: int = 50

# ====================
# CONFIGURAZIONE EXTRA (Feature aggiuntive)
# ====================

# Admin users (Twitch nicknames con permessi speciali)
# Configurabile via variabile d'ambiente ADMIN_USERS (es: "user1,user2,user3")
ADMIN_USERS: list[str] = [x.strip().lower() for x in os.getenv("ADMIN_USERS", "").split(",") if x.strip()]

# Whitelist users (possono richiedere anche senza follower)
WHITELIST_USERS: list[str] = []

# Blacklist users (non possono usare il bot)
BLACKLIST_USERS: list[str] = []

# ====================
# CONFIGURAZIONE COMANDI AVANZATI
# ====================

# Playlist commands
PLAYLIST_CREATE_COMMAND: str = "crea"
PLAYLIST_VIEW_COMMAND: str = "playlist"
PLAYLIST_ADD_COMMAND: str = "aggiungi"
PLAYLIST_REMOVE_COMMAND: str = "rimuovi"
PLAYLIST_MOVE_COMMAND: str = "sposta"
PLAYLIST_CLEAR_COMMAND: str = "svuota"
PLAYLIST_LIST_COMMAND: str = "lista_playlist"
PLAYLIST_POMPA_COMMAND: str = "pompa"

# Max songs per pompa batch (sliding window)
MAX_POMPA_SONGS: int = 5

# Admin commands
ADMIN_WHITELIST_COMMAND: str = "whitelist"
ADMIN_BLACKLIST_COMMAND: str = "blacklist"
ADMIN_UNBLACKLIST_COMMAND: str = "unblacklist"
ADMIN_WHITELIST_LIST_COMMAND: str = "whitelist_list"
ADMIN_BLACKLIST_LIST_COMMAND: str = "blacklist_list"
ADMIN_SKIP_COMMAND: str = "skippa"

ADMIN_REMOVE_QUEUE_COMMAND: str = "rimuovi_coda"
ADMIN_QUEUE_INFO_COMMAND: str = "coda_info"
ADMIN_CLEAR_QUEUE_COMMAND: str = "clear_queue"

# Analytics commands
ANALYTICS_STATS_COMMAND: str = "stats"
ANALYTICS_TOP_SONGS_COMMAND: str = "top_canzoni"
ANALYTICS_TOP_USERS_COMMAND: str = "top_user"
ANALYTICS_STORIA_COMMAND: str = "storia"

# Music control commands
MUSIC_VOLUME_COMMAND: str = "volume"
MUSIC_PAUSE_COMMAND: str = "pausa"
MUSIC_RESUME_COMMAND: str = "riprendi"
MUSIC_REPEAT_COMMAND: str = "repeat"
MUSIC_REPEAT_OFF_COMMAND: str = "repeat_off"
MUSIC_REPEAT_INFINITE_COMMAND: str = "ripeti"
MUSIC_REPEAT_STOP_COMMAND: str = "stop_ripeti"
MUSIC_NEXT_COMMAND: str = "next"
MUSIC_QUEUE_INFO_COMMAND: str = "queue_info"
MUSIC_DURATION_COMMAND: str = "duration"
MUSIC_DURATA_COMMAND: str = "durata"
MUSIC_WHEN_COMMAND: str = "quando"
MUSIC_RANDOM_COMMAND: str = "random"

# Utility commands
UTILITY_HELP_COMMAND: str = "help"
UTILITY_VERSION_COMMAND: str = "version"
UTILITY_UPTIME_COMMAND: str = "uptime"

# ====================
# CONFIGURAZIONE COOLDOWN CANZONI RANDOM
# ====================

# File di persistenza per il cooldown delle canzoni random
COOLDOWN_FILE: str = os.path.join("data", "random_cooldown.json")

# Durata del cooldown per le canzoni random in secondi (default: 1 ora)
RANDOM_COOLDOWN_SECONDS: int = 3600

# Numero massimo di tentativi per trovare una canzone non nel cooldown
RANDOM_MAX_ATTEMPTS: int = 10
