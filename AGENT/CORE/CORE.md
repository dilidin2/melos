# CORE - Data Flow Documentation

**Commit**: `7d0e5d5`
**Last updated**: `2026-07-07`

## Section Overview
Core bot logic: queue processing, Twitch connection, music download, audio playback, and command routing.

## Files in this Section
- `main_core.py` - SongRequestBot, RequestQueue, DuplicateCache, _queue_processor
- `twitch_handler.py` - Twitch chat connection & command routing (twitchAPI)
- `music_downloader.py` - YouTube downloading via yt-dlp (Music category only, max 15min)
- `audio_player.py` - Audio playback via pygame.mixer.music
- `services.py` - DI container (CommandServices) replacing dynamic coupling
- `command_processor.py` - Regex-based command dispatch to cmd_* methods

## Data Flow Map for Each File

### main_core.py
**Entry Point**: `run.py` → `SongRequestBot()` → `bot.run()`

1. **Startup** (`run.main()`):
   - Create `SongRequestBot`, `PlaylistManager`, `Analytics`, `MusicDownloader`
   - Build `CommandServices` DI container with all components
   - Create `CommandProcessor(services)`
   - Set up signal handlers (SIGINT/SIGTERM) for clean shutdown

2. **Queue Processing** (`_queue_processor()`):
   - **Input**: Requests from `RequestQueue` or empty queue (random mode)
   - **Processing**:
     1. Check `_processing_lock` — if already processing, reject new requests
     2. Set `_in_progress = True`
     3. Check `DuplicateCache` for cached file by query
     4. If not cached: call `MusicDownloader.download(query)` in thread pool
   - **Download flow**: `download()` tries up to 10 yt-dlp candidates → validates category=Music + duration≤15min → downloads via threaded yt-dlp with postprocessor hook → returns file path
   - **Playback**: Call `AudioPlayer.play(file_path)` in executor thread
   - **Repeat logic** (inner while loop):
     - `repeat_mode='infinite'`: restart inner loop immediately (no new request)
     - `repeat_mode='count'`: decrement `repeat_remaining`, continue if >0
     - `repeat_mode='off'`: break, advance queue
   - **Random mode**: When queue is empty, pick random file from `downloads/` (avoiding consecutive repetition via `last_random_song`)

3. **Shutdown** (`shutdown()`):
   - Set `_shutdown_event`, stop audio, cancel queue task, persist queue to disk, disconnect Twitch

### twitch_handler.py
1. **Connection**: OAuth flow via `twitchAPI.UserAuthenticator` → tokens saved to `tokens.json`
2. **Command registration**: Each command registered with twitchAPI Chat (e.g., `!sr`, `!skip`)
3. **Message routing**:
   - `!sr <query>` → `_handle_sr_command()` → calls `self.command_callback(query, username, room_id)`
   - All other commands → `_handle_other_command()` → `self.command_processor.process(text, username, room_id)`
4. **Non-command messages** (no !) → discarded in `_handle_message()`

### music_downloader.py
1. **Download** (`download(query_or_url)`):
   - If query is a local file path → return directly
   - If URL → use only that; if text query → search up to 10 candidates via yt-dlp `ytsearch`
   - For each candidate: extract info → validate (Music category + duration≤900s)
   - Check disk for existing file matching video title
   - Download: deepcopy `_ydl_opts`, use `postprocessor_hook` to capture final path after FFmpeg conversion
   - Fallback 1: search by title in downloads/
   - Fallback 2: wait up to 5s for FFmpeg to finish writing

### audio_player.py
**Input**: File path (mp3/m4a/wav) from MusicDownloader or random mode
**Processing**: pygame.mixer.music.load() → play() → busy-wait while `get_busy()` or paused
**Output**: Audio played; `_stop_event` allows interrupting playback

### services.py
**Purpose**: DI container replacing dynamic coupling (`self.bot.xxx`) with explicit dependencies.
- All command handlers receive only the services they need via constructor injection
- `CommandServices.build()` assembles all components from initialized objects

### command_processor.py
1. **Initialization**: Build regex patterns for all 35+ commands; discover admin methods via `@admin_required` attribute
2. **Processing** (`process(text, username, channel_id)`):
   - Match text against each compiled regex pattern
   - If match: check admin permission (if required) → extract groups → append username + channel_id → call cmd_* method
   - Send response via `services.bot.chat_message.send_public()`
