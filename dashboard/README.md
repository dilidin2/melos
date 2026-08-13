# Melos Dashboard

Web dashboard for managing the Melos Twitch music bot.

## Features

- **Overview**: Bot status, playback controls, repeat mode, queue preview, stats
- **Queue**: View and manage the song queue, remove individual songs or clear all
- **Playlists**: Browse, create, and manage user playlists
- **Blacklist/Whitelist**: Add or remove users directly
- **Analytics**: Top songs, top users, play history, daily/weekly/monthly stats
- **Library**: View all downloaded audio files

## Configuration

The dashboard is enabled by default. Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_ENABLED` | `true` | Enable/disable the dashboard |
| `DASHBOARD_PORT` | `8080` | Port to run the dashboard on |
| `DASHBOARD_HOST` | `0.0.0.0` | Host to bind to |

## Usage

Start the bot as usual:

```bash
python run.py
```

The dashboard will be available at `http://localhost:8080`.

## API Endpoints

All endpoints are prefixed with `/api`.

### Status
- `GET /api/status` - Bot status and connection info

### Queue
- `GET /api/queue?limit=N` - Get queue items
- `DELETE /api/queue/{position}` - Remove song by position (1-based)
- `DELETE /api/queue` - Clear entire queue
- `POST /api/queue/skip` - Skip current song

### Playback
- `POST /api/playback/pause` - Pause playback
- `POST /api/playback/resume` - Resume playback
- `POST /api/playback/stop` - Stop playback
- `POST /api/playback/volume?level=N` - Set volume (0-100)
- `POST /api/playback/repeat?mode=MODE&count=N` - Set repeat mode

### Blacklist
- `GET /api/blacklist` - List blacklisted users
- `POST /api/blacklist?username=USER` - Add user
- `DELETE /api/blacklist/{username}` - Remove user

### Whitelist
- `GET /api/whitelist` - List whitelisted users
- `POST /api/whitelist?username=USER` - Add user
- `DELETE /api/whitelist/{username}` - Remove user

### Playlists
- `GET /api/playlists?username=USER` - List all playlists (or for specific user)
- `GET /api/playlists/{username}/{playlist_id}` - Get playlist details
- `POST /api/playlists?username=USER&name=NAME` - Create playlist
- `DELETE /api/playlists/{username}/{playlist_id}` - Delete playlist
- `POST /api/playlists/{username}/{name}/songs?query=QUERY` - Add song to playlist
- `DELETE /api/playlists/{username}/{name}/songs/{index_or_name}` - Remove song

### Analytics
- `GET /api/analytics/summary` - Overall stats
- `GET /api/analytics/top-songs?n=N` - Top songs
- `GET /api/analytics/top-users?n=N` - Top users
- `GET /api/analytics/history?n=N` - Play history

### Library
- `GET /api/library?limit=N` - List downloaded files
