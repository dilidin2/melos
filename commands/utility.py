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
        bot_uptime: str = "N/A",
    ):
        self.request_queue = request_queue
        self.music_downloader = music_downloader
        self.version = bot_version
        self.uptime = bot_uptime

    async def cmd_help(self, username: str, command: str = "") -> Union[str, List[str]]:
        """!help [command] - Shows help."""
        if not command:
            return [
                """📚 1/3 [MUSIC]: !sr <url/title> • !random [N] • !duration <song> • !durata <N> • !quando | [PLAYLIST]: !crea <name> • !playlist [n] • !aggiungi <pl> <song> • !rimuovi <pl> <pos> • !sposta <pl> <p1> <p2> • !svuota <pl> • !lista_playlist • !pompa <pl> [N]""",
                """📚 2/3 [MOD]: !whitelist/!blacklist/!unblacklist <user> • !whitelist_list/!blacklist_list • !skippa • !rimuovi_coda <pos> • !clear_queue • !coda_info | [STATS]: !stats • !top_canzoni [N] • !top_user [N] • !storia [N]""",
                """📚 3/3 [CTRL]: !volume <0-100> • !pausa/!riprendi • !repeat/!repeat_off • !ripeti/!stop_ripeti • !next • !queue_info | [UTIL]: !help [cmd] • !version • !uptime""",
            ]

        else:
            commands = {
                "sr": "!sr <song> - Request a song",
                "crea": "!crea <name> - Create playlist",
                "playlist": "!playlist [name] - Show playlists or songs",
                "aggiungi": "!aggiungi <playlist> - Add current song to playlist",
                "rimuovi": "!rimuovi <playlist> <position> - Remove song from playlist",
                "sposta": "!sposta <playlist> <pos1> <pos2> - Swap songs in playlist",
                "svuota": "!svuota <playlist> - Clear a playlist",
                "lista_playlist": "!lista_playlist - Show all playlists",
                "whitelist": "!whitelist <user> - Add to whitelist (admin)",
                "blacklist": "!blacklist <user> - Add to blacklist (admin)",
                "unblacklist": "!unblacklist <user> - Remove from blacklist (admin)",
                "whitelist_list": "!whitelist_list - Show whitelist",
                "blacklist_list": "!blacklist_list - Show blacklist",
                "coda_info": "!coda_info - Show queue info (admin)",
               "skippa": "!skippa - Skip current song (admin)",
                "rimuovi_coda": "!rimuovi_coda <position> - Remove from queue",
                "clear_queue": "!clear_queue - Clear the queue",
                "stats": "!stats - View general statistics",
                "top_canzoni": "!top_canzoni [N] - Top N requested songs",
                "top_user": "!top_user [N] - Top N users",
               "volume": "!volume <0-100> - Set volume",
                "pausa": "!pausa - Pause playback",
                "riprendi": "!riprendi - Resume playback from pause",
                "repeat": "!repeat [N] - Set repeat (default 1)",
                "repeat_off": "!repeat_off - Disable repeat",
                "ripeti": "!ripeti [N] - Repeat song (N=1 or empty=infinite)",
                "stop_ripeti": "!stop_ripeti - Stop repeat",
                "next": "!next - Next song",
                "queue_info": "!queue_info - Show queue info",
                "duration": "!duration <song> - Show song duration",
                "durata": "!durata <N> - Show duration of song at position N in queue",
                "quando": "!quando - Estimate when your next song will play",
                "random": "!random [N] - Play N random songs from library",
                "storia": "!storia [N] - History of last N songs played",
                "help": "!help [command] - Show help",
                "version": "!version - Show bot version",
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
        """!uptime - Shows uptime."""
        return f"⏱️ Bot has been running for: {self.uptime}"

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
