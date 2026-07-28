#!/usr/bin/env python3
"""
Music Downloader Module

Handles audio downloading from YouTube using yt-dlp.
Filters by "Music" category and maximum duration.
"""

import copy
import os
import re
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Optional, Dict, Any
import yt_dlp
from loguru import logger

if TYPE_CHECKING:
    from main.admin_handler import AdminHandler

from main.config import (
    DOWNLOAD_DIR,
    MAX_DURATION_SECONDS,
    AUDIO_QUALITY,
    AUDIO_FORMAT,
    YOUTUBE_CATEGORY,
    DOWNLOAD_TIMEOUT,
)


class _SongTooLongError(Exception):
    """All found candidates exceed the maximum duration."""
    pass


class _CategoryError(Exception):
    """The video does not belong to the Music category."""
    pass


class _NoValidCandidateError(Exception):
    """No valid candidate found among search results."""
    pass

class _ChannelNotTrustedError(Exception):
    """The video's channel is not in the trusted channels whitelist."""
    pass


class MusicDownloader:
    """Class to handle music downloading from YouTube."""

    def __init__(self, admin_handler: Optional["AdminHandler"] = None):
        """Initializes the MusicDownloader.

        Args:
            admin_handler: Optional reference for channel whitelist checks.
        """
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        self.admin_handler = admin_handler
        self._ydl_opts = self._get_ydl_options()

    def _get_ydl_options(self) -> Dict[str, Any]:
        """Configures yt-dlp options."""
        return {
            "format": "bestaudio/best/b",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": AUDIO_FORMAT,
                    "preferredquality": str(AUDIO_QUALITY),
                }
            ],
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": DOWNLOAD_TIMEOUT,
            "noplaylist": True,
            "format_sort": ["proto:https", "br", "tbr:100"],
        }

    def _get_info_opts(self) -> Dict[str, Any]:
        """Lightweight options to extract only metadata, without format constraints."""
        return {
            # FIX: rimosso "format" e "format_sort" per non bloccare video con
            # formati non standard durante la sola estrazione dei metadati.
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": DOWNLOAD_TIMEOUT,
            "noplaylist": True,
            "skip_download": True,
            "ignore_no_formats_error": True,
        }

    def _extract_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extracts video information without downloading it."""
        try:
            # FIX: usa _get_info_opts() invece di _ydl_opts per l'estrazione
            # dei metadati. _ydl_opts ha vincoli di formato (format_sort, codec)
            # che possono rifiutare video validi durante il solo fetch dei metadati.
            with yt_dlp.YoutubeDL(self._get_info_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp error extracting info for '{url}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting info for '{url}': {e}", exc_info=True)
            return None

    def _validate_song(self, info: Dict[str, Any]) -> tuple[bool, str]:
        """Validates if the song meets the criteria."""
        # Check duration
        duration = info.get("duration", 0)
        if not duration:
            return False, "Duration not available"
        if duration > MAX_DURATION_SECONDS:
            return (
                False,
                f"Song too long ({duration}s > {MAX_DURATION_SECONDS}s)",
            )

        # Check category (Music) - categories are a list
        categories = info.get("categories", [])
        if not any("music" in c.lower() for c in categories):
            cat_str = ", ".join(categories) if categories else "no category"
            return False, (
                f"The video is in the '{cat_str}' category, not 'Music'. "
                f"Only songs are accepted."
            )

        # Check channel whitelist (if enabled)
        from main.config import CHANNEL_WHITELIST_ENABLED
        if CHANNEL_WHITELIST_ENABLED and self.admin_handler:
            trusted = self.admin_handler.get_trusted_channels()
            if not trusted:
                logger.warning(
                    "Channel whitelist is ENABLED but the list is EMPTY. "
                    "No channel will pass validation. Add channels with !trust_channel."
                )
            channel_id = info.get("channel_id") or info.get("uploader_id") or ""
            if not channel_id:
                channel_display = info.get("channel") or info.get("uploader") or "unknown"
                return False, (
                    f"Unable to identify the channel '{channel_display}'. "
                    f"Channel whitelist is active but no channel ID is available."
                )
            if not self.admin_handler.is_trusted_channel(channel_id):
                channel_display = info.get("channel") or info.get("uploader") or "unknown"
                return False, (
                    f"The channel '{channel_display}' is not in the trusted channels whitelist. "
                    f"Use !trust_channel to add it (admin only)."
                )

        return True, ""

    def _is_url(self, text: str) -> bool:
        """Checks if the text is a YouTube URL."""
        url_pattern = r"https?://(www\.)?youtube\.com/|https?://youtu\.be/"
        return bool(re.search(url_pattern, text, re.IGNORECASE))

    def _search_youtube(self, query: str) -> Optional[str]:
        """Searches for a song on YouTube and returns the first result URL."""
        candidates = self._search_youtube_candidates(query, max_results=1)
        return candidates[0] if candidates else None

    def _search_youtube_candidates(self, query: str, max_results: int = 5) -> list[str]:
        """Searches YouTube and returns up to max_results candidate URLs.

        Returns multiple results instead of just one, so download() can
        try the next one if a video is not available (geo-block, etc.).
        """
        return [url for url, _ in self._search_youtube_candidates_with_info(query, max_results)]

    def _search_youtube_candidates_with_info(
        self, query: str, max_results: int = 5
    ) -> list[tuple[str, Dict[str, Any]]]:
        """Searches YouTube and returns up to max_results (url, info) pairs.

        Returns info already fetched from search so download() can
        validate candidates without a second round-trip for each video.
        Duration is almost always present in ytsearch results.
        """
        search_query = f"ytsearch{max_results}:{query}"
        results: list[tuple[str, Dict[str, Any]]] = []
        try:
            with yt_dlp.YoutubeDL(self._get_info_opts()) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if info and "entries" in info:
                    for entry in (info["entries"] or []):
                        if not entry:
                            continue
                        url = entry.get("webpage_url") or (
                            f"https://www.youtube.com/watch?v={entry['id']}"
                            if entry.get("id") else None
                        )
                        if url:
                            results.append((url, entry))
        except Exception as e:
            logger.warning(f"Error in YouTube search for '{query}': {e}")
        return results

    def get_video_info(self, query_or_url: str) -> Optional[Dict[str, Any]]:
        """Gets information about a video without downloading it."""
        url = query_or_url

        if not self._is_url(query_or_url):
            url = self._search_youtube(query_or_url)
            if not url:
                logger.error(f"No results found for: '{query_or_url}'")
                return None

        info = self._extract_info(url)
        if not info:
            return None

        is_valid, error_msg = self._validate_song(info)
        if not is_valid:
            logger.warning(f"Invalid song for '{query_or_url}': {error_msg}")
            return None

        return info

    def download(self, query_or_url: str) -> Optional[str]:
        """
        Downloads a song from YouTube.

        Args:
            query_or_url: Song title, YouTube URL or local file path

        Returns:
            Path of the downloaded file or None in case of error
        """
        # If the query is already an existing file path, return it directly
        # (avoids unnecessary YouTube searches for !random and random playback).
        if os.path.isfile(query_or_url):
            logger.info(f"Local file found, using directly: {query_or_url}")
            return query_or_url

        # Try to find a matching file locally BEFORE any network request.
        # This is instant (regex word-boundary match on disk) and avoids
        # the YouTube round-trip for songs already in downloads/.
        if not self._is_url(query_or_url):
            local_file = self._find_matching_file(query_or_url)
            if local_file:
                logger.info(f"Local fuzzy match found: {local_file}")
                return local_file

        # If it's a direct URL, use only that; if it's a text query
        # retrieve multiple candidates and try in order until one is available.
        # FIX: we use _search_youtube_candidates_with_info to get the info
        # already fetched from the search (including duration), avoiding a second
        # round-trip for each video that caused "Duration not available" for all.
        if self._is_url(query_or_url):
            candidates_with_info: list[tuple[str, Optional[Dict[str, Any]]]] = [
                (query_or_url, None)
            ]
        else:
            raw = self._search_youtube_candidates_with_info(query_or_url, max_results=10)
            if not raw:
                logger.error(f"No results found for: '{query_or_url}'")
                return None
            candidates_with_info = raw  # type: ignore[assignment]

        info: Optional[Dict[str, Any]] = None
        url: Optional[str] = None
        rejection_reasons: list[str] = []

        for candidate, prefetched_info in candidates_with_info:
            # Use the info already fetched from the search if available;
            # do a separate fetch only for direct URLs or if missing.
            candidate_info = prefetched_info
            if not candidate_info or not candidate_info.get("duration"):
                candidate_info = self._extract_info(candidate)
            if not candidate_info:
                rejection_reasons.append("not available")
                logger.warning(
                    f"Info not available for '{candidate}', trying next"
                )
                continue
            is_valid, error_msg = self._validate_song(candidate_info)
            if not is_valid:
                rejection_reasons.append(error_msg)
                logger.warning(
                    f"Candidate rejected '{candidate}': {error_msg}, trying next"
                )
                continue
            info = candidate_info
            url = candidate
            break

        if not info or not url:
            num_tried = len(candidates_with_info)

            # Se tutti i candidati sono stati rifiutati, solleva un'eccezione
            # with the first significant reason found.
            if rejection_reasons:
                all_too_long = all("too long" in r for r in rejection_reasons)
                all_wrong_category = all("category" in r for r in rejection_reasons)

                if all_too_long:
                    logger.error(
                        f"All {num_tried} results for '{query_or_url}' "
                        f"exceed the maximum duration ({MAX_DURATION_SECONDS}s)."
                    )
                    raise _SongTooLongError(
                        f"All found results are too long "
                        f"(max {MAX_DURATION_SECONDS // 60} min). "
                        f"Search for a specific track, not the entire soundtrack."
                    )

                if all_wrong_category:
                    first_reason = next(
                        (r for r in rejection_reasons if "category" in r), ""
                    )
                    logger.error(
                        f"All {num_tried} results for '{query_or_url}' "
                        f"are not in the {YOUTUBE_CATEGORY} category."
                    )
                    raise _CategoryError(
                        first_reason
                        or f"The video is not in the {YOUTUBE_CATEGORY} category. "
                           f"Only songs are accepted."
                    )

                all_channel_not_trusted = all(
                    "not in the trusted channels whitelist" in r for r in rejection_reasons
                )
                if all_channel_not_trusted:
                    logger.error(
                        f"All {num_tried} results for '{query_or_url}' "
                        f"come from untrusted channels."
                    )
                    raise _ChannelNotTrustedError(
                        "None of the search results come from a trusted channel. "
                        "Use !trusted_channels to see authorized channels, "
                        "or ask an admin to add one with !trust_channel."
                    )

                # Fallback for mixed reasons: take the first significant reason
                meaningful = next(
                    (r for r in rejection_reasons if r != "not available"),
                    rejection_reasons[0],
                )
                logger.error(
                    f"No valid candidate for '{query_or_url}' "
                    f"({num_tried} tried, reasons: {rejection_reasons})"
                )
                raise _NoValidCandidateError(meaningful)

            logger.error(
                f"No valid candidate found for '{query_or_url}' "
                f"({num_tried} tried, no rejection reason recorded)"
            )
            return None

        # Check if the file already exists on disk by comparing the exact title
        # of the YouTube video with existing files. We don't use _find_matching_file
        # (fuzzy) because it produces false positives: short tokens like "-" or "ft"
        # match any file in the folder by substring.
        video_title = info.get("title", "").strip()
        if video_title:
            title_safe = re.sub(r'[<>:"/\\|?*]', "_", video_title)[:100]
            for ext in [f".{AUDIO_FORMAT}", ".mp3", ".m4a", ".webm"]:
                expected = os.path.join(DOWNLOAD_DIR, f"{title_safe}{ext}")
                if os.path.exists(expected):
                    logger.info(
                        f"File already present on disk for '{query_or_url}' → '{expected}'"
                    )
                    return expected

        # Download the file
        try:
            # FIX: use deepcopy to prevent concurrent calls from sharing
            # the same postprocessors list (shallow copy is not sufficient).
            opts = copy.deepcopy(self._ydl_opts)

            # FIX: use postprocessor_hook instead of progress_hook to
            # capture the path AFTER FFmpeg has completed the conversion.
            # The progress_hook with status="finished" fires when the raw download
            # finishes, but BEFORE FFmpeg writes the .mp3 file.
            final_path: list[str] = []
            download_exception: list[Exception] = []

            def postprocessor_hook(d: Dict[str, Any]) -> None:
                if d.get("status") == "finished":
                    filepath = d.get("info_dict", {}).get("filepath") or d.get("filepath")
                    if filepath and os.path.exists(filepath):
                        final_path.append(filepath)
                        logger.debug(f"Postprocessor completed: {filepath}")

            opts["postprocessor_hooks"] = [postprocessor_hook]

            def _do_download() -> None:
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                except Exception as e:
                    download_exception.append(e)

            download_thread = threading.Thread(target=_do_download, daemon=True)
            download_thread.start()
            download_thread.join(timeout=600)  # 10 minuti

            if download_thread.is_alive():
                logger.error(f"Download timeout (10 min) for: '{query_or_url}'")
                return None

            if download_exception:
                raise download_exception[0]

            # Usa il percorso catturato dal postprocessor hook
            if final_path:
                path = final_path[-1]
                if os.path.exists(path):
                    logger.info(f"Download completato: {path}")
                    return path
                logger.warning(
                    f"Postprocessor returned a non-existent path: {path}"
                )

            # Fallback 1: wait briefly and search by title
            title = info.get("title", "unknown").strip()
            title_safe = re.sub(r'[<>:"/\\|?*]', "_", title)[:100]
            for ext in [f".{AUDIO_FORMAT}", ".mp3", ".m4a", ".webm"]:
                file_path = os.path.join(DOWNLOAD_DIR, f"{title_safe}{ext}")
                if os.path.exists(file_path):
                    logger.info(f"File found via title fallback: {file_path}")
                    return file_path

            # Fallback 2: wait for FFmpeg to finish writing (max 5s)
            for attempt in range(10):
                time.sleep(0.5)
                for ext in [f".{AUDIO_FORMAT}", ".mp3", ".m4a", ".webm"]:
                    file_path = os.path.join(DOWNLOAD_DIR, f"{title_safe}{ext}")
                    if os.path.exists(file_path):
                        logger.info(
                            f"File found after waiting ({attempt + 1} attempts): {file_path}"
                        )
                        return file_path

            logger.error(
                f"Download completed but file not found for '{query_or_url}' "
                f"(expected title: '{title_safe}')"
            )
            return None

        except Exception as e:
            logger.error(
                f"Error downloading '{query_or_url}': {type(e).__name__}: {e}",
                exc_info=True,
            )
            return None

    def resolve_channel_from_query(self, query_or_url: str) -> Optional[Dict[str, str]]:
        """Resolve channel_id and channel name from a query or URL.

        Used by !trust_channel to resolve a channel from a video URL or search query.

        Returns:
            Dict with {"channel_id": ..., "channel_name": ...} or None.
        """
        url = query_or_url
        if not self._is_url(query_or_url):
            url = self._search_youtube(query_or_url)
            if not url:
                logger.warning(f"No results found for channel query: '{query_or_url}'")
                return None

        info = self._extract_info(url)
        if not info:
            logger.warning(f"Could not extract info from: '{url}'")
            return None

        channel_id = info.get("channel_id") or info.get("uploader_id")
        channel_name = info.get("channel") or info.get("uploader") or "Unknown"

        if not channel_id:
            logger.warning(f"No channel_id found in video info for: '{url}'")
            return None

        return {"channel_id": channel_id, "channel_name": channel_name}

    def _get_local_file_duration(self, file_path: str) -> Optional[int]:
        """Gets the duration of a local audio file using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "csv=p=0",
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            duration_str = result.stdout.strip()
            if duration_str:
                return int(float(duration_str))
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
            logger.debug(f"ffprobe fallito per {file_path}: {e}")
        return None

    def _find_matching_file(self, query: str) -> Optional[str]:
        """Finds a local file that matches the query.

        Uses word-boundary matching (via \b) instead of substring matching to
        avoid false positives — e.g. "ft" would match "After Tonight" with
        substring, but not with word boundaries.  Requires ALL query words to
        match; if no file satisfies this the caller (get_song_info) falls back
        to a YouTube search.  This is intentionally strict because returning
        wrong data (wrong title, wrong duration) is worse than triggering an
        extra network request.
        """
        try:
            files = os.listdir(DOWNLOAD_DIR)
            audio_extensions = (".mp3", ".m4a", ".wav", ".webm", ".flac", ".ogg")
            query_lower = query.lower()

            for filename in files:
                if not filename.lower().endswith(audio_extensions):
                    continue

                name_without_ext = os.path.splitext(filename)[0].lower()

                # Split query into words and strip non-alphanumeric chars from each.
                # This handles parentheses, brackets, etc. (e.g. "tesla (slowed electro mix)"
                # → ["tesla", "slowed", "electro", "mix"]).  Without this, raw chars like
                # '(' would create an invalid regex pattern (PatternError).
                words = [re.sub(r'[^a-z0-9]', '', w) for w in query_lower.split()]
                words = [w for w in words if w]  # drop empty strings

                # Guard against empty word list (e.g. query "???" or "-- --"):
                # without this, matched_words == 0 == len(words) → match-all.
                if not words:
                    return None

                # Every word must appear as a whole word (word-boundary match)
                matched_words = sum(
                    1 for w in words if re.search(rf"\b{w}\b", name_without_ext)
                )

                if matched_words == len(words):
                    return os.path.join(DOWNLOAD_DIR, filename)
        except OSError as e:
            logger.debug(f"Error in local file search: {e}")
        return None

    def get_song_info(self, query_or_url: str) -> Optional[Dict[str, Any]]:
        """Gets detailed information about a song (title, duration, artist)."""
        if not self._is_url(query_or_url):
            local_file = self._find_matching_file(query_or_url)

            if local_file and os.path.exists(local_file):
                duration = self._get_local_file_duration(local_file)
                title = os.path.splitext(os.path.basename(local_file))[0]
                return {
                    "title": title,
                    "duration": duration or 0,
                    "uploader": "",
                }

            url = self._search_youtube(query_or_url)
            if not url:
                return None
            query_or_url = url  # usa l'URL trovato per l'estrazione info

        try:
            info = self._extract_info(query_or_url)
            if not info:
                return None

            return {
                "title": info.get("title", query_or_url),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", ""),
            }
        except Exception as e:
            logger.warning(f"Error extracting info for '{query_or_url}': {e}")
            return {"title": query_or_url, "duration": 0, "uploader": ""}
