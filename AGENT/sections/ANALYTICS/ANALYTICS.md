# ANALYTICS - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Statistics tracking for song requests and plays. Records every request and successful playback to JSON. Provides top songs/users rankings and play history with time filtering (today/week/month). Keeps last 1000 plays in history.

## Files in this Section
- `main/analytics.py` — Analytics class: record/play tracking, stats aggregation
- `commands/analytics.py` — Command handlers: !stats, !top_songs, !top_users, !history

## Data Flow Map

### Analytics — Recording
1. **record_request(username, query)** (called from SongRequestBot._handle_song_request):
   - Increment `_total_requests`
   - Update `_songs_by_user[username.lower()]` count
   - Update `_songs_by_title[query.lower()]` count
   - Save to `data/stats.json`
2. **record_play(username, query)** (called from SongRequestBot._process_request on success):
   - Increment `_total_plays`
   - Append {username, query, timestamp} to `_play_history`
   - Save to `data/stats.json`

### Analytics — Queries
- **get_top_songs(N)**: Sort `_songs_by_title` by count descending → return top N
- **get_top_users(N)**: Sort `_songs_by_user` by count descending → return top N
- **get_stats_today()**: Filter play_history by today's date → count + unique users
- **get_stats_week()**: Filter by last 7 days
- **get_stats_month()**: Filter by last 30 days
- **get_play_history(N)**: Return last N entries from history

### Persistence
- **File**: `data/stats.json`
- **Format**: {total_requests, total_plays, songs_by_user, songs_by_title, play_history[-1000:]}
- **Load on init**: Read from disk or reset to zeros if file missing/corrupt

### Command Handlers (commands/analytics.py)
- **cmd_stats**: Show totals + today/week stats
- **cmd_top_songs(N)**: Format top N songs as ranked list
- **cmd_top_users(N)**: Format top N users as ranked list
- **cmd_history(N)**: Reverse-played history with formatted timestamps

## Dependencies
- External: `json`, `pathlib`, `datetime`
- Internal: Called from SongRequestBot (recording), CommandProcessor (queries)
- Data file: `data/stats.json`
