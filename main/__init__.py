"""Main module for Twitch Song Request Bot."""

__all__ = [
    "SongRequestBot",
    "RequestQueue",
    "DuplicateCache",
    "SongRequest",
    "TwitchHandler",
    "ChatMessage",
    "MusicDownloader",
    "AudioPlayer",
    "PlaylistManager",
    "Playlist",
    "PlaylistSong",
    "AdminHandler",
    "Analytics",
    "CommandProcessor",
]


# Lazy imports to avoid circular dependency issues
def __getattr__(name: str):
    if name == "SongRequestBot":
        from main.main_core import SongRequestBot

        return SongRequestBot
    elif name == "RequestQueue":
        from main.main_core import RequestQueue

        return RequestQueue
    elif name == "DuplicateCache":
        from main.main_core import DuplicateCache

        return DuplicateCache
    elif name == "SongRequest":
        from main.main_core import SongRequest

        return SongRequest
    elif name == "TwitchHandler":
        from main.twitch_handler import TwitchHandler

        return TwitchHandler
    elif name == "ChatMessage":
        from main.chat_message import ChatMessage

        return ChatMessage
    elif name == "MusicDownloader":
        from main.music_downloader import MusicDownloader

        return MusicDownloader
    elif name == "AudioPlayer":
        from main.audio_player import AudioPlayer

        return AudioPlayer
    elif name == "PlaylistManager":
        from main.playlist_manager import PlaylistManager

        return PlaylistManager
    elif name == "Playlist":
        from main.playlist_manager import Playlist

        return Playlist
    elif name == "PlaylistSong":
        from main.playlist_manager import PlaylistSong

        return PlaylistSong
    elif name == "AdminHandler":
        from main.admin_handler import AdminHandler

        return AdminHandler
    elif name == "Analytics":
        from main.analytics import Analytics

        return Analytics
    elif name == "CommandProcessor":
        from main.command_processor import CommandProcessor

        return CommandProcessor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
