"""Tests for admin commands module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from commands.admin import AdminCommands


class TestAdminCommands:
    """Tests for AdminCommands class."""

    @pytest.fixture
    def commands(self, mock_command_services):
        """Create an AdminCommands instance."""
        return AdminCommands(services=mock_command_services)

    @pytest.fixture
    def mock_cmd(self):
        """Create a mock command object."""
        cmd = MagicMock()
        cmd.user.name = "testuser"
        cmd.room.room_id = "12345"
        cmd.parameter = ""
        return cmd

    @pytest.mark.asyncio
    async def test_cmd_whitelist(self, commands, mock_cmd):
        """Test !whitelist command."""
        mock_cmd.parameter = "testuser"
        mock_command_services = MagicMock()
        mock_command_services.admin_handler.add_whitelist = MagicMock(return_value=True)
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_whitelist(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_blacklist(self, commands, mock_cmd):
        """Test !blacklist command."""
        mock_cmd.parameter = "testuser"
        mock_command_services = MagicMock()
        mock_command_services.admin_handler.add_blacklist = MagicMock(return_value=True)
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_blacklist(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_skippa(self, commands, mock_cmd):
        """Test !skippa command."""
        mock_command_services = MagicMock()
        mock_command_services.audio_player.is_playing = MagicMock(return_value=True)
        mock_command_services.audio_player.stop = MagicMock()
        mock_command_services.request_queue.get_next = MagicMock(return_value=None)
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_skippa(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_clear_queue(self, commands, mock_cmd):
        """Test !clear_queue command."""
        mock_command_services = MagicMock()
        mock_command_services.request_queue.clear = MagicMock()
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_clear_queue(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_rimuovi_coda(self, commands, mock_cmd):
        """Test !rimuovi_coda command."""
        mock_cmd.parameter = "1"
        mock_command_services = MagicMock()
        mock_command_services.request_queue.remove_by_index = MagicMock(return_value=True)
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_rimuovi_coda(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_unblacklist(self, commands, mock_cmd):
        """Test !unblacklist command."""
        mock_cmd.parameter = "testuser"
        mock_command_services = MagicMock()
        mock_command_services.admin_handler.remove_blacklist = MagicMock(return_value=True)
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_unblacklist(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_whitelist_list(self, commands, mock_cmd):
        """Test !whitelist_list command."""
        mock_command_services = MagicMock()
        mock_command_services.admin_handler.get_whitelist_list = MagicMock(return_value=["user1", "user2"])
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_whitelist_list(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_blacklist_list(self, commands, mock_cmd):
        """Test !blacklist_list command."""
        mock_command_services = MagicMock()
        mock_command_services.admin_handler.get_blacklist_list = MagicMock(return_value=["banned1"])
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_blacklist_list(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_rimuovi_coda_invalid_index(self, commands, mock_cmd):
        """Test !rimuovi_coda with invalid index."""
        mock_cmd.parameter = "invalid"
        mock_command_services = MagicMock()
        mock_command_services.request_queue.remove_by_index = MagicMock(return_value=False)
        commands = AdminCommands(services=mock_command_services)
        
        result = await commands.cmd_rimuovi_coda(mock_cmd)
        assert "Errore" in result if result else True
