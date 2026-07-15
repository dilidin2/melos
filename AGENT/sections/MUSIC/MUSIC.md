# MUSIC - Data Flow Documentation

**Commit**: `f2f4f10 fix: make !repeat_off actually disable repeat mode`
**Last updated**: 2026-07-15

## Section Overview
YouTube search & download pipeline, audio playback via Pygame, and music-related commands (volume, pause, repeat, vote-to-skip).

## Files in this Section
- `main/music_downloader.py` - YouTube search, validation, download via yt-dlp
- `main/audio_player.py` - Audio playback via Pygame mixer
- `commands/music.py` - Music control command handlers

## Data Flow Map for Each File

### music_downloader.py
1. **Input**: Query string or YouTube URL
2. **Transformation**:
   - If local file path → return directly (used by `!random`)
   - Search YouTube with up to 10 candidates via `ytsearchN:query`
   - Validate each candidate: category must be "Music", duration ≤ 900s
   - Check if file already exists on disk by title match
   - Download in background thread (10min timeout); extract audio to MP3 at 192kbps via FFmpeg
   - Fallback path resolution: postprocessor_hook → title search → polling loop
3. **Output**: File path string or `None` / raised exception (`_SongTooLongError`, `_CategoryError`, `_NoValidCandidateError`)
4. **Error Handling**: Tries next candidate on rejection; logs rejection reasons; re-raises with descriptive messages

### audio_player.py
1. **Input**: File path to MP3 file
2. **Transformation**: `pygame.mixer.music.load()` → `play()` → blocks until done or stopped
3. **Output**: `True` on success, `False` on error/stop
4. **Error Handling**: File not found returns `False`; exceptions logged

### commands/music.py
1. **Input**: Command parameters from `CommandProcessor`
2. **Transformation**: Delegates to bot services (audio_player, request_queue, music_downloader)
3. **Output**: Response strings for chat
4. **Key methods**: `cmd_pause`, `cmd_resume`, `cmd_repeat`/`cmd_repeat_off`, `cmd_volume`, `cmd_next`, `cmd_random`, `cmd_duration`, `cmd_vote`, `cmd_when`

## Dependencies
- External: `yt-dlp>=2026.3.17`, `pygame>=2.5.0`, `numpy`, `soundfile`, `ffmpeg` (system)
- Internal: Called from `main_core.py` (`_queue_processor`), depends on `config.py` constants
