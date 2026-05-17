"""Music Commands - Comandi per il controllo della riproduzione."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from main.audio_player import AudioPlayer
    from main.main_core import RequestQueue
    from main.music_downloader import MusicDownloader


class MusicCommands:
    """Gestisce tutti i comandi musicali avanzati."""

    def __init__(
        self,
        audio_player: "AudioPlayer" | None = None,
        request_queue: "RequestQueue" | None = None,
        music_downloader: "MusicDownloader" | None = None,
        bot=None,
    ):
        self.audio_player = audio_player
        self._request_queue = request_queue
        self._music_downloader = music_downloader
        self._bot = bot  # Riferimento al bot per accedere a repeat settings

    async def cmd_volume(self, username: str, level: int) -> str:
        """!volume <0-100> - Imposta o mostra il volume corrente.

        Se il livello è fornito, imposta il volume (0-100).
        Se non fornito, mostra il volume corrente.
        """
        if level < 0 or level > 100:
            return "❌ Livello di volume deve essere tra 0 e 100."

        # Imposta il volume usando pygame (0.0-1.0)
        if self.audio_player:
            pygame_volume = level / 100.0
            import pygame
            pygame.mixer.music.set_volume(pygame_volume)
            logger.info(f"Volume impostato a {level}% da @{username}")

        return f"🔊 Volume impostato a {level}%"

    async def cmd_pausa(self, username: str) -> str:
        """!pausa - Mette in pausa la riproduzione."""
        if not self.audio_player or not self.audio_player.is_playing():
            return "❌ Nessuna canzone in riproduzione."

        self.audio_player.pause()
        return "⏸️ Riproduzione in pausa."

    async def cmd_riprendi(self, username: str) -> str:
        """!riprendi - Riprende la riproduzione."""
        if not self.audio_player or not self.audio_player.is_paused():
            return "❌ Nessuna canzone in pausa."

        self.audio_player.resume()
        return "▶️ Riproduzione ripresa."

    async def cmd_repeat(self, username: str, count: int = 1) -> str:
        """!repeat [numero] - Ripete la canzone corrente N volte.

        Se count < 0, il repeat è infinito.
        Se count == 0, disattiva il repeat.
        """
        # Aggiorna lo stato del bot se disponibile
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            if count < 0:
                self._bot.repeat_mode = 'infinite'
                self._bot.repeat_remaining = 0  # 0 = infinito per il processor
                return "🔁 Repeat attivo (infinito)"
            elif count == 0:
                self._bot.repeat_mode = 'off'
                self._bot.repeat_remaining = 0
                return "🔁 Modalità repeat disattivata"
            else:
                self._bot.repeat_mode = 'count'
                self._bot.repeat_count = count
                self._bot.repeat_remaining = count  # Inizializza il contatore
                return f"🔁 Repeat attivo ({count} volte)"

        # Fallback se il bot non ha il campo repeat_mode
        if count < 0:
            return "🔁 Repeat attivo (infinito)"
        if count == 0:
            return "🔁 Modalità repeat disattivata"
        return f"🔁 Repeat attivo ({count} volte)"

    async def cmd_repeat_off(self, username: str) -> str:
        """!repeat_off - Disattiva il repeat."""
        return "🔁 Modalità repeat disattivata"

    async def cmd_stop_repeat(self, username: str) -> str:
        """!stop_ripeti - Ferma il repeat e torna al normale flusso.

        Disattiva il repeat corrente e permette al bot di procedere
        con la coda normalmente.
        """
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            self._bot.repeat_mode = 'off'
            logger.info(f"Repeat disattivato da @{username}")

        return "🔁 Repeat disattivato"

    async def cmd_next(self, username: str) -> str:
        """!next - Mostra la prossima canzone nella coda."""
        if not self._request_queue:
            return "❌ Impossibile accedere alla coda."

        items = self._request_queue.get_items(count=1)
        if not items:
            return "⏭️ Non ci sono canzoni nella coda."

        request = items[0]
        if self._music_downloader:
            song_info = self._music_downloader.get_song_info(request.query)
            if song_info:
                title = song_info.get("title", request.query)
            else:
                title = request.query
        else:
            title = request.query

        return f"⏭️ Prossima canzone: **{title}** (richiesta da @{request.username})"

    async def cmd_queue_info(self, username: str) -> str:
        """!queue_info - Mostra info complete sulla coda.

        Include: numero di canzoni in coda, prossima canzone,
        durata stimata totale e stato del repeat.
        """
        if not self._request_queue:
            return "❌ Impossibile accedere alla coda."

        items = self._request_queue.get_items(count=10)
        if not items:
            return "📊 Info coda: Coda vuota."

        # Calcola durata stimata totale
        total_duration = 0
        for item in items:
            if self._music_downloader:
                song_info = self._music_downloader.get_song_info(item.query)
                if song_info and song_info.get("duration", 0) > 0:
                    total_duration += song_info["duration"]
            # Se non abbiamo info, usiamo 4 minuti come media
            if total_duration == 0:
                total_duration += 240  # 4 minuti

        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60

        # Stato del repeat
        repeat_status = "Disattivato"
        if self._bot and hasattr(self._bot, 'repeat_mode'):
            if self._bot.repeat_mode == 'infinite':
                repeat_status = "Infinito"
            elif self._bot.repeat_mode == 'count':
                repeat_status = f"{self._bot.repeat_count} volte"
            else:
                repeat_status = "Disattivato"

        lines = [
            f"📊 **Info Coda:**",
            f"  • Canzoni in coda: {len(items)}",
            f"  • Durata stimata: {hours}h {minutes}m",
            f"  • Repeat: {repeat_status}",
            f"  • Prossima: **{items[0].query}**",
        ]

        return "\n".join(lines)

    async def cmd_duration(self, username: str, query: str) -> str:
        """!duration <canzone> - Mostra la durata di una canzone.

        Cerca la canzone nel database locale o su YouTube.
        """
        if not self._music_downloader:
            return "❌ Impossibile accedere al downloader."

        song_info = self._music_downloader.get_song_info(query)
        if song_info:
            title = song_info.get("title", query)
            duration_seconds = song_info.get("duration", 0)
            if duration_seconds > 0:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/D"
            return f"⏱️ **{title}**: {duration_str}"
        else:
            return f"⏱️ Durata di '{query}': non trovata nel database locale"

    async def cmd_durata(self, position_str: str, username: str, channel_id: str) -> str:
        """!durata <N> - Mostra durata canzone in posizione N nella coda."""
        try:
            position = int(position_str)
        except ValueError:
            return "❌ Usa !durata <numero> (es: !durata 3)"

        if position < 1:
            return "❌ La posizione deve essere un numero positivo (minimo 1)."

        if not self._request_queue or not self._music_downloader:
            return "❌ Impossibile accedere alla coda."

        items = self._request_queue.get_items(count=position)
        if len(items) < position:
            return f"❌ La coda ha solo {len(items)} canzoni. Usa un numero minore o uguale."

        request = items[position - 1]  # 1-based
        song_info = self._music_downloader.get_song_info(request.query)

        if song_info:
            duration_seconds = song_info.get("duration", 0)
            if duration_seconds > 0:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/D"
            title = song_info.get("title", request.query)
        else:
            title = request.query
            duration_str = "N/D"

        return f"⏱️ Canzone #{position}: **'{title}'** - Durata: {duration_str}"

    async def cmd_quando(self, username: str, channel_id: str) -> str:
        """!quando - Stima quando partirà la tua prossima canzone nella coda."""
        if not self._request_queue:
            return "❌ Impossibile accedere alla coda."

        items = self._request_queue.get_items(count=50)  # Controlla fino a 50 canzoni

        # Trova la prima richiesta dell'utente corrente nella coda
        user_request = None
        user_position = -1
        for i, request in enumerate(items):
            if request.username == username:
                user_request = request
                user_position = i
                break

        if user_request is None:
            return "❌ Non hai canzoni in coda."

        # Calcola il tempo stimato (durata media 4 minuti per canzone)
        avg_duration_seconds = 4 * 60  # 4 minuti
        songs_before = user_position
        estimated_seconds = songs_before * avg_duration_seconds

        if estimated_seconds >= 3600:
            hours = estimated_seconds // 3600
            remaining_minutes = (estimated_seconds % 3600) // 60
            time_str = f"{hours}:{remaining_minutes:02d}"
        else:
            minutes = estimated_seconds // 60
            seconds = estimated_seconds % 60
            time_str = f"{minutes}:{seconds:02d}"

        # Ottieni il titolo della canzone
        song_info = self._music_downloader.get_song_info(user_request.query)
        if song_info:
            title = song_info.get("title", user_request.query)
        else:
            title = user_request.query

        if songs_before == 0:
            return f"🕐 La tua prossima canzone (**'{title}'**) partirà **adesso!**"
        else:
            return f"🕐 La tua prossima canzone (**'{title}'**) partirà tra circa {time_str} ({songs_before} canzoni)"

    async def cmd_random(self, username: str, n: int = 1) -> str:
        """!random [N] - Riproduci N canzoni casuali dalla libreria scaricata."""
        import os
        import random as random_module
        from main.config import DOWNLOAD_DIR
        from main.main_core import SongRequest

        try:
            files = os.listdir(DOWNLOAD_DIR)
            audio_files = [
                f for f in files if f.lower().endswith((".mp3", ".wav", ".m4a"))
            ]
        except Exception as e:
            logger.error(f"Errore lettura directory downloads: {e}")
            return "❌ Impossibile leggere la libreria musicale."

        if not audio_files:
            return "📭 Nessuna canzone scaricata nella libreria. Scarica prima qualcosa con !sr!"

        # Evita di ripetere la stessa canzone 2 volte di fila
        last_song = getattr(self._bot, 'last_random_song', None)
        available = [f for f in audio_files if f != last_song] if last_song else audio_files

        count = min(n, len(available))
        selected = random_module.sample(available, count)

        if count == 0:
            return "📭 Libreria vuota o nessun brano disponibile."

        for song_file in selected:
            request_id = self._request_queue._request_counter
            self._request_queue._request_counter += 1
            # Passa il path completo così download() lo trova subito senza cercare su YouTube
            full_path = os.path.join(DOWNLOAD_DIR, song_file)
            request = SongRequest(
                query=full_path,
                username=username,
                channel_id="",
                request_id=request_id,
            )
            await self._request_queue.put(request)

            # Aggiorna il tracking per evitare ripetizioni consecutive
            if self._bot and hasattr(self._bot, 'last_random_song'):
                self._bot.last_random_song = song_file

        song_names = [os.path.splitext(f)[0] for f in selected]
        if n == 1:
            return f"🎲 Canzone random dalla libreria: **{song_names[0]}**"
        else:
            lines = [f"🎲 {count} canzoni random dalla libreria:"]
            for i, name in enumerate(song_names, 1):
                lines.append(f"  {i}. {name}")
            return "\n".join(lines)
