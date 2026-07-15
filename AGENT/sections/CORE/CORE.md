# CORE - Data Flow Documentation

**Commit**: `f2f4f10 fix: make !repeat_off actually disable repeat mode`
**Last updated**: 2026-07-15

## Section Overview
Core bot lifecycle, request queue management, duplicate caching, dependency injection, and persistent queue storage.

## Files in this Section
- `main/main_core.py` - SongRequestBot (lifecycle), RequestQueue, DuplicateCache
- `main/config.py` - All configuration constants loaded from .env
- `main/services.py` - CommandServices DI container
- `main/queue_persistence.py` - Atomic queue save/load to JSON
- `main/chat_message.py` - Chat message formatting utilities

## Data Flow Map for Each File

### main_core.py
1. **Input**: Song request from Twitch chat (`!sr <query>`, username, channel_id)
2. **Transformation**:
   - Check blacklist → reject if blacklisted
   - Create `SongRequest` with unique ID and add to `RequestQueue` (asyncio.Queue)
   - Record analytics event
   - Persist queue to disk via `QueuePersistence`
3. **Output**: Confirmation message sent to chat
4. **Queue Processor** (`_queue_processor`):
   - Pops from `RequestQueue`, checks duplicate cache
   - If not cached: calls `MusicDownloader.download()`
   - Plays via `AudioPlayer.play()` in thread pool executor
   - Handles repeat modes (off/count/infinite) in inner while loop
   - On empty queue: picks random song from `downloads/` avoiding consecutive repeats
5. **Error Handling**: Download failures, playback errors, and validation errors all send chat notifications

### config.py
1. **Input**: `.env` file + environment variables
2. **Transformation**: Loads via `load_dotenv()`; parses `ADMIN_USERS` as comma-separated list
3. **Output**: Module-level constants (`TWITCH_CLIENT_ID`, `MAX_DURATION_SECONDS=900`, `VOTE_REQUIRED_COUNT=3`, etc.)
4. **Error Handling**: Defaults provided for all values; empty strings if env var missing

### services.py
1. **Input**: Initialized components (bot, handlers, managers)
2. **Transformation**: `CommandServices.build()` packages all into a single dataclass
3. **Output**: DI container injected into `CommandProcessor`
4. **Error Handling**: None — relies on caller passing valid instances

### queue_persistence.py
1. **Input**: List of `SongRequest` dicts from runtime queue
2. **Transformation**: Writes to temp file then atomic rename (`data/queue.json`)
3. **Output**: JSON with `{version, last_updated, songs: [...]}`
4. **Error Handling**: Lock prevents concurrent writes; temp file cleaned up on failure

### chat_message.py
1. **Input**: Message text, channel_id, optional username
2. **Transformation**: Formats messages (now-playing, error, public) via `TwitchHandler`
3. **Output**: Sent to Twitch chat
4. **Error Handling**: Errors logged, no crash propagation

## Dependencies
- External: `loguru`, `python-dotenv`, `asyncio` (stdlib)
- Internal: Called from `twitch_handler.py` (message routing), `command_processor.py` (DI access)
