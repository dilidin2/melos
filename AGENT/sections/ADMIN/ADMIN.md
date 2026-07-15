# ADMIN - Data Flow Documentation

**Commit**: `f2f4f10 fix: make !repeat_off actually disable repeat mode`
**Last updated**: 2026-07-15

## Section Overview
User moderation (blacklist/whitelist) and admin-only commands with permission enforcement.

## Files in this Section
- `main/admin_handler.py` - Blacklist/whitelist persistence
- `commands/admin.py` - Admin command handlers

## Data Flow Map for Each File

### admin_handler.py
1. **Input**: Username to add/remove from blacklist or whitelist
2. **Transformation**:
   - Loads from `data/blacklist.json` and `data/whitelist.json` on init
   - Case-insensitive matching (stores lowercase)
   - Saves immediately after each mutation
3. **Output**: Boolean success, list of blacklisted/whitelisted users
4. **Error Handling**: Corrupt JSON files silently reset; missing files treated as empty

### commands/admin.py
1. **Input**: Command parameters from `CommandProcessor`
2. **Transformation**: All methods decorated with `@admin_required` — permission checked in `CommandProcessor._build_admin_set()` at runtime
3. **Output**: Response strings for chat
4. **Key methods**: `cmd_blacklist`, `cmd_unblacklist`, `cmd_blacklist_list`, `cmd_skip`, `cmd_remove_queue`, `cmd_clear_queue`

## Dependencies
- External: `json` (stdlib)
- Internal: Depends on `AdminHandler`, `AudioPlayer`, `RequestQueue`; permission decorator checked by `CommandProcessor`
