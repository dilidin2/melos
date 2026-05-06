# -*- coding: utf-8 -*-
"""
Queue Persistence - Persistenza della coda delle richieste

Implementa un layer di persistenza ibrido che:
- Mantiene asyncio.Queue per il runtime (performance + thread-safety)
- Aggiunge un QueuePersistence layer per salvataggio su disco
- Garantisce atomicità con file temporaneo + rename
- Preserva i timestamp originali di added_at
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger


class QueuePersistence:
    """Layer di persistenza per la coda canzoni."""

    def __init__(self, queue_file: str = "data/queue.json"):
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_lock = asyncio.Lock()

    async def load(self) -> List[Dict[str, Any]]:
        """Carica la coda dal disco all'avvio."""
        if not self.queue_file.exists():
            logger.info("Nessun file queue trovato, avvio con coda vuota")
            return []

        try:
            content = await asyncio.to_thread(self.queue_file.read_text)
            data = json.loads(content)
            songs = data.get("songs", [])
            logger.info(f"Caricate {len(songs)} richieste dalla persistenza")
            return songs
        except Exception as e:
            logger.error(f"Errore caricamento queue: {e}")
            return []

    async def save(self, songs: List[Dict[str, Any]]) -> bool:
        """Salva atomicamente la coda su disco."""
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
                logger.debug(f"Queue salvata: {len(songs)} canzoni")
                return True
            except Exception as e:
                logger.error(f"Errore salvataggio queue: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                return False

    async def backup(self) -> Optional[Path]:
        """Crea un backup del file corrente."""
        if not self.queue_file.exists():
            return None

        try:
            import shutil

            backup_path = self.queue_file.with_suffix(".bak")
            await asyncio.to_thread(shutil.copy2, self.queue_file, backup_path)
            logger.info(f"Backup creato: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Errore durante il backup: {e}")
            return None


class SongRequestPersistence:
    """Gestisce la persistenza specifica per le canzoni (validazione file)."""

    def __init__(self, downloads_dir: str = "downloads"):
        self.downloads_dir = Path(downloads_dir)

    async def validate_song_exists(self, query: str, username: str) -> bool:
        """Valida che una canzone ripristinata esista ancora nel filesystem."""
        import re

        sanitized = re.sub(r"[^\w\s\-]", "", query)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        for ext in [".mp3", ".m4a", ".webm"]:
            expected_path = self.downloads_dir / f"{username} - {sanitized}{ext}"

            if await asyncio.to_thread(expected_path.exists):
                logger.info(f"Canzone verificata: {query}")
                return True

        logger.warning(f"File canzone non trovato: {query} da @{username}")
        return False
