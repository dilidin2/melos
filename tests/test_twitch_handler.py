"""Tests for twitch_handler module."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from main.twitch_handler import TwitchHandler


class TestTwitchHandler:
    """Tests for TwitchHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a TwitchHandler instance."""
        with patch("main.twitch_handler.Chat"):
            with patch("main.twitch_handler.Twitch"):
                with patch("main.twitch_handler.AuthScope"):
                    handler = TwitchHandler()
                    return handler

    def test_init(self, handler):
        """Test initialization."""
        assert handler.twitch is None
        assert handler.chat is None
        assert handler.command_callback is None
        assert handler._connected is False

    def test_set_command_callback(self, handler):
        """Test setting command callback."""
        callback = MagicMock()
        handler.set_command_callback(callback)
        assert handler.command_callback == callback

    def test_set_command_callback_with_pattern(self, handler):
        """Test setting command callback with custom pattern."""
        callback = MagicMock()
        handler.set_command_callback(callback, pattern="!custom\s+(.+)")
        assert handler.command_callback == callback
        assert "!custom" in handler.command_pattern

    def test_set_multiple_commands(self, handler):
        """Test setting multiple command patterns."""
        callback = MagicMock()
        handler.set_multiple_commands(["!sr", "!custom"], callback)
        assert handler.command_callback == callback
        assert len(handler.multiple_patterns) == 2

    def test_is_connected_false(self, handler):
        """Test is_connected returns False initially."""
        assert handler.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_failure(self, handler):
        """Test connect returns False on failure."""
        with patch("main.twitch_handler.Twitch") as mock_twitch:
            mock_twitch.return_value.__aenter__ = AsyncMock(side_effect=Exception("Error"))
            result = await handler.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self, handler):
        """Test sending message succeeds."""
        handler.chat = MagicMock()
        handler.chat.send_message = AsyncMock(return_value=True)
        
        result = await handler.send_message("testchannel", "Hello!")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_message_no_chat(self, handler):
        """Test sending message with no chat returns False."""
        handler.chat = None
        result = await handler.send_message("testchannel", "Hello!")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_uses_target_channel_for_digit_id(self, handler):
        """Test send_message uses TARGET_CHANNEL for numeric channel IDs."""
        handler.chat = MagicMock()
        handler.chat.send_message = AsyncMock(return_value=True)
        
        await handler.send_message("123456789", "Hello!")
        # Should use TARGET_CHANNEL instead of numeric ID
        handler.chat.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, handler):
        """Test disconnect."""
        handler.chat = MagicMock()
        handler.chat.stop = MagicMock()
        handler.twitch = MagicMock()
        handler.twitch.close = AsyncMock()
        
        await handler.disconnect()
        handler.chat.stop.assert_called_once()
        assert handler._connected is False

    @pytest.mark.asyncio
    async def test_handle_sr_command_with_callback(self, handler):
        """Test handling SR command with callback."""
        handler.command_callback = AsyncMock()
        handler.command_pattern = "!sr\\s+(.+)$"
        
        mock_cmd = MagicMock()
        mock_cmd.parameter = "test song"
        mock_cmd.user.name = "testuser"
        mock_cmd.room.room_id = "12345"
        
        await handler._handle_sr_command(mock_cmd)
        handler.command_callback.assert_called_once_with("test song", "testuser", "12345")

    @pytest.mark.asyncio
    async def test_handle_sr_command_no_query(self, handler):
        """Test handling SR command with no query."""
        handler.command_callback = AsyncMock()
        
        mock_cmd = MagicMock()
        mock_cmd.parameter = ""
        mock_cmd.user.name = "testuser"
        
        await handler._handle_sr_command(mock_cmd)
        # Callback should not be called for empty query
        handler.command_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_sr_command_no_callback(self, handler):
        """Test handling SR command without callback."""
        handler.command_callback = None
        
        mock_cmd = MagicMock()
        mock_cmd.parameter = "test song"
        
        await handler._handle_sr_command(mock_cmd)
        # Should not raise

    @pytest.mark.asyncio
    async def test_handle_other_command_with_processor(self, handler):
        """Test handling other command with processor."""
        handler.command_processor = MagicMock()
        handler.command_processor.process = AsyncMock(return_value=True)
        
        mock_cmd = MagicMock()
        mock_cmd.name = "help"
        mock_cmd.parameter = "sr"
        mock_cmd.user.name = "testuser"
        mock_cmd.room.room_id = "12345"
        
        await handler._handle_other_command(mock_cmd)
        handler.command_processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_other_command_no_processor(self, handler):
        """Test handling other command without processor."""
        handler.command_processor = None
        
        mock_cmd = MagicMock()
        mock_cmd.name = "help"
        
        await handler._handle_other_command(mock_cmd)
        # Should not raise

    @pytest.mark.asyncio
    async def test_handle_message_ignores_commands(self, handler):
        """Test handling message ignores commands."""
        handler.command_callback = MagicMock()
        
        mock_msg = MagicMock()
        mock_msg.text = "!sr test song"
        
        await handler._handle_message(mock_msg)
        handler.command_callback.assert_not_called()
