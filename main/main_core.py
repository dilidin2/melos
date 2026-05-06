import os
import asyncio
import signal
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable
from queue import Queue

from main.config import (
    TARGET_CHANNEL,
    MAX_WORKERS,
    LOG_LEVEL,
    LOG_FILE,
    DOWNLOAD_DIR,
)

from main.music_downloader import (
    MusicDownloader,
    _SongTooLongError,
    _CategoryError,
    _NoValidCandidateError,
)
from main.audio_player import AudioPlayer
from main.twitch_handler import TwitchHandler
from main.chat_message import ChatMessage
from main.queue_persistence import QueuePersistence, SongRequestPersistence

from loguru import logger


@dataclass
class SongRequest:
    """Rappresenta una richiesta di canzone."""

    query: str
    username: str
    channel_id: str
    request_id: int
    added_at: Optional[str] = None
    resolved_title: Optional[str] = None
    resolved_duration: Optional[int] = None


class RequestQueue:
    """Gestisce la coda delle richieste."""

    def __init__(self, max_size: int = 999):
        self.queue: asyncio.Queue[SongRequest] = asyncio.Queue(maxsize=max_size)
        self.max_size = max_size
        self._request_counter = 0
        self._in_progress = False

    async def put(self, request: SongRequest) -> bool:
        """Aggiunge una richiesta alla coda."""
        try:
            await asyncio.wait_for(self.queue.put(request), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Coda piena, richiesta rifiutata: {request.query}")
            return False

    async def get(self) -> Optional[SongRequest]:
        """Ritorna la prossima richiesta."""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def task_done(self):
        """Segna una richiesta come completata."""
        self.queue.task_done()

    def qsize(self) -> int:
        """Ritorna la dimensione della coda."""
        return self.queue.qsize()

    def is_processing(self) -> bool:
        """Ritorna True se sta processando una richiesta."""
        return self._in_progress

    def get_items(self, count: int = 10) -> list[SongRequest]:
        """Restituisce le prossime N richieste senza rimuoverle dalla coda."""
        return list(self.queue._queue)[:count]


class DuplicateCache:
    """Cache per evitare download duplicati."""

    def __init__(self, max_size: int = 100):
        self.cache: dict[str, tuple[str, str]] = {}
        self.max_size = max_size

    def add(self, query: str, file_path: str, username: str) -> None:
        """Aggiunge una canzone alla cache."""
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        self.cache[query.lower()] = (file_path, username)

    def get(self, query: str) -> Optional[tuple[str, str]]:
        """Ritorna la canzone se già scaricata."""
        return self.cache.get(query.lower())

    def remove(self, query: str) -> None:
        """Rimuove una canzone dalla cache."""
        self.cache.pop(query.lower(), None)


class SongRequestBot:
    """Bot principale per le richieste di canzoni."""

    def __init__(self, audio_device=None):
        """Inizializza il bot."""
        self.music_downloader = MusicDownloader()
        self.audio_player = AudioPlayer(device_name=audio_device)
        self.twitch_handler = TwitchHandler()
        self.chat_message = ChatMessage(self.twitch_handler)
        self.request_queue = RequestQueue()
        self.duplicate_cache = DuplicateCache()
        self._running = False
        self._processing_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._shutdown_initiated = False
        self._request_counter = 0

        # Repeat mode settings
        self.repeat_mode = 'off'  # 'off', 'count', 'infinite'
        self.repeat_count = 1     # Numero di ripetizioni se repeat_mode='count'
        self.repeat_remaining = 0 # Conteggio residuo per repeat

        # Traccia l'ultima canzone random riprodotta per evitare ripetizioni consecutive
        self.last_random_song: Optional[str] = None

        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

        self.queue_persistence = QueuePersistence()
        self.song_request_persistence = SongRequestPersistence()

    async def _handle_song_request(self, query: str, username: str, channel_id: str):
        """Gestisce una richiesta di canzone."""
        if hasattr(self, "analytics"):
            self.analytics.record_request(username, query)

        request = SongRequest(query, username, channel_id, self._request_counter)
        self._request_counter += 1

        success = await self.request_queue.put(request)
        if not success:
            await self.chat_message.send_error(
                channel_id, username, "Coda piena, riprova più tardi."
            )
            return

        position = self.request_queue.qsize()
        logger.info(f"Richiesta aggiunta alla coda: {query} da @{username}")

        await self.chat_message.send_public(
            channel_id,
            f"✅ Aggiunta **{query}** alla coda in posizione {position}",
        )

        await self._persist_queue()
        self._shutdown_event.clear()

    async def _persist_queue(self):
        """Converte la coda attuale in JSON e salva."""
        items = list(self.request_queue.queue._queue)

        songs_data = [
            {
                "query": item.query,
                "username": item.username,
                "channel_id": item.channel_id,
                "request_id": item.request_id,
                "added_at": getattr(item, "added_at", datetime.now().isoformat()),
            }
            for item in items
        ]

        await self.queue_persistence.save(songs_data)

    async def _load_persisted_queue(self):
        """Ripristina la coda dal file all'avvio."""
        songs = await self.queue_persistence.load()

        for song_data in songs:
            request = SongRequest(
                query=song_data["query"],
                username=song_data["username"],
                channel_id=song_data["channel_id"],
                request_id=song_data["request_id"],
            )
            request.added_at = song_data.get("added_at")

            try:
                self.request_queue.queue.put_nowait(request)
                logger.info(f"🔄 Ripristinata dalla persistenza: {request.query}")
            except asyncio.QueueFull:
                logger.warning("Coda piena durante il ripristino")
                break

    async def _play_audio_file(
        self, channel_id: str, file_path: str, notification_text: Optional[str] = None
    ):
        """Riproduce un file audio e invia l'eventuale notifica di riproduzione."""
        try:
            if notification_text:
                await self.chat_message.send_now_playing(
                    channel_id,
                    notification_text,
                )

            await asyncio.get_running_loop().run_in_executor(
                self.executor, self.audio_player.play, file_path
            )
            return True
        except Exception as e:
            logger.error(f"Errore nella riproduzione di '{file_path}': {e}", exc_info=True)
            return False

    async def _process_request(self, request: SongRequest) -> bool:
        """Processa una singola richiesta."""
        async with self._processing_lock:
            if self.request_queue.is_processing():
                logger.warning(
                    f"Già in elaborazione, richiesta ignorata: '{request.query}' da @{request.username}"
                )
                await self.chat_message.send_error(
                    request.channel_id,
                    request.username,
                    "C'è già una canzone in riproduzione. Riprova più tardi.",
                )
                return False

            self.request_queue._in_progress = True
            logger.info(f"Processando: '{request.query}' da @{request.username}")

        try:
            cached = self.duplicate_cache.get(request.query)
            if cached:
                file_path, _ = cached
                # FIX: verifica che il file in cache esista ancora su disco
                if not os.path.exists(file_path):
                    logger.warning(
                        f"File in cache non trovato su disco, ri-scarico: '{request.query}'"
                    )
                    self.duplicate_cache.remove(request.query)
                    file_path = None
                else:
                    logger.info(f"Canzone già scaricata, uso cache: '{request.query}'")
            else:
                file_path = None

            if file_path is None:
                try:
                    file_path = await asyncio.get_running_loop().run_in_executor(
                        self.executor, self.music_downloader.download, request.query
                    )

                    if not file_path:
                        logger.warning(
                            f"Download fallito (nessun file) per '{request.query}' da @{request.username}"
                        )
                        await self.chat_message.send_error(
                            request.channel_id,
                            request.username,
                            "Impossibile scaricare la canzone. Riprova più tardi.",
                        )
                        return False

                    # Usa il nome del file su disco come chiave cache (non la query
                    # dell'utente), così query diverse per la stessa canzone
                    # trovano il file in cache al secondo tentativo.
                    cache_key = os.path.splitext(os.path.basename(file_path))[0]
                    self.duplicate_cache.add(cache_key, file_path, request.username)
                    # Aggiungi anche la query originale per hit immediato
                    self.duplicate_cache.add(request.query, file_path, request.username)

                except _SongTooLongError as e:
                    logger.warning(
                        f"Canzone troppo lunga per '{request.query}' da @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except _CategoryError as e:
                    logger.warning(
                        f"Categoria non consentita per '{request.query}' da @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except _NoValidCandidateError as e:
                    logger.warning(
                        f"Nessun candidato valido per '{request.query}' da @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except Exception as e:
                    logger.error(
                        f"Eccezione nel download di '{request.query}' da @{request.username}: "
                        f"{type(e).__name__}: {e}",
                        exc_info=True,
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        "Errore durante il download. Riprova più tardi.",
                    )
                    return False

            song_info = self.music_downloader.get_song_info(request.query)
            if song_info:
                request.resolved_title = song_info.get("title")
                request.resolved_duration = song_info.get("duration")

            # FIX BUG: dopo il download, ottieni il titolo corretto dal nome del
            # file su disco. Il download() prova fino a 10 candidati YouTube e
            # se il primo è geo-blocked prende il secondo, quindi il titolo
            # originale della ricerca potrebbe non corrispondere alla canzone
            # effettivamente riprodotta.
            if file_path and os.path.exists(file_path):
                actual_title = os.path.splitext(os.path.basename(file_path))[0]
                request.resolved_title = actual_title

            notification = f"{request.resolved_title or request.query} - @{request.username}"
            success = await self._play_audio_file(
                request.channel_id, file_path, notification
            )

            # FIX: notifica l'utente anche in caso di errore di riproduzione.
            # Prima mancava questo ramo: se _play_audio_file restituiva False,
            # il bot non mandava nessun messaggio in chat.
            if not success:
                logger.error(
                    f"Riproduzione fallita per '{request.query}' da @{request.username} "
                    f"(file: '{file_path}')"
                )
                await self.chat_message.send_error(
                    request.channel_id,
                    request.username,
                    "Errore durante la riproduzione. Riprova più tardi.",
                )

            if success and hasattr(self, "analytics"):
                self.analytics.record_play(request.username, request.query)

            return success

        finally:
            self.request_queue._in_progress = False

    async def _queue_processor(self):
        """Processa continuamente la coda delle richieste."""
        while not self._shutdown_event.is_set() or self.request_queue.qsize() > 0:
            if self._shutdown_event.is_set():
                while self.request_queue.qsize() > 0:
                    try:
                        req = await self.request_queue.get()
                        if req:
                            self.request_queue.task_done()
                            logger.info(f"Coda svuotata: {req.query}")
                    except Exception:
                        break
                break

            request = await self.request_queue.get()

            if request:
                await self._process_request(request)
                self.request_queue.task_done()
                await self._persist_queue()
            else:
                if not self._shutdown_event.is_set():
                    # Estrae una canzone random da downloads/ evitando la stessa 2 volte di fila
                    try:
                        import random as random_module
                        files = os.listdir(DOWNLOAD_DIR)
                        audio_files = [
                            f for f in files if f.lower().endswith((".mp3", ".wav", ".m4a"))
                        ]

                        if audio_files:
                            # Se c'è un'ultima canzone riprodotta, filtra per evitare ripetizioni consecutive
                            if self.last_random_song:
                                available = [f for f in audio_files if f != self.last_random_song]
                                if not available:
                                    # Tutti i file sono l'ultima canzone (solo un file presente), usa quello
                                    available = audio_files
                            else:
                                available = audio_files

                            selected = random_module.choice(available)
                            random_file = os.path.join(DOWNLOAD_DIR, selected)
                            # Aggiorna il tracking
                            self.last_random_song = selected

                            song_name = os.path.splitext(selected)[0]
                            notification = f"Riproduzione casuale di {song_name}"
                            await self._play_audio_file(
                                TARGET_CHANNEL, random_file, notification
                            )
                        else:
                            await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"Errore selezione canzone random: {e}")
                        await asyncio.sleep(1)

            await asyncio.sleep(0.1)

    def skip_current_song(self) -> bool:
        """Ferma la riproduzione corrente per saltare alla successiva."""
        if not self.audio_player.is_playing():
            return False

        self.audio_player.stop()
        return True

    def _signal_handler(self):
        """Handler per SIGINT/SIGTERM."""
        if not self._shutdown_initiated:
            logger.info("Segnale di arresto ricevuto (Ctrl+C)")
            asyncio.create_task(self.shutdown())

    async def run(self):
        """Avvia il bot."""
        self._running = True

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)

        self.twitch_handler.set_command_callback(self._handle_song_request)
        await self._load_persisted_queue()

        if not await self.twitch_handler.connect():
            logger.error("Impossibile connettersi a Twitch")
            return

        logger.info(f"Bot attivo sul canale @{TARGET_CHANNEL}")
        logger.info("Ascolto comandi !sr... (Ctrl+C per uscire)")

        self._queue_task = asyncio.create_task(self._queue_processor())
        self._queue_task.add_done_callback(
            lambda t: (
                logger.error(f"Queue processor morto: {t.exception()}")
                if not t.cancelled() and t.exception()
                else None
            )
        )

        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            logger.info("Shutdown in corso...")
        except KeyboardInterrupt:
            await self.shutdown()

    async def shutdown(self):
        """Arresta il bot in modo pulito."""
        if self._shutdown_initiated:
            logger.warning("Shutdown già in corso, ignoro richiesta duplicata")
            return

        self._shutdown_initiated = True
        self._running = False
        self._shutdown_event.set()

        logger.info("Arresto bot...")

        self.audio_player.stop()

        if hasattr(self, "_queue_task") and not self._queue_task.done():
            self._queue_task.cancel()
            try:
                await asyncio.wait_for(self._queue_task, timeout=3.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        await self._persist_queue()

        try:
            await asyncio.wait_for(self.twitch_handler.disconnect(), timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning("Timeout disconnessione Twitch, forzato")

        self.executor.shutdown(wait=False, cancel_futures=True)

        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)
        except Exception:
            pass

        logger.info("Bot arrestato correttamente")
