# TWITCH - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Twitch IRC connection management via twitchAPI library. Handles OAuth authentication using **Device Code Flow (DCF)** — no client secret required. Tokens are cached in `tokens.json` and auto-refreshed on expiry. Chat connection, command registration, and message routing. All registered commands route to either `_handle_sr_command` (!sr → music queue) or `_handle_other_command` (everything else → CommandProcessor).

## Files in this Section
- `main/twitch_handler.py` — TwitchHandler: connection, DCF OAuth, command registration, message handling
- `main/chat_message.py` — ChatMessage: formatted message sending (error, notification, now-playing, public)

## Data Flow Map

### TwitchHandler — Connection Flow
1. **Init**: Create patterns for !sr command; store optional command_processor reference
2. **connect()**:
   - Initialize `Twitch(app_id=client_id, app_secret="", authenticate_app=False)` — no client secret needed
   - Register `_on_token_refresh` callback on `twitch.user_auth_refresh_callback` **before** any auth call
   - Load tokens from `tokens.json` or do fresh DCF login via `_do_fresh_login()`
   - Create `Chat(twitch)` instance
   - Register events: READY → join TARGET_CHANNEL, MESSAGE → `_handle_message` (non-command messages only)
   - Register commands: `!sr` → `_handle_sr_command`, all others → `_handle_other_command`
   - Start chat connection

### Device Code Flow (DCF) OAuth
The DCF replaces the old `UserAuthenticator` flow. It requires **no client secret** and works headless (no browser needed).

1. **`_get_device_code(scopes)`**: POST to `https://id.twitch.tv/oauth2/device` → returns `device_code`, `user_code`, `verification_uri`, `expires_in`, `interval`
2. **User action**: User opens `verification_uri` in browser and enters `user_code`
3. **`_poll_for_token(device_code, interval, scopes)`**: Polls `https://id.twitch.tv/oauth2/token` with grant_type `urn:ietf:params:oauth:grant-type:device_code`
   - `authorization_pending` → keep polling
   - `slow_down` → increase poll interval by 5s
   - `expired_token` → raise TimeoutError
   - `access_denied` → raise RuntimeError
   - success (200) → return `(access_token, refresh_token)`
4. **`_do_device_auth(scopes)`**: Orchestrates steps 1-3 (blocking until user authorizes)
5. **`_do_fresh_login(scopes)`**: Calls `_do_device_auth()`, saves tokens to `tokens.json`, sets authentication on Twitch instance

### Token Refresh
When twitchAPI automatically refreshes an expiring token (~4h lifetime), the `_on_token_refresh(token, refresh_token)` callback is invoked and persists the new tokens to `tokens.json`. This prevents silent expiry.

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
- External: `twitchAPI` (Twitch, Chat, AuthScope), `aiohttp` (DCF HTTP calls), `json`, `asyncio`, `pathlib`
- Internal: Called from SongRequestBot; command_callback set to SongRequestBot._handle_song_request
- Data files: `tokens.json` (OAuth tokens, gitignored)
