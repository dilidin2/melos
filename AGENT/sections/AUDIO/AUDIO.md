# AUDIO - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Audio playback via Pygame mixer. Handles playing, pausing, resuming, and stopping audio files. Thread-safe operations using threading.Event for stop signaling.

## Files in this Section
- `main/audio_player.py` — AudioPlayer class (Pygame mixer wrapper)

## Data Flow Map

### AudioPlayer
1. **Init**: `pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)`
2. **play(filepath)**:
   - **Input**: File path to audio file (.mp3, .wav, .m4a)
   - **Validation**: Check file exists on disk
   - **Playback**: `pygame.mixer.music.load()` → `music.play()`
   - **Blocking loop**: Polls `get_busy()` every 100ms until done or stopped
   - **Stop signal**: `_stop_event` threading.Event checked each iteration
   - **Output**: True on completion, False on stop/error
3. **pause()**: `pygame.mixer.music.pause()` (only if playing and not already paused)
4. **resume()**: `pygame.mixer.music.unpause()` (only if paused)
5. **stop()**: Set `_stop_event` + `pygame.mixer.music.stop()` → reset all flags
6. **is_playing()** / **is_paused()**: State queries

### Thread Safety
- `_stop_event` is a `threading.Event` — safe across threads (called from main asyncio thread via `skip_current_song()`)
- Playback runs in `ThreadPoolExecutor` (from SongRequestBot) so it doesn't block the event loop
- Volume (`pygame.mixer.music.set_volume()`) is set directly by admin commands

## Dependencies
- External: `pygame` (mixer module)
- Internal: Called from `SongRequestBot._play_audio_file()`; volume/pause/resume called via command handlers
