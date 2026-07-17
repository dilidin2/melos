#!/usr/bin/env python3
"""Main entry point for the Twitch music request bot.

This is the main executable that starts the bot with all features.
"""

import asyncio
import signal
import sys

from main.config import (
    TARGET_CHANNEL,
    MAX_WORKERS,
    LOG_LEVEL,
    LOG_FILE,
)

from main.main_core import SongRequestBot
from main.services import CommandServices
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

from utils.logger import setup_logger

setup_logger(log_file=LOG_FILE, level=LOG_LEVEL)


async def main():
    """Main entry point."""
    admin_handler = AdminHandler()
    bot = SongRequestBot(audio_device="MusicaBot_Input", admin_handler=admin_handler)

    # Initialize services
    playlist_manager = PlaylistManager()
    analytics = Analytics()
    music_downloader = MusicDownloader(admin_handler=admin_handler)

    # Wire analytics into the bot so record_request/record_play are called
    bot.analytics = analytics

    # Initialize command handlers with explicit dependencies
    playlist_commands = PlaylistCommands(playlist_manager, bot.request_queue, bot)
    admin_commands = AdminCommands(
        admin_handler, bot.audio_player, bot.request_queue, bot, music_downloader
    )
    analytics_commands = AnalyticsCommands(analytics)
    music_commands = MusicCommands(bot.audio_player, bot.request_queue, music_downloader, bot)
    utility_commands = UtilityCommands(
        bot.request_queue, music_downloader, bot_version="1.1.0"
    )

    # Build DI container
    services = CommandServices.build(
        bot=bot,
        playlist_manager=playlist_manager,
        admin_handler=admin_handler,
        analytics=analytics,
        music_downloader=music_downloader,
        playlist_commands=playlist_commands,
        admin_commands=admin_commands,
        analytics_commands=analytics_commands,
        music_commands=music_commands,
        utility_commands=utility_commands,
    )

    # Initialize command processor with DI container
    command_processor = CommandProcessor(services)

    bot.command_processor = command_processor
    bot.twitch_handler.set_command_callback(bot._handle_song_request)
    bot.twitch_handler.command_processor = command_processor

    loop = asyncio.get_running_loop()
    shutdown_task = None

    def signal_handler(sig, frame):
        """Handles shutdown signals."""
        nonlocal shutdown_task
        logger.info("Signal received, shutting down...")

        if shutdown_task and not shutdown_task.done():
            return

        shutdown_task = loop.create_task(bot.shutdown())
        shutdown_task.add_done_callback(
            lambda f: loop.call_soon_threadsafe(lambda: sys.exit(0))
        )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
