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

    async def cmd_top_songs(self, username: str, n: int = 5) -> str:
        """!top_songs [number] - Shows the N most requested songs (max 5 to stay under Twitch's 500 char limit)."""
        n = min(n, 5)
        songs = self.analytics.get_top_songs(n)

        if not songs:
            return "📭 No statistics available."

        lines = [f"🎵 Top {len(songs)} Requested Songs:"]
        for i, song in enumerate(songs, 1):
            lines.append(f"  {i}. {song['title']} - {song['count']} times")

        return "\n".join(lines)

    async def cmd_top_users(self, username: str, n: int = 10) -> str:
        """!top_user [number] - Shows the users with the most requests."""
        users = self.analytics.get_top_users(n)

        if not users:
            return "📭 No statistics available."

        lines = [f"👥 Top {n} Users:"]
        for i, user in enumerate(users, 1):
            lines.append(f"  {i}. @{user['username']} - {user['count']} requests")

        return "\n".join(lines)

    async def cmd_history(self, username: str, n: int = 5) -> str:
        """!storia [N] - History of the last N songs played (hard limit 500 chars)."""
        history = self.analytics.get_play_history(n)

        if not history:
            return "📭 No songs played yet. Use !sr <song> to start!"

        song_lines: list[str] = []
        for i, entry in enumerate(reversed(history), 1):
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%d/%m %H:%M")
            except (ValueError, TypeError):
                time_str = ts

            line = f"  {i}. **{entry['query']}** (@{entry['username']}) — {time_str}"
            header = f"🎧 Last {len(song_lines) + 1} songs played:"
            candidate = "\n".join([header] + song_lines + [line])
            if len(candidate) > 500:
                break
            song_lines.append(line)

        return "\n".join([f"🎧 Last {len(song_lines)} songs played:"] + song_lines)
