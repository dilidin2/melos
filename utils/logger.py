"""Logging utilities - powered by Loguru."""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_file: str = "twitch_sr.log",
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "30 days",
):
    """Configure loguru with console (colored) and file handlers.

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        rotation: When to rotate the log file
        retention: How long to keep old log files
    """
    # Remove default handler
    logger.remove()

    # Console handler with colors
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
        enqueue=True,
    )

    # File handler with rotation and retention
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention,
        compression="zip",
        enqueue=True,
    )

    return logger


# Default setup
setup_logger()
