"""Analytics - Sistema di statistica e tracking."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


class Analytics:
    """Gestisce le statistiche e l'analytics del bot."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._stats_file = self.data_dir / "stats.json"
        self._load_stats()

    def _load_stats(self):
        """Carica le statistiche dal disco."""
        if self._stats_file.exists():
            try:
                with open(self._stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._total_requests = data.get("total_requests", 0)
                    self._total_plays = data.get("total_plays", 0)
                    self._songs_by_user = data.get("songs_by_user", {})
                    self._songs_by_title = data.get("songs_by_title", {})
                    self._play_history = data.get("play_history", [])
            except (json.JSONDecodeError, KeyError):
                self._reset_stats()
        else:
            self._reset_stats()

    def _save_stats(self):
        """Salva le statistiche sul disco."""
        data = {
            "total_requests": self._total_requests,
            "total_plays": self._total_plays,
            "songs_by_user": self._songs_by_user,
            "songs_by_title": self._songs_by_title,
            "play_history": self._play_history[-1000:],  # Mantieni ultimi 1000
        }

        with open(self._stats_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _reset_stats(self):
        """Resetta le statistiche."""
        self._total_requests = 0
        self._total_plays = 0
        self._songs_by_user = {}
        self._songs_by_title = {}
        self._play_history = []

    def record_request(self, username: str, query: str):
        """Registra una richiesta di canzone."""
        self._total_requests += 1

        # Aggiorna conteggio per utente
        user_lower = username.lower()
        self._songs_by_user[user_lower] = self._songs_by_user.get(user_lower, 0) + 1

        # Aggiorna conteggio per titolo
        query_lower = query.lower()
        self._songs_by_title[query_lower] = self._songs_by_title.get(query_lower, 0) + 1

        self._save_stats()

    def record_play(self, username: str, query: str):
        """Registra una riproduzione completata."""
        self._total_plays += 1

        # Aggiungi alla cronologia
        self._play_history.append(
            {
                "username": username,
                "query": query,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self._save_stats()

    def get_total_requests(self) -> int:
        """Ottieni il totale delle richieste."""
        return self._total_requests

    def get_total_plays(self) -> int:
        """Ottieni il totale delle riproduzioni."""
        return self._total_plays

    def get_top_songs(self, n: int = 10) -> list[dict]:
        """Ottieni le N canzoni più richieste."""
        sorted_songs = sorted(
            self._songs_by_title.items(), key=lambda x: x[1], reverse=True
        )[:n]

        return [{"title": title, "count": count} for title, count in sorted_songs]

    def get_top_users(self, n: int = 10) -> list[dict]:
        """Ottieni gli N utenti con più richieste."""
        sorted_users = sorted(
            self._songs_by_user.items(), key=lambda x: x[1], reverse=True
        )[:n]

        return [{"username": user, "count": count} for user, count in sorted_users]

    def get_stats_today(self) -> dict:
        """Ottieni statistiche per oggi."""
        today = datetime.now().date()

        today_plays = []
        for play in self._play_history:
            play_date = datetime.fromisoformat(play["timestamp"]).date()
            if play_date == today:
                today_plays.append(play)

        return {
            "date": today.isoformat(),
            "total_requests_today": len(today_plays),
            "unique_users_today": len(set(p["username"] for p in today_plays)),
        }

    def get_stats_week(self) -> dict:
        """Ottieni statistiche per questa settimana."""
        week_ago = datetime.now() - timedelta(days=7)

        week_plays = []
        for play in self._play_history:
            play_date = datetime.fromisoformat(play["timestamp"])
            if play_date >= week_ago:
                week_plays.append(play)

        return {
            "period": "last_7_days",
            "total_requests_week": len(week_plays),
            "unique_users_week": len(set(p["username"] for p in week_plays)),
        }

    def get_stats_month(self) -> dict:
        """Ottieni statistiche per questo mese."""
        month_ago = datetime.now() - timedelta(days=30)

        month_plays = []
        for play in self._play_history:
            play_date = datetime.fromisoformat(play["timestamp"])
            if play_date >= month_ago:
                month_plays.append(play)

        return {
            "period": "last_30_days",
            "total_requests_month": len(month_plays),
            "unique_users_month": len(set(p["username"] for p in month_plays)),
        }

    def get_play_history(self, n: int = 20) -> list[dict]:
        """Ottiene le ultime N riproduzioni dalla cronologia."""
        return self._play_history[-n:]
