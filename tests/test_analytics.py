"""Tests for analytics module."""

import pytest
import json
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from main.analytics import Analytics


class TestAnalytics:
    """Tests for Analytics class."""

    @pytest.fixture
    def analytics(self, temp_dir):
        """Create an Analytics instance with temp dir."""
        return Analytics(data_dir=temp_dir)

    def test_init_creates_data_dir(self, temp_dir):
        """Test init creates data directory."""
        analytics = Analytics(data_dir=temp_dir)
        assert os.path.exists(temp_dir)

    def test_init_loads_empty_stats(self, temp_dir):
        """Test init loads empty stats when no file exists."""
        analytics = Analytics(data_dir=temp_dir)
        assert analytics.get_total_requests() == 0
        assert analytics.get_total_plays() == 0

    def test_init_loads_existing_stats(self, temp_dir):
        """Test init loads existing stats from file."""
        stats_file = os.path.join(temp_dir, "stats.json")
        with open(stats_file, "w") as f:
            json.dump({
                "total_requests": 100,
                "total_plays": 50,
                "songs_by_user": {"user1": 10},
                "songs_by_title": {"song1": 5},
                "play_history": []
            }, f)
        
        analytics = Analytics(data_dir=temp_dir)
        assert analytics.get_total_requests() == 100
        assert analytics.get_total_plays() == 50

    def test_init_invalid_json(self, temp_dir):
        """Test init handles invalid JSON gracefully."""
        stats_file = os.path.join(temp_dir, "stats.json")
        with open(stats_file, "w") as f:
            f.write("invalid json")
        
        analytics = Analytics(data_dir=temp_dir)
        assert analytics.get_total_requests() == 0

    def test_record_request(self, analytics):
        """Test recording a request."""
        analytics.record_request("testuser", "test song")
        assert analytics.get_total_requests() == 1

    def test_record_request_updates_user_count(self, analytics):
        """Test recording request updates user count."""
        analytics.record_request("testuser", "test song")
        analytics.record_request("testuser", "another song")
        assert analytics.get_total_requests() == 2

    def test_record_request_case_insensitive_user(self, analytics):
        """Test recording request is case insensitive for users."""
        analytics.record_request("TestUser", "test song")
        analytics.record_request("testuser", "another song")
        assert analytics.get_total_requests() == 2

    def test_record_play(self, analytics):
        """Test recording a play."""
        analytics.record_play("testuser", "test song")
        assert analytics.get_total_plays() == 1

    def test_record_play_adds_to_history(self, analytics):
        """Test recording play adds to history."""
        analytics.record_play("testuser", "test song")
        stats_today = analytics.get_stats_today()
        assert stats_today["total_requests_today"] == 1

    def test_get_total_requests(self, analytics):
        """Test getting total requests."""
        analytics.record_request("user1", "song1")
        analytics.record_request("user2", "song2")
        assert analytics.get_total_requests() == 2

    def test_get_total_plays(self, analytics):
        """Test getting total plays."""
        analytics.record_play("user1", "song1")
        analytics.record_play("user2", "song2")
        assert analytics.get_total_plays() == 2

    def test_get_top_songs(self, analytics):
        """Test getting top songs."""
        analytics.record_request("user1", "song1")
        analytics.record_request("user1", "song1")
        analytics.record_request("user2", "song2")
        
        top = analytics.get_top_songs(n=5)
        assert len(top) == 2
        assert top[0]["title"] == "song1"
        assert top[0]["count"] == 2

    def test_get_top_songs_limit(self, analytics):
        """Test getting top songs with limit."""
        for i in range(10):
            analytics.record_request("user1", f"song{i}")
        
        top = analytics.get_top_songs(n=3)
        assert len(top) == 3

    def test_get_top_users(self, analytics):
        """Test getting top users."""
        analytics.record_request("user1", "song1")
        analytics.record_request("user1", "song2")
        analytics.record_request("user2", "song3")
        
        top = analytics.get_top_users(n=5)
        assert len(top) == 2
        assert top[0]["username"] == "user1"
        assert top[0]["count"] == 2

    def test_get_stats_today(self, analytics):
        """Test getting today's stats."""
        analytics.record_request("user1", "song1")
        analytics.record_request("user2", "song2")
        
        stats = analytics.get_stats_today()
        assert "date" in stats
        assert stats["total_requests_today"] == 2
        assert stats["unique_users_today"] == 2

    def test_get_stats_week(self, analytics):
        """Test getting week stats."""
        analytics.record_request("user1", "song1")
        
        stats = analytics.get_stats_week()
        assert stats["period"] == "last_7_days"
        assert stats["total_requests_week"] == 1

    def test_get_stats_month(self, analytics):
        """Test getting month stats."""
        analytics.record_request("user1", "song1")
        
        stats = analytics.get_stats_month()
        assert stats["period"] == "last_30_days"
        assert stats["total_requests_month"] == 1

    def test_stats_persistence(self, temp_dir):
        """Test stats are persisted to disk."""
        analytics1 = Analytics(data_dir=temp_dir)
        analytics1.record_request("user1", "song1")
        
        # Load from same directory
        analytics2 = Analytics(data_dir=temp_dir)
        assert analytics2.get_total_requests() == 1
