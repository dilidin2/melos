"""Tests for music commands module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from commands.music import MusicCommands


class TestMusicCommands:
    """Tests for MusicCommands class."""

    @pytest.fixture
    def mock_cmd(self):
        """Create a mock command object."""
        cmd = MagicMock()
        cmd.user.name = "testuser"
        cmd.room.room_id = "12345"
        cmd.parameter = ""
        return cmd

    @pytest.mark.asyncio
    async def test_cmd_sr(self, mock_cmd):
        """Test !sr command."""
        mock_cmd.parameter = "test song"
        mock_command_services = MagicMock()
        mock_command_services.music_downloader.get_video_info = MagicMock(return_value={
            "title": "Test Song",
            "duration": 240,
            "categories": ["Music"],
        })
        
        commands = MusicCommands(services=mock_command_services)
        result = await commands.cmd_sr(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_sr_no_query(self, mock_cmd):
        """Test !sr with no query."""
        mock_cmd.parameter = ""
        mock_command_services = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_sr(mock_cmd)
        assert result is not None
        assert "Errore" in result

    @pytest.mark.asyncio
    async def test_cmd_sr_not_url(self, mock_cmd):
        """Test !sr with non-URL query."""
        mock_cmd.parameter = "test song"
        mock_command_services = MagicMock()
        mock_command_services.music_downloader.get_video_info = MagicMock(return_value=None)
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_sr(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_volume(self, mock_cmd):
        """Test !volume command."""
        mock_cmd.parameter = "50"
        mock_command_services = MagicMock()
        mock_command_services.bot.config.volume = 50
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_volume(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_volume_no_arg(self, mock_cmd):
        """Test !volume without argument."""
        mock_cmd.parameter = ""
        mock_command_services = MagicMock()
        mock_command_services.bot.config.volume = 50
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_volume(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_pausa(self, mock_cmd):
        """Test !pausa command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=True)
        mock_command_services.audio_player.pause = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_pausa(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_pausa_not_playing(self, mock_cmd):
        """Test !pausa when not playing."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=False)
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_pausa(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_riprendi(self, mock_cmd):
        """Test !riprendi command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_paused = MagicMock(return_value=True)
        mock_command_services.audio_player.resume = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_riprendi(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_ripeti(self, mock_cmd):
        """Test !ripeti command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=True)
        mock_command_services.audio_player.pause = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_ripeti(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_stop_repeat(self, mock_cmd):
        """Test !stop_ripeti command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_paused = MagicMock(return_value=True)
        mock_command_services.audio_player.resume = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_stop_repeat(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_repeat(self, mock_cmd):
        """Test !repeat command."""
        mock_cmd.parameter = "3"
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=True)
        mock_command_services.audio_player.pause = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_repeat(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_repeat_off(self, mock_cmd):
        """Test !repeat_off command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_paused = MagicMock(return_value=True)
        mock_command_services.audio_player.resume = MagicMock()
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_repeat_off(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_next(self, mock_cmd):
        """Test !next command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.stop = MagicMock()
        mock_command_services.request_queue.get_next = MagicMock(return_value={"query": "Next Song"})
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_next(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_duration(self, mock_cmd):
        """Test !duration command."""
        mock_cmd.parameter = "test song"
        mock_command_services = MagicMock()
        mock_command_services.music_downloader.get_song_info = MagicMock(return_value={
            "title": "Test Song",
            "duration": 240,
        })
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_duration(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_durata(self, mock_cmd):
        """Test !durata command."""
        mock_cmd.parameter = "1"
        mock_command_services = MagicMock()
        mock_command_services.request_queue.get_by_index = MagicMock(return_value={
            "query": "Song at position 1",
            "duration": 180,
        })
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_durata(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_quando(self, mock_cmd):
        """Test !quando command."""
        mock_command_services = MagicMock()
        mock_command_services.request_queue.get_all = MagicMock(return_value=[
            {"query": "Song 1"},
            {"query": "Song 2"},
        ])
        commands = MusicCommands(services=mock_command_services)
        
        result = await commands.cmd_quando(mock_cmd)
        assert result is not None
