# COMMANDS - Data Flow Documentation

**Commit**: `7d0e5d5`
**Last updated**: `2026-07-07`

## Section Overview
All chat command handlers. Each file maps to a responsibility group: music playback, playlists, admin, analytics, utilities.

## Files in this Section
- `commands/music.py` - Playback control (pause/resume/repeat/vote/next/random/duration/etc.)
- `commands/playlists.py` - Playlist CRUD commands
- `commands/admin.py` - Admin commands (blacklist/skip/clear_queue/volume)
- `commands/analytics.py` - Stats commands (stats/top_songs/top_users/history)
- `commands/utility.py` - Utility commands (help/version/uptime/queue_info)

## Data Flow Map for Each File

### music.py
**Dependencies**: AudioPlayer, RequestQueue, MusicDownloader, SongRequestBot
- `cmd_pause()` → `audio_player.pause()`
- `cmd_resume()` → `audio_player.resume()`
- `cmd_repeat(count)` → updates bot.repeat_mode + repeat_remaining/repeat_count
- `cmd_next()` → gets next item from queue via `_request_queue.get_items(1)`
- `cmd_queue_info()` → calculates estimated duration from all items (4min avg if no info)
- `cmd_duration(query)` → calls `music_downloader.get_song_info(query)` for title+duration
- `cmd_at(position)` → gets item at position N, shows its duration
- `cmd_when(username)` → finds user's next song in queue, estimates time (4min/song avg)
- `cmd_random(N)` → creates SongRequest objects with local file paths, adds to queue
- `cmd_ops(username)` → removes user's last queued song from asyncio.Queue._queue
- `cmd_vote(username)` → calls `bot.process_vote(username)`; if 3 voters reached, stops playback

### playlists.py
**Dependencies**: PlaylistManager, RequestQueue, SongRequestBot
- `cmd_create()` → `playlist_manager.create_playlist()`
- `cmd_playlist(name?, page?)` → shows user's playlists or songs within a playlist (8 per page)
- `cmd_add(playlist, query)` → adds current song to playlist (file_path="unknown" — needs fixing for !add)
- `cmd_remove(playlist, index_or_name)` → removes by index or title substring match
- `cmd_move(playlist, pos1, pos2)` → swaps two songs in playlist
- `cmd_clear(playlist)` → clears all songs from playlist
- `cmd_list_playlists()` → shows all playlists for user
- `cmd_pump(playlist?, n=5)` → sliding-window random selection (excludes recently-pumped), adds to queue

### admin.py
**Dependencies**: AdminHandler, AudioPlayer, RequestQueue, SongRequestBot
- **Permission check**: username must be in ADMIN_USERS env var
- `cmd_blacklist(target)` → `admin_handler.add_blacklist()`
- `cmd_unblacklist(target)` → `admin_handler.remove_blacklist()`
- `cmd_blacklist_list()` → returns blacklist users
- `cmd_skip()` → `audio_player.stop()` (only for admins)
- `cmd_remove_queue(position)` → rebuilds asyncio.Queue without the item at position
- `cmd_volume(level)` → sets pygame.mixer.music.set_volume(level/100.0)
- `cmd_clear_queue()` → rebuilds empty asyncio.Queue, clears all songs

### analytics.py
**Dependencies**: Analytics
- `cmd_stats()` → shows total requests/plays + today + week stats
- `cmd_top_songs(n=10)` → returns top N by request count
- `cmd_top_users(n=10)` → returns top N users by request count
- `cmd_history(n=10)` → returns last N plays with timestamps

### utility.py
**Dependencies**: RequestQueue, MusicDownloader
- `cmd_help(command?)` → 3-page help or single command help
- `cmd_version()` → shows bot version (1.1.0)
- `cmd_uptime()` → shows uptime string
- `cmd_queue_info()` → shows next 5 songs with duration estimates

## Dependencies
- External: `twitchAPI`, `yt-dlp`, `pygame`, `soundfile`, `numpy`, `python-dotenv`, `loguru` (from pyproject.toml)
- Internal: All command handlers depend on `services.py` DI container for access to core services
