import os
import time
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
    VOTE_REQUIRED_COUNT,
    SONG_PRECHECK_TIMEOUT,
)

from main.music_downloader import (
    MusicDownloader,
    _SongTooLongError,
    _CategoryError,
    _NoValidCandidateError,
    _ChannelNotTrustedError,
)
from main.audio_player import AudioPlayer
from main.twitch_handler import TwitchHandler
from main.chat_message import ChatMessage
from main.queue_persistence import QueuePersistence

from loguru import logger


@dataclass
class SongRequest:
    """Represents a song request."""

    query: str
    username: str
    channel_id: str
    request_id: int
    added_at: Optional[str] = None
    resolved_title: Optional[str] = None
    resolved_duration: Optional[int] = None
    # Set by the pre-request precheck (NOT persisted — after a restart the
    # normal download flow re-resolves everything).
    resolved_file: Optional[str] = None   # local file found by precheck
    resolved_url: Optional[str] = None    # YouTube URL found by precheck


class RequestQueue:
    """Manages the request queue.

    Thread-safety note: asyncio is single-threaded, so true concurrent access
    never happens. The lock here protects against logical races at await
    boundaries — e.g. an admin command swapping the internal deque while
    _queue_processor has a reference to it between get() and task_done().

    Pragmatic choice: we mutate the existing asyncio.Queue in-place (via its
    internal _queue deque) rather than replacing self.queue with a new object.
    This guarantees that any coroutine holding a reference to the old Queue
    still operates on the same underlying data structure, avoiding stale-
    reference bugs with task_done().
    """

    def __init__(self, max_size: int = 999):
        self.queue: asyncio.Queue[SongRequest] = asyncio.Queue(maxsize=max_size)
        self.max_size = max_size
        self._request_counter = 0
        self._in_progress = False
        self._lock = asyncio.Lock()

    async def put(self, request: SongRequest) -> bool:
        """Adds a request to the queue."""
        try:
            await asyncio.wait_for(self.queue.put(request), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Queue full, request rejected: {request.query}")
            return False

    async def get(self) -> Optional[SongRequest]:
        """Returns the next request."""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def task_done(self):
        """Marks a request as completed."""
        self.queue.task_done()

    def qsize(self) -> int:
        """Returns the queue size."""
        return self.queue.qsize()

    def is_processing(self) -> bool:
        """Returns True if a request is being processed."""
        return self._in_progress

    def get_items(self, count: int = 10) -> list[SongRequest]:
        """Returns the next N requests without removing them from the queue."""
        return list(self.queue._queue)[:count]

    async def clear(self):
        """Svuota completamente la coda.

        Mutates the existing Queue in-place (no reference swap) so that any
        coroutine holding a stale reference still sees an empty deque.
        Protected by _lock to prevent races with remove_by_index / get_items.
        """
        async with self._lock:
            self.queue._queue.clear()

    async def remove_by_index(self, index: int) -> Optional[SongRequest]:
        """Rimuove un elemento alla posizione data (0-based).

        Returns the removed SongRequest, or None if the index is out of range.
        Mutates in-place and protected by _lock.
        """
        async with self._lock:
            items = self.queue._queue  # the internal deque
            if index < 0 or index >= len(items):
                return None
            # deque.rotate + popleft is O(k) where k=index, which is fine for
            # queue sizes < 1000. Avoids creating a new list/deque.
            items.rotate(-index)
            removed = items.popleft()
            items.rotate(index)
            return removed

    async def get_all_items(self) -> list[SongRequest]:
        """Restituisce TUTTI gli elementi senza rimuoverli.

        Protected by _lock so _persist_queue never reads during a mutation.
        """
        async with self._lock:
            return list(self.queue._queue)


class DuplicateCache:
    """Cache to avoid duplicate downloads."""

    def __init__(self, max_size: int = 100):
        self.cache: dict[str, tuple[str, str]] = {}
        self.max_size = max_size

    def add(self, query: str, file_path: str, username: str) -> None:
        """Adds a song to the cache."""
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        self.cache[query.lower()] = (file_path, username)

    def get(self, query: str) -> Optional[tuple[str, str]]:
        """Returns the song if already downloaded."""
        return self.cache.get(query.lower())

    def remove(self, query: str) -> None:
        """Removes a song from the cache."""
        self.cache.pop(query.lower(), None)


class SongRequestBot:
    """Main bot for music requests."""

    def __init__(self, audio_device=None, admin_handler=None):
        """Initializes the bot."""
        self.music_downloader = MusicDownloader(admin_handler=admin_handler)
        self.audio_player = AudioPlayer(device_name=audio_device)
        self.twitch_handler = TwitchHandler()
        self.chat_message = ChatMessage(self.twitch_handler)
        self.admin_handler = admin_handler
        self.request_queue = RequestQueue()
        self.duplicate_cache = DuplicateCache()
        self._running = False
        self._processing_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._shutdown_initiated = False
        self._shutdown_task: Optional[asyncio.Task] = None
        self._request_counter = 0

        # Repeat mode settings
        self.repeat_mode = 'off'  # 'off', 'count', 'infinite'
        self.repeat_count = 1     # Number of repetitions if repeat_mode='count'
        self.repeat_remaining = 0 # Remaining count for repeat

        # Tracks the last random song played to avoid consecutive repetitions
        self.last_random_song: Optional[str] = None

        # Vote-to-skip tracking for the currently playing song
        self._vote_skip_voters: set[str] = set()
        self._vote_active: bool = False

        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

        self.queue_persistence = QueuePersistence()
        # Bot start time for uptime tracking
        self._start_time = time.time()

    async def _handle_song_request(self, query: str, username: str, channel_id: str):
        """Handles a music request.

        Inverted flow (search FIRST, queue SECOND):
          1. precheck: local database check → online YouTube search + validation
          2. if the song is found (local or online) → add to queue and reply
             with the RESOLVED title, so the name the user sees here is the
             same one shown by "Now Playing" later.
          3. if the song is not found / rejected → clear chat message, and the
             song is NOT added to the queue.
        """
        # Block blacklisted users from requesting songs
        if self.admin_handler and self.admin_handler.is_blacklisted(username):
            await self.chat_message.send_public(
                channel_id,
                f"🚫 @{username} is blacklisted and cannot request songs.",
            )
            return

        if hasattr(self, "analytics"):
            self.analytics.record_request(username, query)

        # ── 1) Precheck: check local database, then online (no download) ──
        try:
            result = await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    self.executor, self.music_downloader.precheck, query
                ),
                timeout=SONG_PRECHECK_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Precheck timed out after {SONG_PRECHECK_TIMEOUT}s "
                f"for '{query}' from @{username}"
            )
            await self.chat_message.send_error(
                channel_id,
                username,
                f"Search timed out for '{query}'. Nothing was added, try again later.",
            )
            return
        except Exception as e:
            logger.error(
                f"Precheck failed for '{query}' from @{username}: "
                f"{type(e).__name__}: {e}",
                exc_info=True,
            )
            await self.chat_message.send_error(
                channel_id,
                username,
                f"Search failed for '{query}'. Nothing was added, try again later.",
            )
            return

        # ── 2) Song not found or rejected: clear message, NOT queued ──
        if result["status"] not in ("local", "ok"):
            logger.info(
                f"Request rejected by precheck ({result['status']}): "
                f"'{query}' from @{username}"
            )
            await self.chat_message.send_error(channel_id, username, result["error"])
            return

        # ── 3) Song found: proceed normally, keep resolved metadata ──
        request = SongRequest(query, username, channel_id, self._request_counter)
        self._request_counter += 1
        request.resolved_title = result.get("title")
        request.resolved_duration = result.get("duration")
        if result["status"] == "local":
            request.resolved_file = result.get("file_path")
        else:
            request.resolved_url = result.get("url")

        success = await self.request_queue.put(request)
        if not success:
            await self.chat_message.send_error(
                channel_id, username, "Queue full, try again later."
            )
            return

        position = self.request_queue.qsize()
        display_title = request.resolved_title or query
        logger.info(
            f"Request added to queue: {query} → {display_title} (from @{username})"
        )

        await self.chat_message.send_public(
            channel_id,
            f"✅ Added **{display_title}** to queue at position {position}",
        )

        await self._persist_queue()
        self._shutdown_event.clear()

    async def _persist_queue(self):
        """Converts the current queue to JSON and saves it."""
        items = await self.request_queue.get_all_items()

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
        """Restores the queue from file on startup."""
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
                logger.info(f"🔄 Restored from persistence: {request.query}")
            except asyncio.QueueFull:
                logger.warning("Queue full during restore")
                break

    async def _play_audio_file(
        self, channel_id: str, file_path: str, notification_text: Optional[str] = None
    ):
        """Plays an audio file and sends the playback notification."""
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
            logger.error(f"Error playing '{file_path}': {e}", exc_info=True)
            return False

    async def _process_request(self, request: SongRequest) -> bool:
        """Processes a single request."""
        # NOTE: _in_progress flag + _processing_lock work correctly today because
        # _queue_processor runs as a single asyncio task. If download/playback is
        # ever parallelized (e.g. pre-caching), this pattern must be replaced with
        # a semaphore or event-based coordination to avoid race conditions.
        async with self._processing_lock:
            if self.request_queue.is_processing():
                logger.warning(
                    f"Already processing, request ignored: '{request.query}' from @{request.username}"
                )
                await self.chat_message.send_error(
                    request.channel_id,
                    request.username,
                    "A song is already playing. Try again later.",
                )
                return False

            self.request_queue._in_progress = True
            logger.info(f"Processing: '{request.query}' from @{request.username}")

        try:
            cached = self.duplicate_cache.get(request.query)
            if cached:
                file_path, _ = cached
                # FIX: verify that the cached file still exists on disk
                if not os.path.exists(file_path):
                    logger.warning(
                        f"Cached file not found on disk, re-downloading: '{request.query}'"
                    )
                    self.duplicate_cache.remove(request.query)
                    file_path = None
                else:
                    logger.info(f"Song already downloaded, using cache: '{request.query}'")
            else:
                file_path = None

            # Precheck already found the exact local file: use it directly.
            if (
                file_path is None
                and request.resolved_file
                and os.path.exists(request.resolved_file)
            ):
                file_path = request.resolved_file

            if file_path is None:
                try:
                    # If the precheck resolved a YouTube URL, pass it directly:
                    # the search was already done at request time, so
                    # download() only validates + downloads (no second search).
                    download_target = request.resolved_url or request.query
                    file_path = await asyncio.get_running_loop().run_in_executor(
                        self.executor, self.music_downloader.download, download_target
                    )

                    if not file_path:
                        logger.warning(
                            f"Download failed (no file) for '{request.query}' from @{request.username}"
                        )
                        await self.chat_message.send_error(
                            request.channel_id,
                            request.username,
                            "Unable to download the song. Try again later.",
                        )
                        return False

                    # Use the disk filename as normalized cache key.
                    # Only one entry per file — the filename is already
                    # normalized (lowercase, no special chars), so "Bella Ciao"
                    # and "bella ciao" map to the same cached file.
                    cache_key = os.path.splitext(os.path.basename(file_path))[0]
                    self.duplicate_cache.add(cache_key, file_path, request.username)

                except _SongTooLongError as e:
                    logger.warning(
                        f"Song too long for '{request.query}' from @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except _CategoryError as e:
                    logger.warning(
                        f"Category not allowed for '{request.query}' from @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except _NoValidCandidateError as e:
                    logger.warning(
                        f"No valid candidate for '{request.query}' from @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except _ChannelNotTrustedError as e:
                    logger.warning(
                        f"Channel not trusted for '{request.query}' from @{request.username}: {e}"
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        str(e),
                    )
                    return False
                except Exception as e:
                    logger.error(
                        f"Exception downloading '{request.query}' from @{request.username}: "
                        f"{type(e).__name__}: {e}",
                        exc_info=True,
                    )
                    await self.chat_message.send_error(
                        request.channel_id,
                        request.username,
                        "Error during download. Try again later.",
                    )
                    return False

            # Resolve metadata from the file on disk — no network call needed.
            # resolved_title/duration were usually set by the precheck at
            # request time; fill them in only when missing (e.g. requests
            # restored from persistence after a bot restart don't have them).
            if file_path and os.path.exists(file_path):
                if not request.resolved_title:
                    request.resolved_title = os.path.splitext(os.path.basename(file_path))[0]
                if not request.resolved_duration:
                    request.resolved_duration = self.music_downloader._get_local_file_duration(file_path)

            # Reset votes for the new song
            self.reset_votes()
            self._vote_active = True

            notification = f"{request.resolved_title or request.query} - @{request.username}"
            success = await self._play_audio_file(
                request.channel_id, file_path, notification
            )

            # FIX: notify the user even in case of playback error.
            # Before, this branch was missing: if _play_audio_file returned False,
            # the bot would not send any message to chat.
            if not success:
                logger.error(
                    f"Playback failed for '{request.query}' from @{request.username} "
                    f"(file: '{file_path}')"
                )
                await self.chat_message.send_error(
                    request.channel_id,
                    request.username,
                    "Error during playback. Try again later.",
                )

            if success and hasattr(self, "analytics"):
                resolved = request.resolved_title or request.query
                self.analytics.record_play(request.username, resolved)

            return success

        finally:
            self.request_queue._in_progress = False

    def _should_repeat(self, success: bool, song_name: str) -> bool:
        """Check repeat state after playback. Returns True if the song should replay.

        Shared by queue and random-song branches to avoid duplicating
        the infinite/count/off repeat logic.
        """
        if not success:
            if self.repeat_mode != 'off':
                logger.warning(f"Playback failed, disabling repeat")
                self.repeat_mode = 'off'
                self.repeat_remaining = 0
            return False

        if self.repeat_mode == 'infinite':
            logger.info(f"🔁 INFINITE repeat: repeating '{song_name}'")
            return True

        if self.repeat_mode == 'count':
            self.repeat_remaining -= 1
            if self.repeat_remaining > 0:
                logger.info(
                    f"🔁 Repeat ({self.repeat_remaining}/{self.repeat_count}): "
                    f"repeating '{song_name}'"
                )
                return True
            self.repeat_mode = 'off'
            logger.info(f"🔁 Repeat ended after {self.repeat_count} times")
            return False

        return False

    async def _queue_processor(self):
        """Continuously processes the request queue."""
        while not self._shutdown_event.is_set() or self.request_queue.qsize() > 0:
            if self._shutdown_event.is_set():
                while self.request_queue.qsize() > 0:
                    try:
                        req = await self.request_queue.get()
                        if req:
                            self.request_queue.task_done()
                            logger.info(f"Queue drained: {req.query}")
                    except Exception:
                        break
                break

            request = await self.request_queue.get()

            if request:
                # Save which song is "the one to repeat" at the time of get
                repeat_target = request

                while True:  # ← inner loop for repeat
                    success = await self._process_request(repeat_target)
                    if not self._should_repeat(success, repeat_target.query):
                        await self._persist_queue()
                        break

                # At the end of the inner loop (repeat ended or failed),
                # signal completion of the original request
                self.request_queue.task_done()

            else:
                if not self._shutdown_event.is_set():
                    # Picks a random song from downloads/ avoiding the same one twice in a row
                    try:
                        import random as random_module
                        files = os.listdir(DOWNLOAD_DIR)
                        audio_files = [
                            f for f in files if f.lower().endswith((".mp3", ".wav", ".m4a"))
                        ]

                        if not audio_files:
                            await asyncio.sleep(1)
                            continue

                        # If there's a last song played, filter to avoid consecutive repetitions
                        if self.last_random_song:
                            available = [f for f in audio_files if f != self.last_random_song]
                            if not available:
                                available = audio_files
                        else:
                            available = audio_files

                        selected = random_module.choice(available)
                        random_file = os.path.join(DOWNLOAD_DIR, selected)
                        song_name = os.path.splitext(selected)[0]

                        self.reset_votes()
                        self._vote_active = True
                        while True:
                            notification = f"Playing random: {song_name}"
                            success = await self._play_audio_file(
                                TARGET_CHANNEL, random_file, notification
                            )
                            if not self._should_repeat(success, song_name):
                                break

                        # Record random song in analytics
                        if success and hasattr(self, "analytics"):
                            self.analytics.record_play("random", song_name)

                        self.last_random_song = selected
                    except Exception as e:
                        logger.error(f"Error selecting random song: {e}")
                        await asyncio.sleep(1)

            await asyncio.sleep(0.1)

    def skip_current_song(self) -> bool:
        """Stops current playback to move to the next."""
        if not self.audio_player.is_playing():
            return False

        self.audio_player.stop()
        self.reset_votes()
        return True

    def process_vote(self, username: str) -> bool:
        """Registers a vote to skip the currently playing song.

        Returns True if the required number of votes was reached and the song should be skipped.
        """
        self._vote_skip_voters.add(username.lower())
        return len(self._vote_skip_voters) >= VOTE_REQUIRED_COUNT

    def reset_votes(self):
        """Resets vote tracking for a new song."""
        self._vote_skip_voters.clear()
        self._vote_active = False

    def _signal_handler(self):
        """Handler for SIGINT/SIGTERM."""
        if not self._shutdown_initiated:
            logger.info("Shutdown signal received (Ctrl+C)")
            self._shutdown_task = asyncio.create_task(self.shutdown())

    async def run(self):
        """Starts the bot."""
        self._running = True

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)

        self.twitch_handler.set_command_callback(self._handle_song_request)
        await self._load_persisted_queue()

        if not await self.twitch_handler.connect():
            logger.error("Unable to connect to Twitch")
            return

        logger.info(f"Bot active on channel @{TARGET_CHANNEL}")
        logger.info("Listening for !sr commands... (Ctrl+C to exit)")

        self._queue_task = asyncio.create_task(self._queue_processor())
        self._queue_task.add_done_callback(
            lambda t: (
                logger.error(f"Queue processor died: {t.exception()}")
                if not t.cancelled() and t.exception()
                else None
            )
        )

        try:
            await self._shutdown_event.wait()
            # _shutdown_event is set near the START of shutdown(), as a
            # signal to stop accepting new work — it does NOT mean cleanup
            # (twitch disconnect, queue persistence, executor shutdown) has
            # finished. When shutdown() was launched as a detached task from
            # _signal_handler (a real Ctrl+C), we must wait for that task to
            # fully complete here. Otherwise this coroutine (and therefore
            # main()) returns immediately, asyncio.run() starts its teardown,
            # and forcibly cancels the still-running shutdown task mid-cleanup
            # — which can hang forever if it's currently inside a blocking,
            # non-cooperative call like executor.shutdown(wait=True).
            if self._shutdown_task is not None:
                await self._shutdown_task
        except asyncio.CancelledError:
            logger.info("Shutdown in progress...")
        except KeyboardInterrupt:
            await self.shutdown()

    async def shutdown(self):
        """Stops the bot cleanly."""
        if self._shutdown_initiated:
            logger.warning("Shutdown already in progress, ignoring duplicate request")
            return

        self._shutdown_initiated = True
        self._running = False
        self._shutdown_event.set()

        logger.info("Stopping bot...")

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
            logger.warning("Twitch disconnect timeout, forced")

        # Give the executor thread time to see audio_player._stop_event
        # before we shut down the pool. Without this sleep the thread is still
        # inside time.sleep(0.1) in AudioPlayer.play() and wait=True would
        # block for up to ~100 ms anyway; an explicit sleep makes it predictable.
        await asyncio.sleep(0.3)
        self.executor.shutdown(wait=True, cancel_futures=True)

        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)
        except Exception:
            pass

        logger.info("Bot stopped successfully")
