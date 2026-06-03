# -*- coding: utf-8 -*-
"""
Queue Persistence - Persistence of the request queue

Implements a hybrid persistence layer that:
- Keeps asyncio.Queue for runtime (performance + thread-safety)
- Adds a QueuePersistence layer for disk saving
- Guarantees atomicity with temp file + rename
- Preserves original added_at timestamps
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger


class QueuePersistence:
    """Persistence layer for the song queue."""

    def __init__(self, queue_file: str = "data/queue.json"):
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_lock = asyncio.Lock()

    async def load(self) -> List[Dict[str, Any]]:
        """Loads the queue from disk on startup."""
        if not self.queue_file.exists():
            logger.info("No queue file found, starting with empty queue")
            return []

        try:
            content = await asyncio.to_thread(self.queue_file.read_text)
            data = json.loads(content)
            songs = data.get("songs", [])
            logger.info(f"Loaded {len(songs)} requests from persistence")
            return songs
        except Exception as e:
            logger.error(f"Error loading queue: {e}")
            return []

    async def save(self, songs: List[Dict[str, Any]]) -> bool:
        """Atomically saves the queue to disk."""
        async with self._save_lock:
            temp_file = self.queue_file.with_suffix(".tmp")

            data = {
                "version": 1,
                "last_updated": datetime.now().isoformat(),
                "songs": songs,
            }

            try:
                content = json.dumps(data, indent=2, default=str)
                await asyncio.to_thread(temp_file.write_text, content)
                temp_file.replace(self.queue_file)  # Atomic rename
                logger.debug(f"Queue saved: {len(songs)} songs")
                return True
            except Exception as e:
                logger.error(f"Error saving queue: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                return False

    async def backup(self) -> Optional[Path]:
        """Creates a backup of the current file."""
        if not self.queue_file.exists():
            return None

        try:
            import shutil

            backup_path = self.queue_file.with_suffix(".bak")
            await asyncio.to_thread(shutil.copy2, self.queue_file, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return None


class SongRequestPersistence:
    """Manages song-specific persistence (file validation)."""

    def __init__(self, downloads_dir: str = "downloads"):
        self.downloads_dir = Path(downloads_dir)

    async def validate_song_exists(self, query: str, username: str) -> bool:
        """Validates that a restored song still exists in the filesystem."""
        import re

        sanitized = re.sub(r"[^\w\s\-]", "", query)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        for ext in [".mp3", ".m4a", ".webm"]:
            expected_path = self.downloads_dir / f"{username} - {sanitized}{ext}"

            if await asyncio.to_thread(expected_path.exists):
                logger.info(f"Song verified: {query}")
                return True

        logger.warning(f"Song file not found: {query} from @{username}")
        return False
