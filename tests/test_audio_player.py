"""Tests for audio_player module."""

import pytest
from unittest.mock import MagicMock, patch, call
import threading

from main.audio_player import AudioPlayer


class TestAudioPlayer:
    """Tests for AudioPlayer class."""

    @pytest.fixture
    def player(self):
        """Create an AudioPlayer instance."""
        with patch("pygame.mixer.init"):
            with patch("pygame.mixer.music"):
                player = AudioPlayer()
                return player

    def test_init_initializes_pygame(self):
        """Test init initializes pygame."""
        with patch("pygame.mixer.init") as mock_init:
            AudioPlayer()
            mock_init.assert_called_once_with(
                frequency=44100, size=-16, channels=2, buffer=2048
            )

    def test_init_sets_device(self):
        """Test init sets device name."""
        with patch("pygame.mixer.init"):
            player = AudioPlayer(device_name="test_device")
            assert player._device == "test_device"

    def test_init_sets_stop_event(self):
        """Test init creates stop event."""
        with patch("pygame.mixer.init"):
            player = AudioPlayer()
            assert player._stop_event is not None

    def test_init_sets_initial_states(self):
        """Test init sets initial playing/paused states."""
        with patch("pygame.mixer.init"):
            player = AudioPlayer()
            assert player._is_playing is False
            assert player._is_paused is False

    def test_play_file_not_found(self, player):
        """Test play returns False for non-existent file."""
        with patch("os.path.exists", return_value=False):
            with patch("pygame.mixer.music"):
                result = player.play("/nonexistent.mp3")
                assert result is False

    def test_play_success(self, player):
        """Test successful playback."""
        with patch("os.path.exists", return_value=True):
            with patch("pygame.mixer.music") as mock_music:
                mock_music.load = MagicMock()
                mock_music.play = MagicMock()
                mock_music.get_busy = MagicMock(side_effect=[True, False])
                
                result = player.play("/test.mp3")
                assert result is True
                mock_music.load.assert_called_once_with("/test.mp3")
                mock_music.play.assert_called_once()

    def test_play_stops_on_stop_event(self, player):
        """Test playback stops when stop event is set."""
        with patch("os.path.exists", return_value=True):
            with patch("pygame.mixer.music") as mock_music:
                mock_music.load = MagicMock()
                mock_music.play = MagicMock()
                mock_music.get_busy = MagicMock(side_effect=[True, False])
                
                player.play("/test.mp3")
                assert player._is_playing is False

    def test_play_exception(self, player):
        """Test play handles exceptions."""
        with patch("os.path.exists", return_value=True):
            with patch("pygame.mixer.music") as mock_music:
                mock_music.load = MagicMock(side_effect=Exception("Error"))
                
                result = player.play("/test.mp3")
                assert result is False

    def test_pause_when_playing(self, player):
        """Test pause when playing."""
        player._is_playing = True
        player._is_paused = False
        
        with patch("pygame.mixer.music") as mock_music:
            player.pause()
            mock_music.pause.assert_called_once()
            assert player._is_paused is True

    def test_pause_when_not_playing(self, player):
        """Test pause when not playing does nothing."""
        player._is_playing = False
        
        with patch("pygame.mixer.music") as mock_music:
            player.pause()
            mock_music.pause.assert_not_called()

    def test_resume_when_paused(self, player):
        """Test resume when paused."""
        player._is_paused = True
        
        with patch("pygame.mixer.music") as mock_music:
            player.resume()
            mock_music.unpause.assert_called_once()
            assert player._is_paused is False

    def test_resume_when_not_paused(self, player):
        """Test resume when not paused does nothing."""
        player._is_paused = False
        
        with patch("pygame.mixer.music") as mock_music:
            player.resume()
            mock_music.unpause.assert_not_called()

    def test_stop(self, player):
        """Test stopping playback."""
        player._is_playing = True
        player._is_paused = True
        
        with patch("pygame.mixer.music") as mock_music:
            player.stop()
            player._stop_event.set()
            mock_music.stop.assert_called_once()
            assert player._is_playing is False
            assert player._is_paused is False

    def test_is_playing(self, player):
        """Test is_playing returns correct value."""
        player._is_playing = True
        assert player.is_playing() is True
        
        player._is_playing = False
        assert player.is_playing() is False

    def test_is_paused(self, player):
        """Test is_paused returns correct value."""
        player._is_paused = True
        assert player.is_paused() is True
        
        player._is_paused = False
        assert player.is_paused() is False
