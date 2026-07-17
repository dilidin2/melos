# TWITCH - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Twitch IRC connection management via twitchAPI library. Handles OAuth authentication (with token caching), chat connection, and command registration. All registered commands route to either `_handle_sr_command` (!sr → music queue) or `_handle_other_command` (everything else → CommandProcessor).

## Files in this Section
- `main/twitch_handler.py` — TwitchHandler: connection, OAuth, command registration, message handling
- `main/chat_message.py` — ChatMessage: formatted message sending (error, notification, now-playing, public)

## Data Flow Map

### TwitchHandler — Connection Flow
1. **Init**: Create patterns for !sr command; store optional command_processor reference
2. **connect()**:
   - Initialize `Twitch(client_id, client_secret)`
   - Load tokens from `tokens.json` or do fresh OAuth login via `UserAuthenticator`
   - Create `Chat(twitch)` instance
   - Register events: READY → join TARGET_CHANNEL, MESSAGE → `_handle_message` (non-command messages only)
   - Register commands: `!sr` → `_handle_sr_command`, all others → `_handle_other_command`
   - Start chat connection
3. **OAuth Login** (`_do_fresh_login`):
   - UserAuthenticator opens browser for OAuth flow
   - Saves access_token + refresh_token to `tokens.json`
   - Sets authentication on Twitch instance

### Message Routing
- **!sr command** (`_handle_sr_command`): Extract query parameter → call `command_callback(query, username, room_id)` → routes to SongRequestBot._handle_song_request
- **Other commands** (`_handle_other_command`): Format as "!name [params]" → call `command_processor.process(text, username, room_id)`
- **Regular messages** (`_handle_message`): Ignored (early return if starts with `!`)

### Command Registration
All known commands are registered via `chat.register_command(name, handler)`:
- Music: sr, volume, pause, resume, repeat, repeat_off, next, queue_info, duration, when, random, ops
- Playlists: create, playlist, add, remove, move, clear, list_playlists, pump
- Admin: blacklist, unblacklist, blacklist_list, skip, remove_queue, clear_queue
- Analytics: stats, top_songs, top_users, history
- Utility: help, version, uptime
- Vote: vote

### ChatMessage — Message Formatting
1. **send_error(channel_id, username, message)**: `@{username} ❌ {message}` → send via TwitchHandler
2. **send_notification(channel_id, message)**: `🎵 {message}` → send
3. **send_now_playing(channel_id, title)**: `🎶 Now Playing: {title}` → send
4. **send_direct(channel_id, username, message)**: `@{username} {message}` → send
5. **send_public(channel_id, message)**: Raw message → send

### disconnect()
- Stop chat → close Twitch instance → reset `_connected` flag

## Dependencies
- External: `twitchAPI` (Twitch, Chat, UserAuthenticator, AuthScope), `json`, `asyncio`
- Internal: Called from SongRequestBot; command_callback set to SongRequestBot._handle_song_request
- Data files: `tokens.json` (OAuth tokens, gitignored)
