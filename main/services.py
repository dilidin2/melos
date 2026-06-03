"""Services layer - Dependency Injection container for all bot services."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main.audio_player import AudioPlayer
    from main.admin_handler import AdminHandler
    from main.analytics import Analytics
    from main.music_downloader import MusicDownloader
    from main.playlist_manager import PlaylistManager
    from main.main_core import RequestQueue, SongRequestBot
    from commands.admin import AdminCommands
    from commands.analytics import AnalyticsCommands
    from commands.music import MusicCommands
    from commands.playlists import PlaylistCommands
    from commands.utility import UtilityCommands


@dataclass
class CommandServices:
    """DI container - all services injected explicitly.

    Replaces dynamic self.bot.xxx coupling with explicit dependencies.
    """
    # Command handlers (commands layer)
    playlist_commands: Optional["PlaylistCommands"] = None
    admin_commands: Optional["AdminCommands"] = None
    analytics_commands: Optional["AnalyticsCommands"] = None
    music_commands: Optional["MusicCommands"] = None
    utility_commands: Optional["UtilityCommands"] = None

    # Business logic services
    playlist_manager: Optional["PlaylistManager"] = None
    admin_handler: Optional["AdminHandler"] = None
    analytics: Optional["Analytics"] = None
    audio_player: Optional["AudioPlayer"] = None
    music_downloader: Optional["MusicDownloader"] = None

    # Core infrastructure
    request_queue: Optional["RequestQueue"] = None
    bot: Optional["SongRequestBot"] = None

    @classmethod
    def build(
        cls,
        bot: "SongRequestBot",
        playlist_manager: "PlaylistManager",
        admin_handler: "AdminHandler",
        analytics: "Analytics",
        music_downloader: "MusicDownloader",
        playlist_commands: "PlaylistCommands",
        admin_commands: "AdminCommands",
        analytics_commands: "AnalyticsCommands",
        music_commands: "MusicCommands",
        utility_commands: "UtilityCommands",
    ) -> "CommandServices":
        """Build the services container from initialized components."""
        return cls(
            playlist_commands=playlist_commands,
            admin_commands=admin_commands,
            analytics_commands=analytics_commands,
            music_commands=music_commands,
            utility_commands=utility_commands,
            playlist_manager=playlist_manager,
            admin_handler=admin_handler,
            analytics=analytics,
            music_downloader=music_downloader,
            audio_player=bot.audio_player,
            request_queue=bot.request_queue,
            bot=bot,
        )
