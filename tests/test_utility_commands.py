"""Tests for utility commands module."""

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch

from commands.utility import UtilityCommands


class TestUtilityCommands:
    """Tests for UtilityCommands class."""

    @pytest.fixture
    def mock_cmd(self):
        """Create a mock command object."""
        cmd = MagicMock()
        cmd.user.name = "testuser"
        cmd.room.room_id = "12345"
        cmd.parameter = ""
        return cmd

    @pytest.mark.asyncio
    async def test_cmd_help_no_args(self, mock_cmd):
        """Test !help without arguments."""
        mock_command_services = MagicMock()
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_help(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_help_sr(self, mock_cmd):
        """Test !help sr."""
        mock_cmd.parameter = "sr"
        mock_command_services = MagicMock()
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_help(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_help_version(self, mock_cmd):
        """Test !help version."""
        mock_cmd.parameter = "version"
        mock_command_services = MagicMock()
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_help(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_help_unknown(self, mock_cmd):
        """Test !help with unknown command."""
        mock_cmd.parameter = "unknown"
        mock_command_services = MagicMock()
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_help(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_version(self, mock_cmd):
        """Test !version command."""
        mock_command_services = MagicMock()
        mock_command_services.bot.config.version = "1.0.0"
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_version(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_uptime(self, mock_cmd):
        """Test !uptime command."""
        mock_command_services = MagicMock()
        mock_command_services.bot.uptime_start = time.time() - 3600  # 1 hour ago
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_uptime(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_uptime_zero(self, mock_cmd):
        """Test !uptime when bot just started."""
        mock_command_services = MagicMock()
        mock_command_services.bot.uptime_start = time.time()
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_uptime(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_queue_info(self, mock_cmd):
        """Test !queue_info command."""
        mock_command_services = MagicMock()
        mock_command_services.request_queue.get_all = MagicMock(return_value=[
            {"query": "Song 1"},
            {"query": "Song 2"},
        ])
        mock_command_services.audio_player.is_playing = MagicMock(return_value=True)
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_queue_info(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_now_playing(self, mock_cmd):
        """Test !now_playing command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=True)
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_now_playing(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_now_playing_not_playing(self, mock_cmd):
        """Test !now_playing when not playing."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=False)
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_now_playing(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_queue_length(self, mock_cmd):
        """Test !queue_length command."""
        mock_command_services = MagicMock()
        mock_command_services.request_queue.get_all = MagicMock(return_value=[
            {"query": "Song 1"},
            {"query": "Song 2"},
        ])
        commands = UtilityCommands(services=mock_command_services)
        
        result = await commands.cmd_queue_length(mock_cmd)
        assert result is not None
