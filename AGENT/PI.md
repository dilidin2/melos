# Project Index - melos (Twitch Music Bot)

## Commit Reference
- Last updated: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
- Current branch: `master`

## Repository Tree

```
melos/
├── run.py                              # Entry point — wires all services and starts the bot
├── pyproject.toml                      # Project metadata, dependencies, tool configs (ruff, pytest)
├── requirements.txt                    # Flat dependency list (legacy, pyproject.toml is source of truth)
├── .env                                # Env vars: TWITCH_CLIENT_ID, TARGET_CHANNEL, ADMIN_USERS, etc.
├── tokens.json                         # Cached Twitch OAuth tokens (gitignored)
├── twitch_sr.log                       # Loguru log file (gitignored)
│
├── main/                               # Core bot logic and services
│   ├── __init__.py                     # Lazy imports for all public classes
│   ├── config.py                       # All configuration (Twitch, audio, queue, commands, vote skip)
│   ├── main_core.py                    # SongRequestBot, RequestQueue, DuplicateCache, SongRequest
│   ├── twitch_handler.py               # Twitch IRC connection, OAuth flow, command registration
│   ├── chat_message.py                 # Chat message formatting (error, notification, now-playing)
│   ├── music_downloader.py             # YouTube download via yt-dlp, local file matching, validation
│   ├── audio_player.py                 # Pygame mixer playback (play/pause/stop/volume)
│   ├── playlist_manager.py             # CRUD for user playlists, pompa (random batch queue)
│   ├── admin_handler.py                # Blacklist/whitelist management (JSON persistence)
│   ├── analytics.py                    # Request/play tracking, top songs/users, history
│   ├── command_processor.py            # Regex-based command router + permission checks + DI delegation
│   ├── services.py                     # CommandServices DI container (dataclass)
│   └── queue_persistence.py            # QueuePersistence (atomic JSON save), SongRequestPersistence
│
├── commands/                           # Command handler classes (one per domain)
│   ├── __init__.py                     # @admin_required decorator
│   ├── music.py                        # !pause, !resume, !volume, !repeat*, !next, !random, !ops, !vote
│   ├── playlists.py                    # !create, !playlist, !add, !remove, !move, !clear, !pump
│   ├── admin.py                        # !blacklist, !unblacklist, !skip, !remove_queue, !clear_queue
│   ├── analytics.py                    # !stats, !top_songs, !top_users, !history
│   └── utility.py                      # !help, !version, !uptime, !queue_info
│
├── utils/                              # Shared utilities
│   ├── __init__.py                     # (empty)
│   └── logger.py                       # Loguru setup (console + file with rotation/compression)
│
├── data/                               # Persistent JSON data (gitignored)
│   ├── queue.json                      # Persisted request queue
│   ├── blacklist.json                  # Blacklisted users
│   └── playlists/                      # Per-user playlist files (<username>.json)
│
├── downloads/                          # Downloaded audio files (yt-dlp output, gitignored)
├── tests/                              # Pytest test suite
│   ├── conftest.py                     # Shared fixtures
│   └── test_*.py                       # ~20 test modules covering all components
│
└── AGENT/                              # This project index (tracked in git)
    ├── PI.md                           # ← you are here
    └── sections/                       # One .md per logical section with data flow docs
        ├── CORE/CORE.md
        ├── AUDIO/AUDIO.md
        ├── DOWNLOAD/DOWNLOAD.md
        ├── COMMANDS/COMMANDS.md
        ├── PLAYLISTS/PLAYLISTS.md
        ├── ADMIN/ADMIN.md
        ├── ANALYTICS/ANALYTICS.md
        ├── TWITCH/TWITCH.md
        ├── PERSISTENCE/PERSISTENCE.md
        ├── CONFIG/CONFIG.md
        ├── UTILS/UTILS.md
        └── TESTS/TESTS.md
```

## Section Navigation

| Section | Description | Files | Read this when... |
|---------|-------------|-------|--------------------|
| [CORE](sections/CORE/CORE.md) | Main bot loop, request queue, duplicate cache, playback orchestration | `main_core.py`, `SongRequestBot`, `RequestQueue`, `DuplicateCache` | If you need to change how song requests flow through the queue, how repeat/vote-skip works, or modify the main event loop → read `AGENT/sections/CORE/CORE.md` |
| [AUDIO](sections/AUDIO/AUDIO.md) | Audio playback via Pygame mixer | `audio_player.py` | If you need to change playback behavior (play/pause/stop), volume handling, or switch audio backends → read `AGENT/sections/AUDIO/AUDIO.md` |
| [DOWNLOAD](sections/DOWNLOAD/DOWNLOAD.md) | YouTube search, download via yt-dlp, local file matching, validation | `music_downloader.py` | If you need to change how songs are searched/downloaded from YouTube, modify duration/category filters, or improve local file matching → read `AGENT/sections/DOWNLOAD/DOWNLOAD.md` |
| [COMMANDS](sections/COMMANDS/COMMANDS.md) | Command routing (regex patterns), permission checks, handler delegation via DI | `command_processor.py`, `commands/*.py`, `services.py` | If you need to add a new chat command, change command syntax, modify admin permissions, or fix command dispatch → read `AGENT/sections/COMMANDS/COMMANDS.md` |
| [PLAYLISTS](sections/PLAYLISTS/PLAYLISTS.md) | User playlist CRUD, pompa (random batch queuing), JSON persistence | `playlist_manager.py`, `commands/playlists.py` | If you need to change playlist creation, song management, the pompa feature, or playlist data format → read `AGENT/sections/PLAYLISTS/PLAYLISTS.md` |
| [ADMIN](sections/ADMIN/ADMIN.md) | Blacklist/whitelist management, admin command handlers | `admin_handler.py`, `commands/admin.py` | If you need to change blacklist behavior, add new admin commands, or modify permission checks → read `AGENT/sections/ADMIN/ADMIN.md` |
| [ANALYTICS](sections/ANALYTICS/ANALYTICS.md) | Request/play tracking, top songs/users stats, play history | `analytics.py`, `commands/analytics.py` | If you need to add new statistics, change how tracking works, or modify !stats/!top_songs output → read `AGENT/sections/ANALYTICS/ANALYTICS.md` |
| [TWITCH](sections/TWITCH/TWITCH.md) | Twitch IRC connection, OAuth flow, command registration via twitchAPI | `twitch_handler.py`, `chat_message.py` | If you need to change how the bot connects to Twitch, handle OAuth tokens, register new commands, or modify chat messaging → read `AGENT/sections/TWITCH/TWITCH.md` |
| [PERSISTENCE](sections/PERSISTENCE/PERSISTENCE.md) | Queue persistence (atomic JSON save/load), song file validation | `queue_persistence.py` | If you need to change how the queue is saved/restored, add new persisted data, or modify backup strategy → read `AGENT/sections/PERSISTENCE/PERSISTENCE.md` |
| [CONFIG](sections/CONFIG/CONFIG.md) | All configuration: Twitch credentials, audio settings, command names, thresholds | `config.py`, `.env` | If you need to add a new config option, change default values (max duration, queue size, vote count), or modify command prefixes → read `AGENT/sections/CONFIG/CONFIG.md` |
| [UTILS](sections/UTILS/UTILS.md) | Shared utilities: logging setup with Loguru | `utils/logger.py` | If you need to change log format, rotation policy, or add new utility modules → read `AGENT/sections/UTILS/UTILS.md` |
| [TESTS](sections/TESTS/TESTS.md) | Pytest test suite covering all components | `tests/*.py` | If you need to add tests for a new feature, understand test fixtures, or run the test suite → read `AGENT/sections/TESTS/TESTS.md` |

## Glossary

- **Entry Point**: `run.py` — Wires all services into DI container, starts SongRequestBot
- **Core Bot**: `SongRequestBot` (main_core.py) — Main orchestrator: queue processing, playback, repeat modes
- **Command Router**: `CommandProcessor` — Regex-based dispatcher with @admin_required permission checks
- **DI Container**: `CommandServices` (services.py) — Dataclass holding all injected dependencies
- **Queue**: `RequestQueue` — asyncio.Queue wrapper with in-place mutation and lock protection
- **Config**: `config.py` — All settings loaded from .env + hardcoded defaults
- **Data Flow**: See section-specific files for detailed flow maps
