# DATA - Data Flow Documentation

**Commit**: `7d0e5d5`
**Last updated**: `2026-07-07`

## Section Overview
Persistent data models: playlists, analytics stats, admin lists, and queue persistence. All use JSON files on disk.

## Files in this Section
- `main/playlist_manager.py` - Playlist CRUD (per-user JSON files)
- `main/analytics.py` - Stats tracking (requests, plays, history)
- `main/admin_handler.py` - Whitelist/blacklist management
- `main/queue_persistence.py` - Hybrid persistence: asyncio.Queue + disk JSON

## Data Flow Map for Each File

### playlist_manager.py
**Data model**: `Playlist(id, name, songs[], created_at, last_modified)` where each song is `PlaylistSong(query, file_path, username_original, added_at)`.

1. **Per-user files**: Each user has a JSON file: `data/playlists/{username}.json`
2. **Create** (`create_playlist()`): Generates UUID as playlist_id; checks for name collision
3. **Add song** (`add_song_to_playlist()`): Appends `PlaylistSong` to list, saves immediately
4. **Remove** (`remove_song_from_playlist()`): Supports index (1-based) or title substring match
5. **Move** (`swap_songs_in_playlist()`): Swaps two songs by 1-based index
6. **Pump** (`pompa_songs()`): Sliding-window random selection — excludes `recently_pumped_queries`; resets if all used

### analytics.py
**Data model**: JSON file `data/stats.json` with keys: total_requests, total_plays, songs_by_user, songs_by_title, play_history.

1. **Record request** (`record_request()`): Increments total_requests + per-user + per-title counts
2. **Record play** (`record_play()`): Increments total_plays + appends to play_history (capped at 1000)
3. **Get stats**: Methods return sorted lists of top users/songs; time-windowed stats for today/week/month
4. **Persistence**: Auto-save on every mutation via `_save_stats()`

### admin_handler.py
**Data model**: Two JSON files — `data/whitelist.json` and `data/blacklist.json`, each with `{"users": [...]} structure`.

1. **Load**: On init, reads both files into sets (case-insensitive)
2. **Add/remove**: Case-insensitive comparison; saves immediately on mutation
3. **Check**: `is_blacklisted(username)` — case-insensitive set lookup

### queue_persistence.py
**Data model**: JSON file `data/queue.json` with keys: version, last_updated, songs[].

1. **Load** (`load()`): Reads JSON on bot startup; validates song files exist via `SongRequestPersistence.validate_song_exists()`
2. **Save** (`save()`): Atomic write — writes to `.tmp`, then `replace()` (renames atomically)
3. **Backup** (`backup()`): Copies queue.json → queue.json.bak
4. **Song validation**: On restore, checks that each song's file still exists in downloads/

## Dependencies
- External: None (uses stdlib json + pathlib)
- Internal: Called from `main_core.py` for queue operations; from command handlers for playlist/admin/analytics
