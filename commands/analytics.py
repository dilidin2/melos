"""Analytics Commands - Comandi per statistiche e analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main.analytics import Analytics


class AnalyticsCommands:
    """Gestisce tutti i comandi di statistica."""

    def __init__(self, analytics: Analytics):
        self.analytics = analytics

    async def cmd_stats(self, username: str) -> str:
        """!stats - Mostra statistiche generali."""
        total_requests = self.analytics.get_total_requests()
        total_plays = self.analytics.get_total_plays()

        today = self.analytics.get_stats_today()
        week = self.analytics.get_stats_week()

        lines = [
            f"📊 Statistiche Bot:",
            f"  • Totale richieste: {total_requests}",
            f"  • Totale riproduzioni: {total_plays}",
            f"  • Oggi: {today['total_requests_today']} richieste",
            f"  • Questa settimana: {week['total_requests_week']} richieste",
        ]

        return "\n".join(lines)

    async def cmd_top_canzoni(self, username: str, n: int = 10) -> str:
        """!top_canzoni [numero] - Mostra le N canzoni più richieste."""
        songs = self.analytics.get_top_songs(n)

        if not songs:
            return "📭 Nessuna statistica disponibile."

        lines = [f"🎵 Top {n} Canzoni Richieste:"]
        for i, song in enumerate(songs, 1):
            lines.append(f"  {i}. {song['title']} - {song['count']} volte")

        return "\n".join(lines)

    async def cmd_top_user(self, username: str, n: int = 10) -> str:
        """!top_user [numero] - Mostra gli utenti con più richieste."""
        users = self.analytics.get_top_users(n)

        if not users:
            return "📭 Nessuna statistica disponibile."

        lines = [f"👥 Top {n} Utenti:"]
        for i, user in enumerate(users, 1):
            lines.append(f"  {i}. @{user['username']} - {user['count']} richieste")

        return "\n".join(lines)

    async def cmd_export_stats(self, username: str, format: str = "json") -> str:
        """!export_stats <formato> - Esporta le statistiche."""
        export = self.analytics.export_stats(format)

        if format == "json":
            return f"📦 Statistiche esportate:\n```json\n{export}\n```"
        else:
            return f"```\n{export}\n```"
