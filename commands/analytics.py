"""Analytics Commands - Commands for statistics and analytics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main.analytics import Analytics


class AnalyticsCommands:
    """Handles all statistics commands."""

    def __init__(self, analytics: Analytics):
        self.analytics = analytics

    async def cmd_stats(self, username: str) -> str:
        """!stats - Shows general statistics."""
        total_requests = self.analytics.get_total_requests()
        total_plays = self.analytics.get_total_plays()

        today = self.analytics.get_stats_today()
        week = self.analytics.get_stats_week()

        lines = [
            f"📊 Bot Statistics:",
            f"  • Total requests: {total_requests}",
            f"  • Total plays: {total_plays}",
            f"  • Today: {today['total_requests_today']} requests",
            f"  • This week: {week['total_requests_week']} requests",
        ]

        return "\n".join(lines)

    async def cmd_top_canzoni(self, username: str, n: int = 10) -> str:
        """!top_canzoni [number] - Shows the N most requested songs."""
        songs = self.analytics.get_top_songs(n)

        if not songs:
            return "📭 No statistics available."

        lines = [f"🎵 Top {n} Requested Songs:"]
        for i, song in enumerate(songs, 1):
            lines.append(f"  {i}. {song['title']} - {song['count']} times")

        return "\n".join(lines)

    async def cmd_top_user(self, username: str, n: int = 10) -> str:
        """!top_user [number] - Shows the users with the most requests."""
        users = self.analytics.get_top_users(n)

        if not users:
            return "📭 No statistics available."

        lines = [f"👥 Top {n} Users:"]
        for i, user in enumerate(users, 1):
            lines.append(f"  {i}. @{user['username']} - {user['count']} requests")

        return "\n".join(lines)

    async def cmd_storia(self, username: str, n: int = 10) -> str:
        """!storia [N] - History of the last N songs played."""
        history = self.analytics.get_play_history(n)

        if not history:
            return "📭 No songs played yet. Use !sr <song> to start!"

        lines = [f"🎧 Last {len(history)} songs played:"]
        for i, entry in enumerate(reversed(history), 1):
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%d/%m %H:%M")
            except (ValueError, TypeError):
                time_str = ts

            lines.append(
                f"  {i}. **{entry['query']}** (@{entry['username']}) — {time_str}"
            )

        return "\n".join(lines)
