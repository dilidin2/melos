# PLAYLISTS - Data Flow Documentation

**Commit**: `f2f4f10 fix: make !repeat_off actually disable repeat mode`
**Last updated**: 2026-07-15

## Section Overview
Per-user playlist management with CRUD operations and "pompa" (random pump) feature.

## Files in this Section
- `main/playlist_manager.py` - Playlist data model + persistence
- `commands/playlists.py` - Command handlers for playlists

## Data Flow Map for Each File

### playlist_manager.py
1. **Input**: Username, playlist name, song query/file_path
2. **Transformation**:
   - Playlists stored as JSON per user: `data/playlists/<username>.json`
   - CRUD: `create_playlist`, `add_song_to_playlist`, `remove_song_from_playlist`, `swap_songs_in_playlist`, `clear_playlist`
   - **Pompa**: Selects N random songs from playlist using sliding-window dedup (tracks `recently_pumped_queries`); resets if no songs available
3. **Output**: `Playlist` objects, boolean success, or selected song lists
4. **Error Handling**: Missing playlists return `None`; invalid indices return `False`

### commands/playlists.py
1. **Input**: Command parameters from `CommandProcessor`
2. **Transformation**: Delegates to `PlaylistManager`, formats responses with chat-friendly formatting (emojis, pagination)
3. **Output**: Response strings for chat
4. **Key methods**: `cmd_create`, `cmd_playlist` (view), `cmd_add`, `cmd_remove`, `cmd_move`, `cmd_clear`, `cmd_list_playlists`, `cmd_pump`

## Dependencies
- External: `uuid` (stdlib) for playlist IDs, `json` (stdlib)
- Internal: Depends on `main_core.py` (`RequestQueue`) for pompa injection into queue
