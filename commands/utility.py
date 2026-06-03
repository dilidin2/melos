"""Utility Commands - Comandi generali di utilità."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from main.main_core import RequestQueue
    from main.music_downloader import MusicDownloader


class UtilityCommands:
    """Gestisce tutti i comandi utility generali."""

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
        """!help [comando] - Mostra aiuto."""
        if not command:
            return [
                """📚 1/3 [MUSICA]: !sr <url/titolo> • !random [N] • !duration <canzone> • !durata <N> • !quando | [PLAYLIST]: !crea <nome> • !playlist [n] • !aggiungi <pl> <song> • !rimuovi <pl> <pos> • !sposta <pl> <p1> <p2> • !svuota <pl> • !lista_playlist • !pompa <pl> [N]""",
                """📚 2/3 [MOD]: !whitelist/!blacklist/!unblacklist <user> • !whitelist_list/!blacklist_list • !skippa • !rimuovi_coda <pos> • !clear_queue • !coda_info | [STATS]: !stats • !top_canzoni [N] • !top_user [N] • !storia [N]""",
                """📚 3/3 [CTRL]: !volume <0-100> • !pausa/!riprendi • !repeat/!repeat_off • !ripeti/!stop_ripeti • !next • !queue_info | [UTIL]: !help [cmd] • !version • !uptime""",
            ]

        else:
            commands = {
                "sr": "!sr <canzone> - Richiedi una canzone",
                "crea": "!crea <nome> - Crea playlist",
                "playlist": "!playlist [nome] - Mostra playlist o canzoni",
                "aggiungi": "!aggiungi <playlist> - Aggiungi canzone corrente alla playlist",
                "rimuovi": "!rimuovi <playlist> <posizione> - Rimuovi canzone dalla playlist",
                "sposta": "!sposta <playlist> <pos1> <pos2> - Sposta canzoni nella playlist",
                "svuota": "!svuota <playlist> - Svuota una playlist",
                "lista_playlist": "!lista_playlist - Mostra tutte le playlist",
                "whitelist": "!whitelist <utente> - Aggiungi alla whitelist (admin)",
                "blacklist": "!blacklist <utente> - Metti in blacklist (admin)",
                "unblacklist": "!unblacklist <utente> - Rimuovi dalla blacklist (admin)",
                "whitelist_list": "!whitelist_list - Mostra lista whitelist",
                "blacklist_list": "!blacklist_list - Mostra lista blacklist",
                "coda_info": "!coda_info - Mostra info sulla coda (admin)",
               "skippa": "!skippa - Salta canzone corrente (admin)",
                "rimuovi_coda": "!rimuovi_coda <posizione> - Rimuovi dalla coda",
                "coda_info": "!coda_info - Mostra info sulla coda",
                "clear_queue": "!clear_queue - Svuota la coda",
                "stats": "!stats - Visualizza statistiche generali",
                "top_canzoni": "!top_canzoni [N] - Top N canzoni richieste",
                "top_user": "!top_user [N] - Top N utenti",
               "volume": "!volume <0-100> - Imposta volume",
                "pausa": "!pausa - Metti in pausa la riproduzione",
                "riprendi": "!riprendi - Riprendi la riproduzione dalla pausa",
                "repeat": "!repeat [N] - Imposta ripetizione (default 1)",
                "repeat_off": "!repeat_off - Disattiva ripetizione",
                "ripeti": "!ripeti [N] - Ripeti canzone (N=1 o vuoto=infinito)",
                "stop_ripeti": "!stop_ripeti - Ferma il repeat",
                "next": "!next - Prossima canzone",
                "queue_info": "!queue_info - Mostra info coda",
                "duration": "!duration <canzone> - Mostra durata canzone",
                "durata": "!durata <N> - Mostra durata canzone in posizione N nella coda",
                "quando": "!quando - Stima quando partirà la tua prossima canzone",
                "random": "!random [N] - Riproduci N canzoni casuali dalla libreria",
                "storia": "!storia [N] - Cronologia ultime N canzoni riprodotte",
                "help": "!help [comando] - Mostra aiuto",
                "version": "!version - Mostra versione del bot",
                "uptime": "!uptime - Mostra tempo di attività",
            }

            if command in commands:
                return f"📖 **{command}**: {commands[command]}"
            else:
                return f"❌ Comando '{command}' non trovato. Usa !help per la lista completa."

    async def cmd_version(self, username: str) -> str:
        """!version - Mostra versione del bot."""
        return f"🔧 Twitch Song Request Bot v{self.version}"

    async def cmd_uptime(self, username: str) -> str:
        """!uptime - Mostra tempo di attività."""
        return f"⏱️ Il bot è attivo da: {self.uptime}"

    async def cmd_queue_info(self, username: str, channel_id: str) -> str:
        """!queue_info - Mostra le prossime 5 canzoni nella coda."""
        if not self.request_queue or not self.music_downloader:
            return "❌ Impossibile accedere alla coda."

        songs = self.request_queue.get_items(count=5)

        if not songs:
            return "🎵 La coda è vuota."

        lines = ["🎵 **Prossime canzoni nella coda:**"]
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
