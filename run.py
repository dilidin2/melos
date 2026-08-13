#!/usr/bin/env python3
"""Main entry point for the Twitch music request bot."""

import asyncio
import threading
import os

from main.config import LOG_LEVEL, LOG_FILE, DASHBOARD_ENABLED, DASHBOARD_PORT, DASHBOARD_HOST
from main.main_core import SongRequestBot
from main.command_processor import CommandProcessor
from main.playlist_manager import PlaylistManager
from main.admin_handler import AdminHandler
from main.analytics import Analytics
from main.music_downloader import MusicDownloader
from commands.playlists import PlaylistCommands
from commands.admin import AdminCommands
from commands.analytics import AnalyticsCommands
from commands.music import MusicCommands
from commands.utility import UtilityCommands
from main.logger import setup_logger

setup_logger(log_file=LOG_FILE, level=LOG_LEVEL)


def _start_dashboard_thread(api_module, host, port):
    """Start uvicorn in a background thread."""
    import uvicorn

    def run():
        uvicorn.run(api_module, host=host, port=port, log_level="warning", access_log=False)

    thread = threading.Thread(target=run, daemon=True, name="dashboard")
    thread.start()
    return thread


async def main():
    admin_handler = AdminHandler()
    bot = SongRequestBot(audio_device="MusicaBot_Input", admin_handler=admin_handler)

    playlist_manager = PlaylistManager()
    analytics = Analytics()
    music_downloader = MusicDownloader(admin_handler=admin_handler)

    bot.analytics = analytics

    playlist_commands = PlaylistCommands(playlist_manager, bot.request_queue, bot)
    admin_commands = AdminCommands(
        admin_handler, bot.audio_player, bot.request_queue, bot, music_downloader
    )
    analytics_commands = AnalyticsCommands(analytics)
    music_commands = MusicCommands(bot.audio_player, bot.request_queue, music_downloader, bot)
    utility_commands = UtilityCommands(
        bot.request_queue, music_downloader, bot_version="1.1.0"
    )

    command_processor = CommandProcessor(
        bot=bot,
        playlist_commands=playlist_commands,
        admin_commands=admin_commands,
        analytics_commands=analytics_commands,
        music_commands=music_commands,
        utility_commands=utility_commands,
        music_downloader=music_downloader,
    )

    bot.command_processor = command_processor
    bot.twitch_handler.set_command_callback(bot._handle_song_request)
    bot.twitch_handler.command_processor = command_processor

    # ── Start Dashboard ──
    if DASHBOARD_ENABLED:
        from dashboard.api import app, init_dashboard

        init_dashboard(bot, admin_handler, playlist_manager, analytics)
        _start_dashboard_thread(app, DASHBOARD_HOST, DASHBOARD_PORT)
        print(f"🌐 Dashboard running at http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")

    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
