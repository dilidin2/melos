"""Tests for logger module."""

import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from utils.logger import setup_logger


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_returns_logger(self):
        """Test setup_logger returns a logger."""
        result = setup_logger(log_file="test.log", level="DEBUG")
        assert result is not None

    def test_setup_logger_creates_log_dir(self, temp_dir):
        """Test setup_logger creates log directory."""
        log_file = os.path.join(temp_dir, "test.log")
        setup_logger(log_file=log_file)
        assert os.path.exists(os.path.dirname(log_file))

    def test_setup_logger_with_default_log_file(self, temp_dir):
        """Test setup_logger with default log file."""
        log_file = os.path.join(temp_dir, "twitch_sr.log")
        setup_logger(log_file=log_file, level="DEBUG")
        assert os.path.exists(log_file)

    def test_setup_logger_level_debug(self, temp_dir):
        """Test setup_logger with DEBUG level."""
        log_file = os.path.join(temp_dir, "debug.log")
        logger = setup_logger(log_file=log_file, level="DEBUG")
        assert logger.level == 10  # DEBUG level

    def test_setup_logger_level_info(self, temp_dir):
        """Test setup_logger with INFO level."""
        log_file = os.path.join(temp_dir, "info.log")
        logger = setup_logger(log_file=log_file, level="INFO")
        assert logger.level == 20  # INFO level

    def test_setup_logger_creates_file(self, temp_dir):
        """Test setup_logger creates log file."""
        log_file = os.path.join(temp_dir, "test.log")
        setup_logger(log_file=log_file, level="DEBUG")
        assert os.path.exists(log_file)

    def test_setup_logger_with_rotation(self, temp_dir):
        """Test setup_logger with rotation."""
        log_file = os.path.join(temp_dir, "rotated.log")
        logger = setup_logger(log_file=log_file, rotation="5 MB")
        assert logger is not None

    def test_setup_logger_with_retention(self, temp_dir):
        """Test setup_logger with retention."""
        log_file = os.path.join(temp_dir, "retained.log")
        logger = setup_logger(log_file=log_file, retention="7 days")
        assert logger is not None

    def test_setup_logger_multiple_calls(self, temp_dir):
        """Test multiple calls to setup_logger."""
        log_file = os.path.join(temp_dir, "multi.log")
        logger1 = setup_logger(log_file=log_file, level="DEBUG")
        logger2 = setup_logger(log_file=log_file, level="DEBUG")
        assert logger1 is logger2

    def test_setup_logger_creates_parent_directories(self, temp_dir):
        """Test setup_logger creates parent directories."""
        log_file = os.path.join(temp_dir, "sub1", "sub2", "test.log")
        setup_logger(log_file=log_file, level="DEBUG")
        assert os.path.exists(os.path.dirname(log_file))
