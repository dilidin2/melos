#!/usr/bin/env python3
"""
Audio Player Module - Updated to support Pygame
"""

import os
import threading
from typing import Optional

import pygame
from loguru import logger


class AudioPlayer:
    """Class to play audio files with Pygame support."""

    def __init__(self, device_name: Optional[str] = None):
        """Initializes the AudioPlayer."""
        self._device = device_name
        self._stop_event = threading.Event()
        self._is_playing = False
        self._is_paused = False

        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        logger.info("🎵 AudioPlayer initialized with pygame")

    def play(self, filepath: str) -> bool:
        """Plays an audio file."""
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return False

        self._stop_event.clear()
        self._is_paused = False

        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self._is_playing = True
            logger.info(f"🎶 Playing: {filepath}")

            import time

            while pygame.mixer.music.get_busy() or self._is_paused:
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    return False
                time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Error in playback: {e}")
            return False
        finally:
            self._is_playing = False
            self._is_paused = False

    def pause(self):
        """Pauses playback."""
        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            logger.info("⏸️ Playback paused")

    def resume(self):
        """Resumes playback from pause."""
        if self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            logger.info("▶️ Playback resumed")

    def stop(self):
        """Stops current playback."""
        self._stop_event.set()
        pygame.mixer.music.stop()
        self._is_playing = False
        self._is_paused = False

    def is_playing(self) -> bool:
        """Returns True if playing."""
        return self._is_playing

    def is_paused(self) -> bool:
        """Returns True if paused."""
        return self._is_paused

    def set_volume(self, level: float):
        """Set volume level (0.0 to 1.0)."""
        level = max(0.0, min(1.0, level))
        pygame.mixer.music.set_volume(level)
        logger.info(f"🔊 Volume set to {int(level * 100)}%")
