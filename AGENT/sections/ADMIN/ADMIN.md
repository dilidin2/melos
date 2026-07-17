# ADMIN - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
User moderation (blacklist/whitelist), YouTube trusted channel whitelist, and admin command handlers. Blacklisted users are blocked from requesting songs (checked in SongRequestBot._handle_song_request). The trusted channels feature restricts downloads to videos from whitelisted YouTube channels (opt-in via CHANNEL_WHITELIST_ENABLED). Admin commands require the user to be in ADMIN_USERS config list, enforced by `@admin_required` decorator + CommandProcessor permission check.

## Files in this Section
- `main/admin_handler.py` — AdminHandler: blacklist/whitelist CRUD + trusted channels with JSON persistence
- `commands/admin.py` — AdminCommands: !blacklist, !unblacklist, !blacklist_list, !trust_channel, !untrust_channel, !trusted_channels, !skip, !remove_queue, !clear_queue, !volume

## Data Flow Map

### AdminHandler — Blacklist/Whitelist/Trusted Channels Management
1. **Init**: Load `data/blacklist.json`, `data/whitelist.json`, `data/trusted_channels.json` → parse to sets/dict
2. **add_blacklist(username)**: Add lowercase username to set → save JSON
3. **remove_blacklist(username)**: Remove from set → save JSON
4. **is_blacklisted(username)**: Case-insensitive lookup in set
5. **get_blacklist_list()**: Return list of blacklisted usernames
6. **Persistence**: Atomic JSON write on every mutation

### AdminHandler — Trusted Channels (YouTube channel whitelist)
1. **_trusted_channels**: dict[str, str] mapping channel_id → readable name
2. **add_trusted_channel(channel_id, channel_name)**: Add to dict → save `data/trusted_channels.json`
3. **remove_trusted_channel(channel_id)**: Remove from dict → save JSON
4. **is_trusted_channel(channel_id)**: Case-sensitive lookup in dict keys
5. **get_trusted_channels()**: Return copy of the dict
6. **JSON schema**: `{"channels": {"UCxxxx": "Channel Name", ...}}`

### Blacklist Enforcement (in SongRequestBot)
1. On `!sr <query>`: Check `admin_handler.is_blacklisted(username)` → reject with message if blacklisted
2. Whitelist is loaded but NOT enforced in current code (placeholder for future use)

### Admin Commands (commands/admin.py)
- **cmd_blacklist/unblacklist**: Delegate to AdminHandler → return status message
- **cmd_blacklist_list**: Get list from AdminHandler → format as bullet list
- **cmd_trust_channel(query_or_url)**: Resolve channel via `music_downloader.resolve_channel_from_query()` → add to AdminHandler
- **cmd_untrust_channel(channel_id)**: Remove from AdminHandler by channel_id
- **cmd_trusted_channels_list**: Get dict from AdminHandler → format as bullet list with names and IDs
- **cmd_skip**: Call `audio_player.stop()` → trigger next song in queue processor
- **cmd_remove_queue**: `request_queue.remove_by_index(pos - 1)` → persist queue
- **cmd_clear_queue**: `request_queue.clear()` → persist queue
- **cmd_volume**: `pygame.mixer.music.set_volume(level / 100.0)`

## Dependencies
- External: `json`, `pathlib`
- Internal: Called from SongRequestBot (blacklist check), MusicDownloader (channel whitelist check), CommandProcessor (admin commands)
- Data files: `data/blacklist.json`, `data/whitelist.json`, `data/trusted_channels.json`
