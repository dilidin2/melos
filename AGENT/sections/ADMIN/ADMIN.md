# ADMIN - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
User moderation (blacklist/whitelist) and admin command handlers. Blacklisted users are blocked from requesting songs (checked in SongRequestBot._handle_song_request). Admin commands require the user to be in ADMIN_USERS config list, enforced by `@admin_required` decorator + CommandProcessor permission check.

## Files in this Section
- `main/admin_handler.py` — AdminHandler: blacklist/whitelist CRUD with JSON persistence
- `commands/admin.py` — AdminCommands: !blacklist, !unblacklist, !blacklist_list, !skip, !remove_queue, !clear_queue, !volume

## Data Flow Map

### AdminHandler — Blacklist/Whitelist Management
1. **Init**: Load `data/blacklist.json` and `data/whitelist.json` → parse to sets
2. **add_blacklist(username)**: Add lowercase username to set → save JSON
3. **remove_blacklist(username)**: Remove from set → save JSON
4. **is_blacklisted(username)**: Case-insensitive lookup in set
5. **get_blacklist_list()**: Return list of blacklisted usernames
6. **Persistence**: Atomic JSON write on every mutation

### Blacklist Enforcement (in SongRequestBot)
1. On `!sr <query>`: Check `admin_handler.is_blacklisted(username)` → reject with message if blacklisted
2. Whitelist is loaded but NOT enforced in current code (placeholder for future use)

### Admin Commands (commands/admin.py)
- **cmd_blacklist/unblacklist**: Delegate to AdminHandler → return status message
- **cmd_blacklist_list**: Get list from AdminHandler → format as bullet list
- **cmd_skip**: Call `audio_player.stop()` → trigger next song in queue processor
- **cmd_remove_queue**: `request_queue.remove_by_index(pos - 1)` → persist queue
- **cmd_clear_queue**: `request_queue.clear()` → persist queue
- **cmd_volume**: `pygame.mixer.music.set_volume(level / 100.0)`

## Dependencies
- External: `json`, `pathlib`
- Internal: Called from SongRequestBot (blacklist check), CommandProcessor (admin commands)
- Data files: `data/blacklist.json`, `data/whitelist.json`
