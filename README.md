# melos

A Twitch chat bot for requesting and playing music directly in your stream via chat commands.

![melos](image/img.png)

## Features

- 🎵 **Song Requests** — Type `!sr <song name>` in chat to add songs to a queue
- 📻 **YouTube Music Downloading** — Downloads music from YouTube (Music category only, max 15 min)
- 🔊 **Audio Playback** — Plays songs in real-time using Pygame
- 🗳️ **Democratic Skip** — 3 different users can vote `!vote` to skip the current song
- 📋 **Persistent Queue** — Queue survives bot restarts (saved to JSON with atomic writes)
- 🎲 **Random Playback** — Plays random songs from your downloads folder when the queue is empty
- 📊 **Analytics** — Tracks requests, plays, top songs, and top users
- 📁 **Playlists** — Create and manage custom playlists with `!pump` for random batch queuing
- 👑 **Admin Commands** — Blacklist users, manage queue, skip songs, control volume
- 🔁 **Repeat Modes** — Off, count-based, or infinite repeat
- 💾 **Local File Matching** — Word-boundary matching on disk avoids re-downloading known songs
- 🏷️ **Duplicate Detection** — LRU cache (100 entries) prevents redundant downloads

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dilidin2/melos.git
cd melos
```

### 2. Install uv (Python package manager)

Follow the installation instructions at: https://docs.astral.sh/uv/getting-started/installation/

### 3. Create a virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
TARGET_CHANNEL=your_twitch_channel
OAUTH_REDIRECT_URI=http://localhost:17563
ADMIN_USERS=admin1,admin2
LOG_LEVEL=INFO
LOG_FILE=twitch_sr.log
DOWNLOAD_DIR=./downloads
```

To get your credentials:

1. Visit the [Twitch Developer Console](https://dev.twitch.tv/console)
2. Click **"Register Your Application"**
3. Fill in the form:
   - **Name**: any name you like
   - **OAuth Redirect URLs**: `http://localhost:17563`
   - **Category**: `Chat Bot`
   - **Client Type**: `Confidential`
4. Copy the **Client ID** shown on the page
5. Under **Client Secret**, click **"New Secret"** and copy the generated value

## Usage

```bash
python run.py
```

The bot will connect to your Twitch channel and start listening for commands. Press `Ctrl+C` for a graceful shutdown (drains queue, persists state).

## Commands

### Music Requests & Playback

| Command | Description |
|---------|-------------|
| `!sr <query>` | Request a song (title or YouTube URL) |
| `!random [N]` | Play N random songs from library |
| `!vote` | Vote to skip the current song (needs 3 different users) |
| `!duration <song>` | Show song duration |
| `!at <N>` | Show duration of song at position N in queue |
| `!when` | Estimate when your next song will play |
| `!next` | Show the next song in the queue |
| `!queue_info` | Show queue stats (count, estimated duration, repeat status) |
| `!ops` | Remove the last song you added from the queue |

### Playback Control (Admin)

| Command | Description |
|---------|-------------|
| `!volume <0-100>` | Set volume level |
| `!pause` | Pause playback |
| `!resume` | Resume playback |
| `!repeat [N]` | Repeat current song N times (no arg = infinite) |
| `!repeat_off` | Disable repeat mode |
| `!stop_repeat` | Stop repeat and return to normal queue flow |

### Playlists

| Command | Description |
|---------|-------------|
| `!create <name>` | Create a new playlist |
| `!playlist [name] [page]` | List your playlists or show songs in one |
| `!add <playlist> <song>` | Add a song to a playlist (matches local files) |
| `!remove <playlist> <pos/name>` | Remove a song by position or name |
| `!move <playlist> <p1> <p2>` | Swap two songs in a playlist |
| `!clear <playlist>` | Clear all songs from a playlist |
| `!list_playlists` | List all your playlists |
| `!pump <playlist> [N]` | Queue N random songs from a playlist (sliding window) |

### Admin Commands

| Command | Description |
|---------|-------------|
| `!blacklist <user>` | Blacklist a user (blocks song requests) |
| `!unblacklist <user>` | Remove a user from blacklist |
| `!blacklist_list` | Show all blacklisted users |
| `!skip` | Skip the current song |
| `!remove_queue <pos>` | Remove a specific position from the queue |
| `!clear_queue` | Clear the entire queue |

Admin users are configured via the `ADMIN_USERS` environment variable (comma-separated usernames).

### Analytics

| Command | Description |
|---------|-------------|
| `!stats` | Show general bot statistics (total, today, this week) |
| `!top_songs [N]` | Show top N most requested songs |
| `!top_users [N]` | Show top N most active users |
| `!history [N]` | Show last N songs played |

### Utility

| Command | Description |
|---------|-------------|
| `!help [cmd]` | Show help or details for a specific command |
| `!version` | Show bot version |
| `!uptime` | Show how long the bot has been running |

## Architecture

```
melos/
├── run.py                              # Entry point — wires all services, starts bot
├── main/                               # Core bot logic and services
│   ├── config.py                       # All configuration (Twitch, audio, queue, commands)
│   ├── main_core.py                    # SongRequestBot, RequestQueue, DuplicateCache
│   ├── twitch_handler.py               # Twitch IRC connection + OAuth flow
│   ├── chat_message.py                 # Chat message formatting utilities
│   ├── music_downloader.py             # YouTube download (yt-dlp), local file matching
│   ├── audio_player.py                 # Pygame mixer playback
│   ├── playlist_manager.py             # User playlist CRUD + pompa feature
│   ├── admin_handler.py                # Blacklist/whitelist management
│   ├── analytics.py                    # Request/play tracking + statistics
│   ├── command_processor.py            # Regex command router + permission checks
│   ├── services.py                     # DI container (CommandServices dataclass)
│   └── queue_persistence.py            # Atomic JSON save/load for the queue
├── commands/                           # Command handler classes (one per domain)
│   ├── music.py                        # Playback control commands
│   ├── playlists.py                    # Playlist management commands
│   ├── admin.py                        # Admin/moderation commands
│   ├── analytics.py                    # Statistics commands
│   └── utility.py                      # Help, version, uptime, queue_info
├── utils/                              # Shared utilities
│   └── logger.py                       # Loguru setup (console + file with rotation)
├── data/                               # Persistent data (gitignored)
│   ├── queue.json                      # Persisted request queue
│   ├── blacklist.json                  # Blacklisted users
│   ├── stats.json                      # Analytics data
│   └── playlists/                      # Per-user playlist files
├── downloads/                          # Downloaded audio files (gitignored)
├── tests/                              # Pytest test suite (~20 modules)
├── AGENT/                              # Project index for AI agents (tracked in git)
│   ├── PI.md                           # Root index with tree + section navigation
│   └── sections/                       # One .md per logical section with data flows
├── pyproject.toml                      # Project metadata, dependencies, tool configs
├── .env                                # Environment variables (gitignored)
└── tokens.json                         # Cached Twitch OAuth tokens (gitignored)
```

## Key Design Decisions

- **Dependency Injection**: All services are wired explicitly via `CommandServices` dataclass in `run.py`. No global state or implicit coupling.
- **Thread Safety**: `RequestQueue` uses asyncio.Lock for logical race protection at await boundaries. Audio playback runs in a `ThreadPoolExecutor` to avoid blocking the event loop.
- **Local File Matching**: Word-boundary regex (`\bword\b`) on disk filenames avoids false positives. All query words must match as whole words.
- **Atomic Persistence**: Queue saves use temp file + `os.replace()` for crash safety.
- **Command Routing**: Precompiled regex patterns with dynamic admin permission discovery via `@admin_required` decorator.

## Dependencies

| Package | Purpose |
|---------|---------|
| twitchAPI | Twitch IRC chat integration (auth, messaging, commands) |
| yt-dlp | YouTube music downloading + metadata extraction |
| pygame | Audio playback (mixer module) |
| python-dotenv | Environment variable loading from `.env` |
| loguru | Structured logging with rotation and compression |

## Development

### Running Tests

```bash
python -m pytest              # Run all tests
python -m pytest -v           # Verbose output
python -m pytest -k "queue"   # Keyword filter
python -m pytest -m "not slow"  # Exclude slow tests
```

Test markers: `slow`, `integration`, `unit`. Pytest config in `pyproject.toml` (asyncio_mode: auto).

### Code Quality

Ruff is configured in `pyproject.toml` (target: py310, line length: 100, rules: E, F, I, W).

## License

MIT
