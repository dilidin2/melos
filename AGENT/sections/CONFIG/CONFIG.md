# CONFIG - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Centralized configuration loaded from `.env` file (via python-dotenv) with hardcoded defaults. All settings are module-level constants imported by other modules. Covers Twitch credentials, audio quality, download limits, command names, queue size, vote thresholds, and logging.

## Files in this Section
- `main/config.py` — All configuration constants
- `.env` — Environment variables (gitignored)

## Configuration Groups

### Twitch Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| TWITCH_CLIENT_ID | "" | From Twitch Dev Console — used for Device Code Flow (no secret needed) |
| TARGET_CHANNEL | "" | Channel to connect to (no #) |

### Command Configuration
| Variable | Value | Description |
|----------|-------|-------------|
| CHAT_COMMAND_PREFIX | "!" | Command prefix |
| SONG_REQUEST_COMMAND | "sr" | Song request command name |

### Song Configuration
| Variable | Value | Description |
|----------|-------|-------------|
| MAX_DURATION_SECONDS | 900 | Max song length (15 min) |
| AUDIO_QUALITY | 192 | kbps for FFmpeg conversion |
| AUDIO_FORMAT | "mp3" | Output format |

### Download Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| DOWNLOAD_DIR | "./downloads" | Audio file storage |
| DOWNLOAD_TIMEOUT | 60 | Socket timeout in seconds |
| YOUTUBE_CATEGORY | "Music" | Allowed YouTube category |

### Queue Configuration
| Variable | Value | Description |
|----------|-------|-------------|
| MAX_QUEUE_SIZE | 50 | Max requests in queue |
| MAX_WORKERS | 5 | ThreadPoolExecutor workers |

### Vote-to-Skip Configuration
| Variable | Value | Description |
|----------|-------|-------------|
| VOTE_SKIP_COMMAND | "vote" | Command name |
| VOTE_REQUIRED_COUNT | 3 | Voters needed to skip |

### Admin/Blacklist
| Variable | Default | Description |
|----------|---------|-------------|
| ADMIN_USERS | [] | Comma-separated from env (e.g., "user1,user2") |
| BLACKLIST_USERS | [] | Hardcoded blacklist (usually empty, uses file) |

### Logging
| Variable | Default | Description |
|----------|---------|-------------|
| LOG_LEVEL | "INFO" | DEBUG/INFO/WARNING/ERROR |
| LOG_FILE | "twitch_sr.log" | Log file path |

### Command Names (all ! prefixed in chat)
- Playlist: create, playlist, add, remove, move, clear, list_playlists, pump
- Admin: blacklist, unblacklist, blacklist_list, skip, remove_queue, clear_queue
- Analytics: stats, top_songs, top_users, history_played
- Music: volume, pause, resume, repeat, repeat_off, stop_repeat, next, queue_info, duration, durata (at), when, random, ops
- Utility: help, version, uptime

### Random Song Cooldown
| Variable | Value | Description |
|----------|-------|-------------|
| COOLDOWN_FILE | "data/random_cooldown.json" | Cooldown persistence |
| RANDOM_COOLDOWN_SECONDS | 3600 | 1 hour cooldown |
| RANDOM_MAX_ATTEMPTS | 10 | Max attempts to find non-cooldown song |

## Dependencies
- External: `os`, `dotenv` (load_dotenv)
- Internal: Imported by virtually every module in the project
