# PERSISTENCE - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Queue persistence layer providing atomic JSON save/load for the request queue. Uses temp file + rename pattern for crash safety. Loaded on startup, saved after every queue mutation.

## Files in this Section
- `main/queue_persistence.py` — QueuePersistence (atomic JSON save/load), SongRequestPersistence (file validation)

## Data Flow Map

### QueuePersistence
1. **Init**: Create `data/queue.json` parent dir if needed; create asyncio `_save_lock`
2. **load()** (called on bot startup):
   - Read `data/queue.json` → parse JSON → extract `songs` array
   - Return list of song dicts (each: query, username, channel_id, request_id, added_at)
   - On error/missing file: return empty list
3. **save(songs)** (called after every queue mutation):
   - Acquire `_save_lock` (asyncio.Lock for serialization)
   - Write to `data/queue.json.tmp` with metadata (version, last_updated)
   - Atomic rename: `.tmp` → `.json` (os.replace)
   - On error: cleanup temp file, return False
4. **backup()**: Copy current queue.json to queue.bak

### SongRequestPersistence
1. **validate_song_exists(query, username)**: Check if expected file exists in downloads/
   - Sanitize query → build expected path → check for .mp3/.m4a/.webm extensions
   - Used for verifying restored songs still exist on disk

### Integration with SongRequestBot
- **_persist_queue()**: `get_all_items()` from RequestQueue → serialize to dicts → `queue_persistence.save()`
- **_load_persisted_queue()**: `queue_persistence.load()` → create SongRequest objects → `put_nowait()` into queue

## Dependencies
- External: `json`, `pathlib`, `asyncio`, `shutil` (backup)
- Internal: Called from SongRequestBot; data read/written in `data/queue.json`
- Data file: `data/queue.json` (gitignored), `data/queue.json.bak`
