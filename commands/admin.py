"""Admin Commands - Comandi di amministrazione e moderazione."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from main.config import ADMIN_USERS

if TYPE_CHECKING:
    from main.admin_handler import AdminHandler
    from main.audio_player import AudioPlayer


class AdminCommands:
    """Gestisce tutti i comandi admin e moderation."""

    def __init__(
        self,
        admin_handler: AdminHandler | None = None,
        audio_player: AudioPlayer | None = None,
        request_queue=None,
        bot=None,
    ):
        self.admin_handler = admin_handler
        self.audio_player = audio_player
        self.request_queue = request_queue
        self._bot = bot  # Riferimento al bot per persistenza coda

    async def cmd_whitelist(self, username: str, target_user: str) -> str:
        """!whitelist <username> - Aggiunge un utente alla whitelist."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.admin_handler:
            return "❌ Admin handler non disponibile."

        if self.admin_handler.add_whitelist(target_user):
            return f"✅ {target_user} aggiunto alla whitelist."
        return f"❌ {target_user} è già nella whitelist."

    async def cmd_blacklist(self, username: str, target_user: str) -> str:
        """!blacklist <username> - Mette un utente in blacklist."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.admin_handler:
            return "❌ Admin handler non disponibile."

        if self.admin_handler.add_blacklist(target_user):
            return f"🚫 {target_user} messo in blacklist."
        return f"❌ {target_user} è già in blacklist."

    async def cmd_unblacklist(self, username: str, target_user: str) -> str:
        """!unblacklist <username> - Rimuove un utente dalla blacklist."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.admin_handler:
            return "❌ Admin handler non disponibile."

        if self.admin_handler.remove_blacklist(target_user):
            return f"✅ {target_user} rimosso dalla blacklist."
        return f"❌ {target_user} non era in blacklist."

    async def cmd_whitelist_list(self, username: str) -> str:
        """!whitelist_list - Mostra tutti gli utenti whitelist."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.admin_handler:
            return "❌ Admin handler non disponibile."

        users = self.admin_handler.get_whitelist_list()

        if not users:
            return "📭 Whitelist vuota."

        lines = [f"🛡️ Whitelist ({len(users)} utenti):"]
        for user in users:
            lines.append(f"  • {user}")

        return "\n".join(lines)

    async def cmd_blacklist_list(self, username: str) -> str:
        """!blacklist_list - Mostra tutti gli utenti blacklist."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.admin_handler:
            return "❌ Admin handler non disponibile."

        users = self.admin_handler.get_blacklist_list()

        if not users:
            return "📭 Blacklist vuota."

        lines = [f"🚫 Blacklist ({len(users)} utenti):"]
        for user in users:
            lines.append(f"  • {user}")

        return "\n".join(lines)

    async def cmd_skippa(self, username: str) -> str:
        """!skippa - Salta la canzone corrente."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.audio_player or not self.audio_player.is_playing():
            return "❌ Nessuna canzone in riproduzione da saltare."

        self.audio_player.stop()
        return "⏭️ Canzone saltata!"

    async def cmd_rimuovi_coda(self, username: str, position: str) -> str:
        """!rimuovi_coda <posizione> - Rimuove una posizione dalla coda.

        Rimuove la canzone alla posizione specificata (1-based) dalla coda.
        La posizione 1 è la prossima canzone da riprodurre.
        """
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.request_queue:
            return "❌ Impossibile accedere alla coda."

        try:
            pos = int(position)
        except ValueError:
            return "❌ Usa !rimuovi_coda <numero> (es: !rimuovi_coda 3)"

        if pos < 1:
            return "❌ La posizione deve essere un numero positivo (minimo 1)."

        # Ottieni tutti gli elementi della coda
        items = self.request_queue.get_items(count=1000)

        if pos > len(items):
            return f"❌ Posizione non valida. La coda ha solo {len(items)} canzoni."

        # Rimuovi l'elemento dalla coda asyncio.Queue
        # Creiamo una nuova lista senza l'elemento da rimuovere
        queue_items = list(self.request_queue.queue._queue)
        if pos - 1 < len(queue_items):
            removed_item = queue_items.pop(pos - 1)
            # Ricostruisci la coda con gli elementi rimanenti
            from asyncio import Queue
            new_queue = Queue(maxsize=self.request_queue.max_size)
            for item in queue_items:
                try:
                    new_queue.put_nowait(item)
                except Exception:
                    pass
            self.request_queue.queue = new_queue

            logger.info(f"Elemento rimosso dalla coda (posizione {pos}): {removed_item.query} da @{removed_item.username}")

            # Ottieni il titolo per il messaggio
            title = removed_item.query
            if self._bot and hasattr(self._bot, 'music_downloader'):
                song_info = self._bot.music_downloader.get_song_info(removed_item.query)
                if song_info:
                    title = song_info.get("title", removed_item.query)

            # Persisti la modifica
            if self._bot and hasattr(self._bot, '_persist_queue'):
                import asyncio
                try:
                    asyncio.create_task(self._bot._persist_queue())
                except Exception:
                    pass

            return f"🗑️ Rimossa **{title}** dalla coda (posizione {pos})"
        else:
            return f"❌ Impossibile rimuovere la posizione {pos}."

    async def cmd_clear_queue(self, username: str) -> str:
        """!clear_queue - Svuota completamente la coda.

        Rimuove tutte le canzoni dalla coda. Questa operazione non può
        essere annullata.
        """
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.request_queue:
            return "❌ Impossibile accedere alla coda."

        items = self.request_queue.get_items(count=1000)
        count = len(items)

        if count == 0:
            return "📭 La coda è già vuota."

        # Svuota la coda asyncio.Queue
        queue_items = list(self.request_queue.queue._queue)
        from asyncio import Queue
        new_queue = Queue(maxsize=self.request_queue.max_size)
        for item in queue_items:
            try:
                new_queue.put_nowait(item)
            except Exception:
                pass
        self.request_queue.queue = new_queue

        logger.info(f"Coda svuotata da @{username}: {count} canzoni rimosse")

        # Persisti la modifica
        if self._bot and hasattr(self._bot, '_persist_queue'):
            import asyncio
            try:
                asyncio.create_task(self._bot._persist_queue())
            except Exception:
                pass

        return f"🗑️ Coda svuotata: **{count}** canzoni rimosse"

    async def cmd_coda_info(self, username: str) -> str:
        """!coda_info - Mostra informazioni sulla coda."""
        if username.lower() not in [u.lower() for u in ADMIN_USERS]:
            return "⛔ Non hai i permessi per usare questo comando."
        if not self.request_queue:
            return "📭 Coda non disponibile."

        size = self.request_queue.qsize()
        processing = "✅ Sì" if self.request_queue.is_processing() else "❌ No"

        lines = [
            f"📊 Info Coda:",
            f"  • Elementi in attesa: {size}",
            f"  • In riproduzione: {processing}",
        ]

        return "\n".join(lines)
