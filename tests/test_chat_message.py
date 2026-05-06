"""Tests for chat_message module."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from main.chat_message import ChatMessage


class TestChatMessage:
    """Tests for ChatMessage class."""

    @pytest.fixture
    def chat_message(self, mock_twitch_handler):
        """Create a ChatMessage instance."""
        return ChatMessage(mock_twitch_handler)

    def test_init_stores_handler(self, mock_twitch_handler):
        """Test init stores the twitch handler."""
        chat = ChatMessage(mock_twitch_handler)
        assert chat.twitch_handler == mock_twitch_handler

    @pytest.mark.asyncio
    async def test_send_error(self, chat_message):
        """Test sending error message."""
        result = await chat_message.send_error("ch123", "testuser", "Something went wrong")
        assert result is True
        chat_message.twitch_handler.send_message.assert_called_once_with(
            "ch123", "@testuser ❌ Something went wrong"
        )

    @pytest.mark.asyncio
    async def test_send_error_failure(self, chat_message):
        """Test sending error message on failure."""
        chat_message.twitch_handler.send_message = AsyncMock(return_value=False)
        result = await chat_message.send_error("ch123", "testuser", "Error")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_error_exception(self, chat_message):
        """Test sending error message with exception."""
        chat_message.twitch_handler.send_message = AsyncMock(side_effect=Exception("Network error"))
        result = await chat_message.send_error("ch123", "testuser", "Error")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification(self, chat_message):
        """Test sending notification."""
        result = await chat_message.send_notification("ch123", "New song playing")
        assert result is True
        chat_message.twitch_handler.send_message.assert_called_once_with(
            "ch123", "🎵 New song playing"
        )

    @pytest.mark.asyncio
    async def test_send_now_playing(self, chat_message):
        """Test sending now playing message."""
        result = await chat_message.send_now_playing("ch123", "Bohemian Rhapsody")
        assert result is True
        chat_message.twitch_handler.send_message.assert_called_once_with(
            "ch123", "🎶 Now Playing: Bohemian Rhapsody"
        )

    @pytest.mark.asyncio
    async def test_send_direct(self, chat_message):
        """Test sending direct message."""
        result = await chat_message.send_direct("ch123", "testuser", "Hello!")
        assert result is True
        chat_message.twitch_handler.send_message.assert_called_once_with(
            "ch123", "@testuser Hello!"
        )

    @pytest.mark.asyncio
    async def test_send_public(self, chat_message):
        """Test sending public message."""
        result = await chat_message.send_public("ch123", "Hello everyone!")
        assert result is True
        chat_message.twitch_handler.send_message.assert_called_once_with(
            "ch123", "Hello everyone!"
        )

    @pytest.mark.asyncio
    async def test_send_public_failure(self, chat_message):
        """Test sending public message on failure."""
        chat_message.twitch_handler.send_message = AsyncMock(return_value=False)
        result = await chat_message.send_public("ch123", "Hello")
        assert result is False
