# COMMANDS - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Command routing and handling. The `CommandProcessor` uses precompiled regex patterns to match chat messages to handler methods. Permission checks use the `@admin_required` decorator (discovered dynamically). All handler logic is delegated to domain-specific command classes via the `CommandServices` DI container.

## Files in this Section
- `main/command_processor.py` — Regex-based command router, permission enforcement, response sending
- `main/services.py` — CommandServices DI container (dataclass with build() factory)
- `commands/__init__.py` — `@admin_required` decorator (sets `_requires_admin = True`)
- `commands/music.py` — Music control: !pause, !resume, !volume, !repeat*, !next, !random, !ops, !vote
- `commands/playlists.py` — Playlist management: !create, !playlist, !add, !remove, !move, !clear, !pump
- `commands/admin.py` — Admin commands: !blacklist, !unblacklist, !skip, !remove_queue, !clear_queue
- `commands/analytics.py` — Stats commands: !stats, !top_songs, !top_users, !history
- `commands/utility.py` — Utility commands: !help, !version, !uptime, !queue_info

## Data Flow Map

### CommandProcessor — Routing Pipeline
1. **Input**: Raw chat message text + username + channel_id (from TwitchHandler)
2. **Pattern matching** (loop through compiled regexes):
   - `text.lower().strip()` matched against each `CompiledPattern.regex`
   - On match: extract method name + captured groups
3. **Permission check**: If method in `_admin_methods` set (built from `@admin_required` decorated methods) → verify user is in ADMIN_USERS list
4. **Dispatch**: Call `method(*captured_groups, username, channel_id)` via getattr
5. **Response**: Send return value to chat via `_send_response()` (handles single string or list with rate limiting)
6. **Error handling**: Log traceback, send error message to chat

### Admin Method Discovery (`_build_admin_set`)
- Scans all `cmd_*` methods on the instance
- Checks for `_requires_admin` attribute (set by `@admin_required` decorator)
- Builds a set of method names → O(1) lookup at dispatch time

### Response Sending
- Single string → send immediately
- List of strings → send with 1.5s delay between messages (rate limiting)
- All via `bot.chat_message.send_public(channel_id, message)`

### DI Container — CommandServices
- **Build** (`run.py`): Instantiate all services and command handlers with explicit dependencies
- **Inject**: Pass to CommandProcessor constructor
- **Access**: Handlers delegate to `self.services.xxx.method()` (e.g., `self.services.music_commands.cmd_pause(username)`)

### Command Handler Classes
Each class has explicit constructor dependencies:
- **MusicCommands**: AudioPlayer, RequestQueue, MusicDownloader, bot reference
- **PlaylistCommands**: PlaylistManager, RequestQueue, bot
- **AdminCommands**: AdminHandler, AudioPlayer, RequestQueue, bot
- **AnalyticsCommands**: Analytics
- **UtilityCommands**: RequestQueue, MusicDownloader, bot_version

## Dependencies
- External: `re` (regex), `asyncio`, `time`
- Internal: All command handlers depend on services from `main/`; CommandProcessor depends on CommandServices
