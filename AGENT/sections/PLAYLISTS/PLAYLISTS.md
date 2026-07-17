# PLAYLISTS - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
User playlist management with JSON persistence. Each user has their own playlist file (`data/playlists/<username>.json`). Supports creating playlists, adding/removing/moving songs, and the "pompa" feature (queue N random songs from a playlist). Uses word-boundary matching for song name operations to avoid false positives.

## Files in this Section
- `main/playlist_manager.py` — PlaylistManager, Playlist, PlaylistSong dataclasses; CRUD + pompa logic
- `commands/playlists.py` — Command handlers: !create, !playlist, !add, !remove, !move, !clear, !list_playlists, !pump

## Data Flow Map

### Playlist (dataclass)
- **Fields**: id (UUID int), name, songs (list[PlaylistSong]), created_at, last_modified, recently_pumped_queries, has_pumped, last_pumped_queries
- **Serialization**: `to_dict()` / `from_dict()` for JSON persistence

### PlaylistSong (dataclass)
- **Fields**: query, file_path, username_original, added_at
- **file_path**: Real disk path if found via local matching at !add time; "unknown" otherwise

### PlaylistManager — CRUD Operations
1. **Lazy loading**: Playlists loaded from disk on first access per user (`_load_user_playlists`)
2. **create_playlist(username, name)**: Generate UUID → create Playlist → save to JSON
3. **add_song_to_playlist(username, name, query, file_path, original_user)**: Append PlaylistSong → save
4. **remove_song_from_playlist**: By index (int - 1) or by name (word-boundary regex match) → pop → save
5. **swap_songs_in_playlist**: Swap two positions (1-based to 0-based conversion) → save
6. **clear_playlist**: Clear songs list → save
7. **Data file**: `data/playlists/<username>.json` — Dict of {playlist_id: playlist_data}

### pompa_songs(username, playlist_name, n) — Random Batch Queuing
1. **Input**: Username, playlist name, count N (default 5)
2. **Check previous pump**: If songs from last pump are still in queue → reject ("You can't pump this much!")
3. **Filter available**: Exclude `recently_pumped_queries` from selection pool
4. **Reset if needed**: If no songs available (all recently pumped), reset tracking and use all songs
5. **Select N random**: `random.sample(available, count)` → update `recently_pumped_queries` + `has_pumped` + `last_pumped_queries`
6. **Output**: (selected_songs, error_msg, still_in_queue) tuple

### Command Handlers (commands/playlists.py)
- **cmd_add**: Calls `MusicDownloader._find_matching_file(query)` to resolve file_path before adding to playlist
- **cmd_pump**: Converts selected songs to SongRequest objects → puts in RequestQueue. Uses full file_path as query if available (bypasses YouTube search)

## Dependencies
- External: `json`, `uuid`, `random`
- Internal: Called from CommandProcessor; uses MusicDownloader for local file matching, RequestQueue for pompa queuing
