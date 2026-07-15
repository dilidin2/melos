# ANALYTICS - Data Flow Documentation

**Commit**: `f2f4f10 fix: make !repeat_off actually disable repeat mode`
**Last updated**: 2026-07-15

## Section Overview
Statistics tracking (requests, plays, top songs/users) with persistent JSON storage.

## Files in this Section
- `main/analytics.py` - Analytics engine with disk persistence
- `commands/analytics.py` - Analytics command handlers

## Data Flow Map for Each File

### analytics.py
1. **Input**: `(username, query)` from song requests and plays
2. **Transformation**:
   - Loads from `data/stats.json` on init; resets on corrupt file
   - `record_request()`: increments total_requests, per-user count, per-title count → saves to disk
   - `record_play()`: increments total_plays, appends to play_history (max 1000 entries) → saves to disk
   - Aggregations: `get_top_songs(N)`, `get_top_users(N)`, `get_stats_today/week/month()`, `get_play_history(N)`
3. **Output**: Dicts with counts, lists of top items, history records
4. **Error Handling**: JSON decode errors trigger full reset; missing file treated as fresh start

### commands/analytics.py
1. **Input**: Command parameters from `CommandProcessor`
2. **Transformation**: Calls `Analytics` methods, formats results with emojis and pagination
3. **Output**: Response strings for chat
4. **Key methods**: `cmd_stats`, `cmd_top_songs`, `cmd_top_users`, `cmd_history`

## Dependencies
- External: `json` (stdlib), `datetime` (stdlib)
- Internal: Called from `main_core.py` (`_handle_song_request`, `_process_request`) — attached dynamically via `hasattr(self, "analytics")`
