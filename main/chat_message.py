"""Chat Message Module - Gestisce messaggi di errore e notifiche."""

from loguru import logger


class ChatMessage:
    """Classe per gestire i messaggi nella chat."""

    def __init__(self, twitch_handler):
        """
        Inizializza ChatMessage.

        Args:
            twitch_handler: Istanza di TwitchHandler per inviare messaggi
        """
        self.twitch_handler = twitch_handler

    async def send_error(
        self, channel_id: str, username: str, error_message: str
    ) -> bool:
        """
        Invia un messaggio di errore a un utente specifico.
        """
        try:
            message = f"@{username} ❌ {error_message}"
            return await self.twitch_handler.send_message(channel_id, message)
        except Exception as e:
            logger.error(f"Errore nell'invio messaggio errore: {e}")
            return False

    async def send_notification(self, channel_id: str, message: str) -> bool:
        """Invia una notifica nella chat."""
        try:
            return await self.twitch_handler.send_message(channel_id, f"🎵 {message}")
        except Exception as e:
            logger.error(f"Errore nell'invio notifica: {e}")
            return False

    async def send_now_playing(self, channel_id: str, title: str) -> bool:
        """Invia un messaggio "Now Playing"."""
        try:
            message = f"🎶 Now Playing: {title}"
            return await self.twitch_handler.send_message(channel_id, message)
        except Exception as e:
            logger.error(f"Errore nell'invio now playing: {e}")
            return False

    async def send_direct(self, channel_id: str, username: str, message: str) -> bool:
        """Invia un messaggio diretto (con menzione)."""
        try:
            formatted = f"@{username} {message}"
            return await self.twitch_handler.send_message(channel_id, formatted)
        except Exception as e:
            logger.error(f"Errore nell'invio messaggio diretto: {e}")
            return False

    async def send_public(self, channel_id: str, message: str) -> bool:
        """Invia un messaggio pubblico senza menzione."""
        try:
            return await self.twitch_handler.send_message(channel_id, message)
        except Exception as e:
            logger.error(f"Errore nell'invio messaggio pubblico: {e}")
            return False
