# TWITCH - Data Flow Documentation

**Commit**: `f2f4f10 fix: make !repeat_off actually disable repeat mode`
**Last updated**: 2026-07-15

## Section Overview
Twitch chat connection, OAuth authentication flow, and regex-based command routing.

## Files in this Section
- `main/twitch_handler.py` - Twitch connection, OAuth, message dispatch
- `main/command_processor.py` - Regex matching + permission checks + cmd_* method dispatch

## Data Flow Map for Each File

### twitch_handler.py
1. **Input**: Chat messages from Twitch IRC (via `twitchAPI`)
2. **Transformation**:
   - OAuth: reads `tokens.json`; if missing/invalid, triggers browser login via `UserAuthenticator`
   - Registers each command name with `Chat.register_command()` — `!sr` goes to `_handle_sr_command`, all others go to `_handle_other_command`
3. **Output**:
   - `!sr <query>` → calls `command_callback(query, username, channel_id)` → routes to bot's queue
   - Other commands → calls `command_processor.process(text, username, channel_id)`
4. **Error Handling**: Connection failures logged; auth errors trigger re-login

### command_processor.py
1. **Input**: Raw chat text (e.g., `!volume 50`), username, channel_id
2. **Transformation**:
   - Matches against ~35 compiled regex patterns (case-insensitive)
   - Checks `@admin_required` decorator on method; rejects non-admin users
   - Extracts capture groups as arguments, appends `(username, channel_id)`
   - Delegates to corresponding `cmd_*` method via DI container
3. **Output**: Response string(s) sent to chat with 1.5s rate-limit delay between messages
4. **Error Handling**: Exceptions logged; generic error message sent to user

## Dependencies
- External: `twitchAPI>=4.5.0`, `re` (stdlib), `loguru`
- Internal: Depends on `CommandServices` (DI container), all command handler classes in `commands/`
