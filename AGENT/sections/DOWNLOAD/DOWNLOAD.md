# DOWNLOAD - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Handles music downloading from YouTube via yt-dlp. Validates songs by duration (max 15 min) and category (Music only). Supports local file matching to avoid unnecessary downloads. Downloads are threaded with postprocessor hooks for reliable path capture.

## Files in this Section
- `main/music_downloader.py` — MusicDownloader class, custom exceptions (_SongTooLongError, _CategoryError, _NoValidCandidateError)

## Data Flow Map

### download(query_or_url) — Primary Entry Point
1. **Input**: Song query string, YouTube URL, or file path
2. **Local file check** (fast path):
   - If `os.path.isfile(query)` → return directly (used by !random with full paths)
   - `_find_matching_file(query)` → word-boundary regex match on disk filenames
3. **YouTube search** (if not URL):
   - `_search_youtube_candidates_with_info(query, max_results=10)` → returns [(url, info), ...] pairs
   - Info is pre-fetched from ytsearch results (includes duration)
4. **Candidate validation loop**:
   - For each candidate: use prefetched info or `_extract_info(url)` for direct URLs
   - `_validate_song(info)` checks:
     - Duration ≤ 900s (15 min) → raises _SongTooLongError if all exceed
     - Category contains "music" → raises _CategoryError if wrong category
   - On first valid candidate: proceed to download
5. **Disk existence check**: Compare YouTube title with existing files (exact match, not fuzzy)
6. **Download execution** (threaded):
   - `yt_dlp.YoutubeDL(opts).download([url])` in daemon thread (10 min timeout)
   - `postprocessor_hooks` captures final file path after FFmpeg conversion
7. **Fallback chain**: postprocessor path → title-based search → 5s wait polling → error
8. **Output**: File path string or None on failure

### _find_matching_file(query) — Local File Matching
1. **Input**: Query string (e.g., "Bohemian Rhapsody")
2. **Process**: List `downloads/` → filter by audio extensions → word-boundary regex (`\bword\b`) match on filename without extension
3. **Strictness**: ALL query words must match as whole words (avoids false positives like "ft" matching any file)
4. **Output**: Full file path or None

### _get_local_file_duration(file_path) — Duration Extraction
1. **Input**: Path to local audio file
2. **Process**: Run `ffprobe -show_entries format=duration` (5s timeout)
3. **Output**: Duration in seconds (int) or None on failure

### get_song_info(query_or_url) — Metadata Lookup
1. Local file match → ffprobe duration + filename as title
2. YouTube search → extract info via yt-dlp
3. **Output**: Dict with {title, duration, uploader}

## Dependencies
- External: `yt_dlp` (YouTube download/search), `ffprobe` (local duration), `subprocess`, `threading`
- Internal: Called from `SongRequestBot._process_request()`, command handlers (!duration, !random)
- Config: DOWNLOAD_DIR, MAX_DURATION_SECONDS, AUDIO_QUALITY, AUDIO_FORMAT, YOUTUBE_CATEGORY, DOWNLOAD_TIMEOUT
