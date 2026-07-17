# TESTS - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Pytest test suite covering all major components. Uses pytest-asyncio for async tests. Tests are organized by module/component with ~20 test files.

## Files in this Section
- `tests/conftest.py` — Shared fixtures and configuration
- `tests/__init__.py` — Package marker
- `tests/pyproject.toml` — Test-specific config (if any)
- `tests/test_admin_commands.py` — Admin command handler tests
- `tests/test_admin_handler.py` — Blacklist/whitelist management tests
- `tests/test_admin_permissions.py` — Permission enforcement tests
- `tests/test_analytics_commands.py` — Analytics command output tests
- `tests/test_analytics.py` — Stats recording/querying tests
- `tests/test_audio_player.py` — Playback control tests
- `tests/test_chat_message.py` — Message formatting tests
- `tests/test_command_processor.py` — Command routing/dispatch tests
- `tests/test_config.py` — Configuration loading tests
- `tests/test_logger.py` — Logging setup tests
- `tests/test_main_core.py` — SongRequestBot/RequestQueue tests
- `tests/test_music_commands.py` — Music command handler tests
- `tests/test_music_downloader.py` — Download/local matching tests
- `tests/test_playlist_commands.py` — Playlist command handler tests
- `tests/test_playlist_manager.py` — Playlist CRUD/pompa tests
- `tests/test_queue_persistence.py` — Queue save/load tests
- `tests/test_services.py` — DI container tests
- `tests/test_twitch_handler.py` — Twitch connection/command registration tests
- `tests/test_utility_commands.py` — Help/version/uptime tests

## Running Tests
```bash
cd /home/matteo/melos
python -m pytest           # Run all tests
python -m pytest -v       # Verbose output
python -m pytest tests/test_main_core.py  # Single module
python -m pytest -m "not slow"  # Exclude slow tests
python -m pytest -k "queue"     # Keyword filter
```

## Configuration (pyproject.toml)
- **asyncio_mode**: "auto" (no @pytest.mark.asyncio needed)
- **Markers**: slow, integration, unit
- **Default options**: `-v --tb=short`

## Dependencies
- External: `pytest`, `pytest-asyncio`
- Internal: Tests import from `main/` and `commands/` packages
