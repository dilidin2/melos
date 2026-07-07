# DOWNLOAD - Data Flow Documentation

**Commit**: `7d0e5d5`
**Last updated**: `2026-07-07`

## Section Overview
Downloaded audio files. This directory is populated by MusicDownloader and consumed by AudioPlayer. Files are NOT tracked in git (gitignore).

## Data Flow for Each File

### downloads/ (directory)
1. **Input**: Song query from user (`!sr <song>`) or random mode selection
2. **Transformation**:
   - yt-dlp downloads audio stream, converts to MP3 via FFmpegExtractAudio postprocessor
   - Quality: 192kbps (configurable in config.py AUDIO_QUALITY)
   - Format: mp3 (configurable in config.py AUDIO_FORMAT)
   - File naming: `{title}.mp3` (title sanitized of special chars, max 100 chars)
3. **Output**: MP3 file in `downloads/` directory
4. **Consumption**: AudioPlayer reads the file path returned by MusicDownloader.download()

## Duplicate Detection
- **In-memory** (`DuplicateCache`, main_core.py): LRU cache keyed by query string (100 entries max). On duplicate request, returns cached file path without re-downloading.
- **On-disk** (`MusicDownloader.download()`): After search, checks if `downloads/{title}.mp3` exists before downloading.

## Random Playback
When queue is empty, `_queue_processor()` scans `downloads/` for .mp3/.wav/.m4a files and plays one randomly. Avoids consecutive repetition via `last_random_song` tracking.

## Configuration
- Directory: `DOWNLOAD_DIR` (config.py) = `./downloads` (env var override)
- Max song duration: `MAX_DURATION_SECONDS` = 900 (15 min)
- Audio quality: `AUDIO_QUALITY` = 192 kbps
- Format: `AUDIO_FORMAT` = "mp3"
