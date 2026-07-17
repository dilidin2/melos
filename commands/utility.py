"""Utility Commands - General utility commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from main.main_core import RequestQueue
    from main.music_downloader import MusicDownloader


class UtilityCommands:
    """Handles all general utility commands."""

    def __init__(
        self,
        request_queue: Optional["RequestQueue"] = None,
        music_downloader: Optional["MusicDownloader"] = None,
        bot_version: str = "1.0.0",
    ):
        self.request_queue = request_queue
        self.music_downloader = music_downloader
        self.version = bot_version

    async def cmd_help(self, username: str, command: str = "") -> Union[str, List[str]]:
        """!help [command] - Shows help."""
        if not command:
            return [
                """📚 1/3 [MUSIC]: !sr <url/title> • !random [N] • !duration <song> • !at <N> • !when | [PLAYLIST]: !create <name> • !playlist [n] • !add <pl> <song> • !remove <pl> <pos> • !move <pl> <p1> <p2> • !clear <pl> • !list_playlists • !pump <pl> [N]""",
                """📚 2/3 [MOD]: !blacklist/!unblacklist <user> • !blacklist_list • !skip • !remove_queue <pos> • !clear_queue • !volume <0-100> | [STATS]: !stats • !top_songs [N] • !top_users [N] • !history_played [N]""",
                """📚 3/3 [CTRL]: !pause/!resume • !repeat/!repeat_off • !repeat/!stop_repeat • !next • !queue_info • !ops | [UTIL]: !help [cmd] • !version • !uptime""",
            ]

        else:
            commands = {
                "sr": "!sr <song> - Request a song",
                "create": "!create <name> - Create playlist",
                "playlist": "!playlist [name] - Show playlists or songs",
                "add": "!add <playlist> - Add current song to playlist",
                "remove": "!remove <playlist> <position> - Remove song from playlist",
                "move": "!move <playlist> <pos1> <pos2> - Swap songs in playlist",
                "clear": "!clear <playlist> - Clear a playlist",
                "list_playlists": "!list_playlists - Show all playlists",
                "pump": "!pump <playlist> [N] - Pump N random songs from playlist",
                "blacklist": "!blacklist <user> - Add to blacklist (admin)",
                "unblacklist": "!unblacklist <user> - Remove from blacklist (admin)",
                "blacklist_list": "!blacklist_list - Show blacklist",
                "queue_info": "!queue_info - Show the next songs in the queue",
                "skip": "!skip - Skip current song (admin)",
                "remove_queue": "!remove_queue <position> - Remove from queue",
                "clear_queue": "!clear_queue - Clear the queue",
                "volume": "!volume <0-100> - Set volume (admin)",
                "stats": "!stats - View general statistics",
                "top_songs": "!top_songs [N] - Top N requested songs",
                "top_users": "!top_users [N] - Top N users",
                "history_played": "!history_played [N] - History of last N songs played",
                "pause": "!pause - Pause playback",
                "resume": "!resume - Resume playback from pause",
                "repeat": "!repeat [N] - Set repeat (default 1)",
                "repeat_off": "!repeat_off - Disable repeat",
                "stop_repeat": "!stop_repeat - Stop repeat",
                "next": "!next - Next song",
                "duration": "!duration <song> - Show song duration",
                "at": "!at <N> - Show duration of song at position N in queue",
                "when": "!when - Estimate when your next song will play",
                "random": "!random [N] - Play N random songs from library",
                "help": "!help [command] - Show help",
                "version": "!version - Show bot version",
                "ops": "!ops - Remove the last song you added from the queue",
                "uptime": "!uptime - Show uptime",
            }

            if command in commands:
                return f"📖 **{command}**: {commands[command]}"
            else:
                return f"❌ Command '{command}' not found. Use !help for the full list."

    async def cmd_version(self, username: str) -> str:
        """!version - Shows bot version."""
        return f"🔧 Twitch Song Request Bot v{self.version}"

    async def cmd_uptime(self, username: str) -> str:
        """!uptime - Shows bot uptime (fallback when bot._start_time unavailable)."""
        return "⏱️ Uptime info unavailable."

    async def cmd_queue_info(self, username: str, channel_id: str) -> str:
        """!queue_info - Shows the next 5 songs in the queue."""
        if not self.request_queue or not self.music_downloader:
            return "❌ Unable to access the queue."

        songs = self.request_queue.get_items(count=5)

        if not songs:
            return "🎵 The queue is empty."

        lines = ["🎵 **Next songs in queue:**"]
        for i, request in enumerate(songs, 1):
            song_info = self.music_downloader.get_song_info(request.query)

            if song_info:
                title = song_info["title"]
                duration_seconds = song_info["duration"]

                if duration_seconds > 0:
                    minutes = duration_seconds // 60
                    seconds = duration_seconds % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "N/D"

                lines.append(f"{i}. **{title}** ({duration_str})")
            else:
                lines.append(f"{i}. {request.query}")

        return "\n".join(lines)
