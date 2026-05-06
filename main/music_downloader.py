#!/usr/bin/env python3
"""
Music Downloader Module

Gestisce il download di audio da YouTube usando yt-dlp.
Filtra per categoria "Music" e durata massima.
"""

import copy
import os
import re
import subprocess
import threading
import time
import random
from typing import Optional, Dict, Any
import yt_dlp
from loguru import logger

from main.config import (
    DOWNLOAD_DIR,
    MAX_DURATION_SECONDS,
    AUDIO_QUALITY,
    AUDIO_FORMAT,
    YOUTUBE_CATEGORY,
    DOWNLOAD_TIMEOUT,
)


class _SongTooLongError(Exception):
    """Tutti i candidati trovati superano la durata massima."""
    pass


class _CategoryError(Exception):
    """Il video non appartiene alla categoria Music."""
    pass


class _NoValidCandidateError(Exception):
    """Nessun candidato valido trovato tra i risultati della ricerca."""
    pass


class MusicDownloader:
    """Classe per gestire il download di musica da YouTube."""

    def __init__(self):
        """Inizializza il MusicDownloader."""
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        self._ydl_opts = self._get_ydl_options()

    def _get_ydl_options(self) -> Dict[str, Any]:
        """Configura le opzioni di yt-dlp."""
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
        """Opzioni leggere per estrarre solo metadati, senza vincoli di formato."""
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
        """Estrae le informazioni di un video senza scaricarlo."""
        try:
            # FIX: usa _get_info_opts() invece di _ydl_opts per l'estrazione
            # dei metadati. _ydl_opts ha vincoli di formato (format_sort, codec)
            # che possono rifiutare video validi durante il solo fetch dei metadati.
            with yt_dlp.YoutubeDL(self._get_info_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Errore yt-dlp nell'estrazione info per '{url}': {e}")
            return None
        except Exception as e:
            logger.error(f"Errore imprevisto nell'estrazione info per '{url}': {e}", exc_info=True)
            return None

    def _validate_song(self, info: Dict[str, Any]) -> tuple[bool, str]:
        """Valida se la canzone rispetta i criteri."""
        # Verifica durata
        duration = info.get("duration", 0)
        if not duration:
            return False, "Durata non disponibile"
        if duration > MAX_DURATION_SECONDS:
            return (
                False,
                f"Canzone troppo lunga ({duration}s > {MAX_DURATION_SECONDS}s)",
            )

        # Verifica categoria (Music) - le categorie sono una lista
        categories = info.get("categories", [])
        if not any("music" in c.lower() for c in categories):
            cat_str = ", ".join(categories) if categories else "nessuna categoria"
            return False, (
                f"Il video è nella categoria '{cat_str}', non 'Music'. "
                f"Sono accettate solo canzoni."
            )

        return True, ""

    def _is_url(self, text: str) -> bool:
        """Verifica se il testo è un URL YouTube."""
        url_pattern = r"https?://(www\.)?youtube\.com/|https?://youtu\.be/"
        return bool(re.search(url_pattern, text, re.IGNORECASE))

    def _search_youtube(self, query: str) -> Optional[str]:
        """Cerca una canzone su YouTube e ritorna l'URL del primo risultato."""
        candidates = self._search_youtube_candidates(query, max_results=1)
        return candidates[0] if candidates else None

    def _search_youtube_candidates(self, query: str, max_results: int = 5) -> list[str]:
        """Cerca su YouTube e ritorna fino a max_results URL candidati.

        Restituisce più risultati invece di uno solo, così download() può
        provare il successivo se un video non è disponibile (geo-block, ecc.).
        """
        return [url for url, _ in self._search_youtube_candidates_with_info(query, max_results)]

    def _search_youtube_candidates_with_info(
        self, query: str, max_results: int = 5
    ) -> list[tuple[str, Dict[str, Any]]]:
        """Cerca su YouTube e ritorna fino a max_results coppie (url, info).

        Restituisce le info già fetchate dalla ricerca così download() può
        validare i candidati senza un secondo round-trip per ogni video.
        La durata è quasi sempre presente nei risultati di ytsearch.
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
            logger.warning(f"Errore nella ricerca YouTube per '{query}': {e}")
        return results

    def get_video_info(self, query_or_url: str) -> Optional[Dict[str, Any]]:
        """Ottiene informazioni su un video senza scaricarlo."""
        url = query_or_url

        if not self._is_url(query_or_url):
            url = self._search_youtube(query_or_url)
            if not url:
                logger.error(f"Nessun risultato trovato per: '{query_or_url}'")
                return None

        info = self._extract_info(url)
        if not info:
            return None

        is_valid, error_msg = self._validate_song(info)
        if not is_valid:
            logger.warning(f"Canzone non valida per '{query_or_url}': {error_msg}")
            return None

        return info

    def download(self, query_or_url: str) -> Optional[str]:
        """
        Scarica una canzone da YouTube.

        Args:
            query_or_url: Titolo della canzone o URL YouTube

        Returns:
            Percorso del file scaricato o None in caso di errore
        """
        # Se è un URL diretto usa solo quello; se è una query testo
        # recupera più candidati e prova in ordine finché uno è disponibile.
        # FIX: usiamo _search_youtube_candidates_with_info per ottenere le info
        # già fetchate dalla ricerca (inclusa la duration), evitando un secondo
        # round-trip per ogni video che causava "Durata non disponibile" su tutti.
        if self._is_url(query_or_url):
            candidates_with_info: list[tuple[str, Optional[Dict[str, Any]]]] = [
                (query_or_url, None)
            ]
        else:
            raw = self._search_youtube_candidates_with_info(query_or_url, max_results=10)
            if not raw:
                logger.error(f"Nessun risultato trovato per: '{query_or_url}'")
                return None
            candidates_with_info = raw  # type: ignore[assignment]

        info: Optional[Dict[str, Any]] = None
        url: Optional[str] = None
        rejection_reasons: list[str] = []

        for candidate, prefetched_info in candidates_with_info:
            # Usa le info già fetchate dalla ricerca se disponibili;
            # fa un fetch separato solo per URL diretti o se mancano.
            candidate_info = prefetched_info
            if not candidate_info or not candidate_info.get("duration"):
                candidate_info = self._extract_info(candidate)
            if not candidate_info:
                rejection_reasons.append("non disponibile")
                logger.warning(
                    f"Info non disponibili per '{candidate}', provo il prossimo"
                )
                continue
            is_valid, error_msg = self._validate_song(candidate_info)
            if not is_valid:
                rejection_reasons.append(error_msg)
                logger.warning(
                    f"Candidato scartato '{candidate}': {error_msg}, provo il prossimo"
                )
                continue
            info = candidate_info
            url = candidate
            break

        if not info or not url:
            num_tried = len(candidates_with_info)

            # Se tutti i candidati sono stati rifiutati, solleva un'eccezione
            # con il primo motivo significativo trovato.
            if rejection_reasons:
                all_too_long = all("troppo lunga" in r for r in rejection_reasons)
                all_wrong_category = all("categoria" in r for r in rejection_reasons)

                if all_too_long:
                    logger.error(
                        f"Tutti i {num_tried} risultati per '{query_or_url}' "
                        f"superano la durata massima ({MAX_DURATION_SECONDS}s)."
                    )
                    raise _SongTooLongError(
                        f"Tutti i risultati trovati sono troppo lunghi "
                        f"(max {MAX_DURATION_SECONDS // 60} min). "
                        f"Cerca una traccia specifica, non l'intera soundtrack."
                    )

                if all_wrong_category:
                    first_reason = next(
                        (r for r in rejection_reasons if "categoria" in r), ""
                    )
                    logger.error(
                        f"Tutti i {num_tried} risultati per '{query_or_url}' "
                        f"non sono nella categoria {YOUTUBE_CATEGORY}."
                    )
                    raise _CategoryError(
                        first_reason
                        or f"Il video non è nella categoria {YOUTUBE_CATEGORY}. "
                           f"Sono accettate solo canzoni."
                    )

                # Fallback su motivi misti: prendi il primo motivo significativo
                meaningful = next(
                    (r for r in rejection_reasons if r != "non disponibile"),
                    rejection_reasons[0],
                )
                logger.error(
                    f"Nessun candidato valido per '{query_or_url}' "
                    f"({num_tried} provati, motivi: {rejection_reasons})"
                )
                raise _NoValidCandidateError(meaningful)

            logger.error(
                f"Nessun candidato valido trovato per '{query_or_url}' "
                f"({num_tried} provati, nessun motivo di rifiuto registrato)"
            )
            return None

        # Controlla se il file esiste già su disco confrontando il titolo esatto
        # del video YouTube con i file presenti. Non usiamo _find_matching_file
        # (fuzzy) perché produce falsi positivi: token corti come "-" o "ft"
        # matchano per substring qualsiasi file nella cartella.
        video_title = info.get("title", "").strip()
        if video_title:
            title_safe = re.sub(r'[<>:"/\\|?*]', "_", video_title)[:100]
            for ext in [f".{AUDIO_FORMAT}", ".mp3", ".m4a", ".webm"]:
                expected = os.path.join(DOWNLOAD_DIR, f"{title_safe}{ext}")
                if os.path.exists(expected):
                    logger.info(
                        f"File già presente su disco per '{query_or_url}' → '{expected}'"
                    )
                    return expected

        # Scarica il file
        try:
            # FIX: usa deepcopy per evitare che chiamate concorrenti condividano
            # la stessa lista di postprocessors (shallow copy non è sufficiente).
            opts = copy.deepcopy(self._ydl_opts)

            # FIX: usa il postprocessor_hook invece del progress_hook per
            # catturare il percorso DOPO che FFmpeg ha completato la conversione.
            # Il progress_hook con status="finished" scatta quando il download
            # grezzo finisce, ma PRIMA che FFmpeg scriva il file .mp3.
            final_path: list[str] = []
            download_exception: list[Exception] = []

            def postprocessor_hook(d: Dict[str, Any]) -> None:
                if d.get("status") == "finished":
                    filepath = d.get("info_dict", {}).get("filepath") or d.get("filepath")
                    if filepath and os.path.exists(filepath):
                        final_path.append(filepath)
                        logger.debug(f"Postprocessor completato: {filepath}")

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
                logger.error(f"Timeout download (10 min) per: '{query_or_url}'")
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
                    f"Postprocessor ha restituito un percorso inesistente: {path}"
                )

            # Fallback 1: attendi brevemente e cerca per titolo
            title = info.get("title", "unknown").strip()
            title_safe = re.sub(r'[<>:"/\\|?*]', "_", title)[:100]
            for ext in [f".{AUDIO_FORMAT}", ".mp3", ".m4a", ".webm"]:
                file_path = os.path.join(DOWNLOAD_DIR, f"{title_safe}{ext}")
                if os.path.exists(file_path):
                    logger.info(f"File trovato via fallback titolo: {file_path}")
                    return file_path

            # Fallback 2: attendi che FFmpeg finisca di scrivere (max 5s)
            for attempt in range(10):
                time.sleep(0.5)
                for ext in [f".{AUDIO_FORMAT}", ".mp3", ".m4a", ".webm"]:
                    file_path = os.path.join(DOWNLOAD_DIR, f"{title_safe}{ext}")
                    if os.path.exists(file_path):
                        logger.info(
                            f"File trovato dopo attesa ({attempt + 1} tentativi): {file_path}"
                        )
                        return file_path

            logger.error(
                f"Download completato ma file non trovato per '{query_or_url}' "
                f"(titolo atteso: '{title_safe}')"
            )
            return None

        except Exception as e:
            logger.error(
                f"Errore nel download di '{query_or_url}': {type(e).__name__}: {e}",
                exc_info=True,
            )
            return None

    def get_random_downloaded_file(self) -> Optional[str]:
        """Sceglie un file audio casuale dalla cartella di download."""
        try:
            files = os.listdir(DOWNLOAD_DIR)
            audio_files = [
                f for f in files if f.lower().endswith((".mp3", ".wav", ".m4a"))
            ]
            if not audio_files:
                return None

            random_file = random.choice(audio_files)
            return os.path.join(DOWNLOAD_DIR, random_file)
        except Exception as e:
            logger.error(f"Errore durante la scelta del file casuale: {e}")
            return None

    def get_search_results(
        self, query: str, max_results: int = 5
    ) -> list[Dict[str, str]]:
        """Cerca canzoni e ritorna una lista di risultati."""
        search_query = f"ytsearch{max_results}:{query}"
        results = []

        try:
            with yt_dlp.YoutubeDL(self._get_info_opts()) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if info and "entries" in info:
                    for entry in info["entries"]:
                        results.append(
                            {
                                "title": entry.get("title", ""),
                                "url": entry.get("url", ""),
                                "duration": entry.get("duration", 0),
                            }
                        )
        except Exception as e:
            logger.error(f"Errore nella ricerca per '{query}': {e}")

        return results

    def _get_local_file_duration(self, file_path: str) -> Optional[int]:
        """Ottiene la durata di un file audio locale usando ffprobe."""
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
        """Trova un file locale che corrisponde alla query."""
        try:
            files = os.listdir(DOWNLOAD_DIR)
            audio_extensions = (".mp3", ".m4a", ".wav", ".webm", ".flac", ".ogg")
            query_lower = query.lower()

            for filename in files:
                if not filename.lower().endswith(audio_extensions):
                    continue

                name_without_ext = os.path.splitext(filename)[0].lower()
                words = query_lower.split()
                matched_words = sum(1 for w in words if w in name_without_ext)

                if matched_words >= max(1, len(words) * 0.5):
                    return os.path.join(DOWNLOAD_DIR, filename)
        except OSError as e:
            logger.debug(f"Errore nella ricerca file locale: {e}")
        return None

    def get_song_info(self, query_or_url: str) -> Optional[Dict[str, Any]]:
        """Ottiene informazioni dettagliate su una canzone (titolo, durata, artista)."""
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
            logger.warning(f"Errore nell'estrazione info per '{query_or_url}': {e}")
            return {"title": query_or_url, "duration": 0, "uploader": ""}
