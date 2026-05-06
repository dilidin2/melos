"""Tests for analytics commands module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from commands.analytics import AnalyticsCommands


class TestAnalyticsCommands:
    """Tests for AnalyticsCommands class."""

    @pytest.fixture
    def mock_cmd(self):
        """Create a mock command object."""
        cmd = MagicMock()
        cmd.user.name = "testuser"
        cmd.room.room_id = "12345"
        cmd.parameter = ""
        return cmd

    @pytest.mark.asyncio
    async def test_cmd_stats(self, mock_cmd):
        """Test !stats command."""
        mock_command_services = MagicMock()
        mock_command_services.analytics.get_stats_today = MagicMock(return_value={
            "total_requests_today": 10,
            "unique_users_today": 5,
        })
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_stats(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_stats_week(self, mock_cmd):
        """Test !stats week."""
        mock_cmd.parameter = "week"
        mock_command_services = MagicMock()
        mock_command_services.analytics.get_stats_week = MagicMock(return_value={
            "total_requests_week": 50,
            "period": "last_7_days",
        })
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_stats(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_stats_month(self, mock_cmd):
        """Test !stats month."""
        mock_cmd.parameter = "month"
        mock_command_services = MagicMock()
        mock_command_services.analytics.get_stats_month = MagicMock(return_value={
            "total_requests_month": 200,
            "period": "last_30_days",
        })
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_stats(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_top_canzoni(self, mock_cmd):
        """Test !top_canzoni command."""
        mock_cmd.parameter = "5"
        mock_command_services = MagicMock()
        mock_command_services.analytics.get_top_songs = MagicMock(return_value=[
            {"title": "Song 1", "count": 10},
            {"title": "Song 2", "count": 8},
        ])
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_top_canzoni(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_top_user(self, mock_cmd):
        """Test !top_user command."""
        mock_cmd.parameter = "5"
        mock_command_services = MagicMock()
        mock_command_services.analytics.get_top_users = MagicMock(return_value=[
            {"username": "user1", "count": 50},
            {"username": "user2", "count": 30},
        ])
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_top_user(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_export_stats_json(self, mock_cmd):
        """Test !export_stats json command."""
        mock_cmd.parameter = "json"
        mock_command_services = MagicMock()
        mock_command_services.analytics.export_stats = MagicMock(return_value='{"total_requests": 100}')
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_export_stats(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_export_stats_csv(self, mock_cmd):
        """Test !export_stats csv command."""
        mock_cmd.parameter = "csv"
        mock_command_services = MagicMock()
        mock_command_services.analytics.export_stats = MagicMock(return_value="Title,Count\nSong 1,10")
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_export_stats(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_export_stats_invalid_format(self, mock_cmd):
        """Test !export_stats with invalid format."""
        mock_cmd.parameter = "xml"
        mock_command_services = MagicMock()
        mock_command_services.analytics.export_stats = MagicMock(return_value="Formato non supportato")
        commands = AnalyticsCommands(services=mock_command_services)
        
        result = await commands.cmd_export_stats(mock_cmd)
        assert "non supportato" in result
