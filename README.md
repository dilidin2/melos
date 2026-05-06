# Chat-Tune

A Twitch chat bot for requesting and playing music directly in your stream via chat commands.

## Features

- 🎵 **Song Requests** — Type `!sr <song name>` in chat to add songs to a queue
- 📻 **YouTube Music Downloading** — Downloads music from YouTube (Music category only, max 15 min)
- 🔊 **Audio Playback** — Plays songs in real-time using Pygame
- 📋 **Persistent Queue** — Queue survives bot restarts (saved to JSON)
- 🎲 **Random Playback** — Plays random songs from your downloads folder when the queue is empty
- 📊 **Analytics** — Tracks requests, plays, top songs, and top users
- 📁 **Playlists** — Create and manage custom playlists
- 👑 **Admin Commands** — Whitelist/blacklist users, manage queue, skip songs
- 🔁 **Repeat Modes** — Off, count-based, or infinite repeat
- 🏷️ **Duplicate Detection** — Avoids re-downloading the same song

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dilidin2/chat-tune.git
cd chat-tune
```

### 2. Install uv (Python package manager)

Follow the installation instructions at: https://docs.astral.sh/uv/getting-started/installation/

### 3. Create a virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
TARGET_CHANNEL=your_twitch_channel
OAUTH_REDIRECT_URI=http://localhost:17563
```

You can obtain your Twitch Client ID and Client Secret from the [Twitch Developer Console](https://dev.twitch.tv/console).

## Usage

```bash
python run.py
```

The bot will connect to your Twitch channel and start listening for commands.

## Commands

| Command | Description |
|---------|-------------|
| `!sr <query>` | Request a song |
| `!help` | Show help |
| `!volume <0-100>` | Set volume |
| `!pause` | Pause playback |
| `!riprendi` | Resume playback |
| `!repeat` | Enable repeat mode |
| `!ripeti` | Enable infinite repeat |
| `!stop_ripeti` | Disable repeat |
| `!next` | Skip to next song |
| `!queue_info` | Show current queue |
| `!stats` | View analytics |
| `!top_canzoni` | Show top requested songs |
| `!top_user` | Show top requesting users |
| `!playlist <name>` | View a playlist |
| `!crea <name>` | Create a playlist |
| `!aggiungi <playlist> <song>` | Add song to playlist |
| `!rimuovi <playlist> <index>` | Remove song from playlist |
| `!svuota <playlist>` | Clear a playlist |
| `!pompa <playlist>` | Pump (play) a playlist |
| `!whitelist <user>` | Whitelist a user (admin) |
| `!blacklist <user>` | Blacklist a user (admin) |
| `!skippa` | Skip current song (admin) |
| `!clear_queue` | Clear the queue (admin) |

## Project Structure

```
chat-tune/
├── run.py                  # Main entry point
├── main/                   # Core bot logic
│   ├── main_core.py        # SongRequestBot, queue, duplicate cache
│   ├── twitch_handler.py   # Twitch chat connection
│   ├── music_downloader.py # YouTube downloading (yt-dlp)
│   ├── audio_player.py     # Audio playback (Pygame)
│   ├── config.py           # Configuration
│   ├── services.py         # Dependency injection container
│   ├── playlist_manager.py # Playlist management
│   ├── analytics.py        # Statistics tracking
│   ├── admin_handler.py    # Admin permissions
│   ├── chat_message.py     # Chat message utilities
│   ├── command_processor.py # Command routing
│   └── queue_persistence.py # Queue save/load
├── commands/               # Command handlers
│   ├── music.py            # Music commands
│   ├── playlists.py        # Playlist commands
│   ├── admin.py            # Admin commands
│   ├── analytics.py        # Analytics commands
│   └── utility.py          # Utility commands
├── utils/                  # Utilities
│   └── logger.py           # Logging setup
├── data/                   # Persistent data
│   ├── queue.json          # Request queue
│   ├── stats.json          # Analytics data
│   └── playlists/          # Playlist files
├── downloads/              # Downloaded audio files
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
└── .env                    # Environment variables
```

## Dependencies

| Package | Purpose |
|---------|---------|
| twitchAPI | Twitch chat integration |
| yt-dlp | YouTube music downloading |
| pygame | Audio playback |
| soundfile | Audio file reading |
| numpy | Audio processing |
| python-dotenv | Environment variable loading |
| loguru | Logging |

## License

MIT
