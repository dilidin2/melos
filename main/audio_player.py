#!/usr/bin/env python3
"""
Audio Player Module - Aggiornato per supportare Pygame
"""

import os
import threading
from typing import Optional

import pygame
from loguru import logger


class AudioPlayer:
    """Classe per riprodurre file audio con supporto Pygame."""

    def __init__(self, device_name: Optional[str] = None):
        """Inizializza l'AudioPlayer."""
        self._device = device_name
        self._stop_event = threading.Event()
        self._is_playing = False
        self._is_paused = False

        # Configura SDL per usare PipeWire/PulseAudio
        os.environ["SDL_AUDIODRIVER"] = "pulse"
        os.environ["PULSE_PROP"] = "application.name=MusicaBot media.role=music"

        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        logger.info("🎵 AudioPlayer inizializzato con pygame")

    def play(self, filepath: str) -> bool:
        """Riproduce un file audio."""
        if not os.path.exists(filepath):
            logger.error(f"File non trovato: {filepath}")
            return False

        self._stop_event.clear()
        self._is_paused = False

        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self._is_playing = True
            logger.info(f"🎶 Riproduzione: {filepath}")

            import time

            while pygame.mixer.music.get_busy() or self._is_paused:
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    return False
                time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Errore nella riproduzione: {e}")
            return False
        finally:
            self._is_playing = False
            self._is_paused = False

    def pause(self):
        """Mette in pausa la riproduzione."""
        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            logger.info("⏸️ Riproduzione in pausa")

    def resume(self):
        """Riprende la riproduzione dalla pausa."""
        if self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            logger.info("▶️ Riproduzione ripresa")

    def stop(self):
        """Ferma la riproduzione corrente."""
        self._stop_event.set()
        pygame.mixer.music.stop()
        self._is_playing = False
        self._is_paused = False

    def is_playing(self) -> bool:
        """Ritorna True se sta riproducendo."""
        return self._is_playing

    def is_paused(self) -> bool:
        """Ritorna True se è in pausa."""
        return self._is_paused
