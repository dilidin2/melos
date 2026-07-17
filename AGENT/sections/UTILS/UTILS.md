# UTILS - Data Flow Documentation

**Commit**: `8fdc2aa feat: improve local file matching, volume command, playlist fixes`
**Last updated**: 2025-07-17

## Section Overview
Shared utilities. Currently only contains the logging setup module using Loguru.

## Files in this Section
- `utils/logger.py` — Loguru configuration (console + file handlers)
- `utils/__init__.py` — Empty package marker

## Data Flow Map

### setup_logger()
1. **Input**: log_file path, level, rotation size, retention period
2. **Process**:
   - Remove default Loguru handler
   - Add console handler: colored output to stderr, format with timestamp/level/name/function/line, `enqueue=True` (thread-safe)
   - Add file handler: plain text to log_file, rotation at 10MB, retention 30 days, zip compression, `enqueue=True`
3. **Output**: Configured logger instance (global via Loguru's singleton pattern)
4. **Called from**: `run.py` at startup (before any bot initialization)

## Dependencies
- External: `loguru`, `sys`, `pathlib`
- Internal: Used by all modules via `from loguru import logger`
