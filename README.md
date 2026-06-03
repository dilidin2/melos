# melos

A Twitch chat bot for requesting and playing music directly in your stream via chat commands.

![melos](image/img.png)

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

The bot will connect to your Twitch channel and start listening for commands.

## Commands

| Command | Description |
|---------|-------------|
| `!sr <query>` | Request a song |
| `!random [N]` | Play N random songs from library |
| `!duration <song>` | Show song duration |
| `!durata <N>` | Show duration of song at position N in queue |
| `!quando` | Estimate when your song will play |
| `!help [cmd]` | Show help |
| `!volume <0-100>` | Set volume |
| `!pausa` | Pause playback |
| `!riprendi` | Resume playback |
| `!repeat [N]` | Enable repeat mode |
| `!repeat_off` | Disable repeat |
| `!ripeti [N]` | Repeat song (N=1 or infinite) |
| `!stop_ripeti` | Stop repeat |
| `!next` | Next song |
| `!queue_info` | Show current queue |
| `!stats` | View analytics |
| `!top_canzoni [N]` | Show top requested songs |
| `!top_user [N]` | Show top requesting users |
| `!storia [N]` | Play history of last N songs |
| `!playlist <name>` | View a playlist |
| `!crea <name>` | Create a playlist |
| `!aggiungi <playlist> <song>` | Add song to playlist |
| `!rimuovi <playlist> <index>` | Remove song from playlist |
| `!sposta <playlist> <p1> <p2>` | Swap songs in playlist |
| `!svuota <playlist>` | Clear a playlist |
| `!lista_playlist` | List all playlists |
| `!pompa <playlist> [N]` | Pump N random songs from playlist |
| `!whitelist <user>` | Whitelist a user (admin) |
| `!blacklist <user>` | Blacklist a user (admin) |
| `!unblacklist <user>` | Remove from blacklist (admin) |
| `!whitelist_list` | Show whitelist (admin) |
| `!blacklist_list` | Show blacklist (admin) |
| `!skippa` / `!skip` | Skip current song (admin) |
| `!rimuovi_coda <pos>` | Remove from queue (admin) |
| `!coda_info` | Queue info (admin) |
| `!clear_queue` | Clear the queue (admin) |
| `!version` | Show bot version |
| `!uptime` | Show bot uptime |

## Project Structure

```
melos/
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
