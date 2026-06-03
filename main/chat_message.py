"""Chat Message Module - Handles error messages and notifications."""

from loguru import logger


class ChatMessage:
    """Class to manage messages in the chat."""

    def __init__(self, twitch_handler):
        """
        Initializes ChatMessage.

        Args:
            twitch_handler: TwitchHandler instance for sending messages
        """
        self.twitch_handler = twitch_handler

    async def send_error(
        self, channel_id: str, username: str, error_message: str
    ) -> bool:
        """
        Sends an error message to a specific user.
        """
        try:
            message = f"@{username} ❌ {error_message}"
            return await self.twitch_handler.send_message(channel_id, message)
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
            return False

    async def send_notification(self, channel_id: str, message: str) -> bool:
        """Sends a notification in the chat."""
        try:
            return await self.twitch_handler.send_message(channel_id, f"🎵 {message}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def send_now_playing(self, channel_id: str, title: str) -> bool:
        """Sends a "Now Playing" message."""
        try:
            message = f"🎶 Now Playing: {title}"
            return await self.twitch_handler.send_message(channel_id, message)
        except Exception as e:
            logger.error(f"Error sending now playing: {e}")
            return False

    async def send_direct(self, channel_id: str, username: str, message: str) -> bool:
        """Sends a direct message (with mention)."""
        try:
            formatted = f"@{username} {message}"
            return await self.twitch_handler.send_message(channel_id, formatted)
        except Exception as e:
            logger.error(f"Error sending direct message: {e}")
            return False

    async def send_public(self, channel_id: str, message: str) -> bool:
        """Sends a public message without mention."""
        try:
            return await self.twitch_handler.send_message(channel_id, message)
        except Exception as e:
            logger.error(f"Error sending public message: {e}")
            return False
