# CORE - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
The core module is the heart of the bot. It contains the main event loop (`SongRequestBot`), the request queue (`RequestQueue`), and the duplicate cache (`DuplicateCache`). All music requests flow through this module before being processed by the downloader and audio player.

## Files in this Section
- `main/main_core.py` — SongRequestBot, RequestQueue, DuplicateCache, SongRequest dataclass

## Data Flow Map

### SongRequest (dataclass)
1. **Created** when a user types `!sr <query>` in chat
2. **Fields**: query, username, channel_id, request_id, added_at, resolved_title, resolved_duration
3. **Used by**: RequestQueue.put(), analytics tracking, persistence

### RequestQueue
1. **Input**: SongRequest objects via `put()` (async)
2. **Internal**: asyncio.Queue with in-place mutation (no reference swap) + `_lock` for thread safety at await boundaries
3. **Operations**:
   - `get()` — Returns next request (with 1s timeout)
   - `get_items(N)` — Peek at next N items without removal
   - `clear()` / `remove_by_index()` — Admin queue manipulation (lock-protected, in-place)
   - `get_all_items()` — Read all for persistence
4. **Output**: SongRequest objects consumed by `_queue_processor`

### DuplicateCache
1. **Input**: query → (file_path, username) pairs via `add()`
2. **Internal**: LRU dict (max 100 entries), key = lowercase query
3. **Output**: Cached file path on hit, None on miss
4. **Used by**: `_process_request()` to skip re-downloading

### SongRequestBot — Main Event Loop
1. **Startup** (`run()`):
   - Connect to Twitch via `TwitchHandler.connect()`
   - Load persisted queue from `data/queue.json`
   - Start `_queue_processor` as asyncio task
2. **Song Request Flow** (`_handle_song_request`):
   - Check blacklist → reject if blacklisted
   - Record analytics (if available)
   - Create SongRequest → put in RequestQueue
   - Send confirmation message to chat
   - Persist queue to disk
   - Clear shutdown event (keep bot alive)
3. **Queue Processor** (`_queue_processor`):
   - Loop: `get()` from queue → `_process_request(request)` → `task_done()`
   - **Repeat mode**: Inner while loop replays same request based on `repeat_mode` ('off'/'count'/'infinite')
   - **Random fallback**: When queue is empty, picks random file from `downloads/` and plays it
   - **Shutdown drain**: On shutdown signal, drains remaining queue items
4. **Process Request** (`_process_request`):
   - Check `_processing_lock` + `_in_progress` flag (single-threaded processing)
   - Check DuplicateCache → use cached file or call `MusicDownloader.download()`
   - On download: handle exceptions (_SongTooLongError, _CategoryError, _NoValidCandidateError)
   - Resolve metadata (title, duration from local file via ffprobe)
   - Reset vote tracking → enable votes for new song
   - Call `_play_audio_file()` → Pygame playback in executor thread
   - Record analytics on success
5. **Playback** (`_play_audio_file`):
   - Send "Now Playing" message to chat
   - Run `AudioPlayer.play()` in ThreadPoolExecutor (blocking call)
   - Handle playback errors → send error message to chat
6. **Vote-to-Skip**:
   - `process_vote(username)` — Add voter, return True if threshold (3) reached
   - `reset_votes()` — Clear on new song start or skip
7. **Shutdown** (`shutdown()`):
   - Set `_shutdown_event` → queue processor drains remaining items
   - Stop audio player → cancel queue task → persist queue
   - Disconnect Twitch → shutdown executor

## Dependencies
- External: `pygame` (audio), `yt_dlp` (via MusicDownloader), `loguru` (logging)
- Internal: Called from `run.py`; calls `TwitchHandler`, `AudioPlayer`, `MusicDownloader`, `ChatMessage`, `QueuePersistence`, `AdminHandler`, `Analytics`
