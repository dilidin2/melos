"""Tests for admin_handler module."""

import pytest
import json
import os
from unittest.mock import MagicMock, patch

from main.admin_handler import AdminHandler


class TestAdminHandler:
    """Tests for AdminHandler class."""

    @pytest.fixture
    def handler(self, temp_dir):
        """Create an AdminHandler instance."""
        return AdminHandler(data_dir=temp_dir)

    def test_init_creates_data_dir(self, temp_dir):
        """Test init creates data directory."""
        handler = AdminHandler(data_dir=temp_dir)
        assert os.path.exists(temp_dir)

    def test_init_empty_lists(self, temp_dir):
        """Test init creates empty lists."""
        handler = AdminHandler(data_dir=temp_dir)
        assert handler.get_whitelist_list() == []
        assert handler.get_blacklist_list() == []

    def test_is_whitelisted_false(self, handler):
        """Test is_whitelisted returns False for non-whitelisted user."""
        assert handler.is_whitelisted("testuser") is False

    def test_is_blacklisted_false(self, handler):
        """Test is_blacklisted returns False for non-blacklisted user."""
        assert handler.is_blacklisted("testuser") is False

    def test_add_whitelist(self, handler):
        """Test adding user to whitelist."""
        result = handler.add_whitelist("testuser")
        assert result is True
        assert handler.is_whitelisted("testuser") is True

    def test_add_whitelist_duplicate(self, handler):
        """Test adding duplicate to whitelist."""
        handler.add_whitelist("testuser")
        result = handler.add_whitelist("testuser")
        assert result is False

    def test_add_whitelist_case_insensitive(self, handler):
        """Test adding user to whitelist is case insensitive."""
        handler.add_whitelist("TestUser")
        result = handler.add_whitelist("testuser")
        assert result is False

    def test_remove_whitelist(self, handler):
        """Test removing user from whitelist."""
        handler.add_whitelist("testuser")
        result = handler.remove_whitelist("testuser")
        assert result is True
        assert handler.is_whitelisted("testuser") is False

    def test_remove_whitelist_not_found(self, handler):
        """Test removing non-whitelisted user."""
        result = handler.remove_whitelist("testuser")
        assert result is False

    def test_add_blacklist(self, handler):
        """Test adding user to blacklist."""
        result = handler.add_blacklist("testuser")
        assert result is True
        assert handler.is_blacklisted("testuser") is True

    def test_add_blacklist_duplicate(self, handler):
        """Test adding duplicate to blacklist."""
        handler.add_blacklist("testuser")
        result = handler.add_blacklist("testuser")
        assert result is False

    def test_remove_blacklist(self, handler):
        """Test removing user from blacklist."""
        handler.add_blacklist("testuser")
        result = handler.remove_blacklist("testuser")
        assert result is True
        assert handler.is_blacklisted("testuser") is False

    def test_remove_blacklist_not_found(self, handler):
        """Test removing non-blacklisted user."""
        result = handler.remove_blacklist("testuser")
        assert result is False

    def test_get_whitelist_list(self, handler):
        """Test getting whitelist list."""
        handler.add_whitelist("user1")
        handler.add_whitelist("user2")
        users = handler.get_whitelist_list()
        assert len(users) == 2
        assert "user1" in users
        assert "user2" in users

    def test_get_blacklist_list(self, handler):
        """Test getting blacklist list."""
        handler.add_blacklist("banned1")
        handler.add_blacklist("banned2")
        users = handler.get_blacklist_list()
        assert len(users) == 2

    def test_persist_whitelist(self, temp_dir):
        """Test whitelist is persisted to disk."""
        handler = AdminHandler(data_dir=temp_dir)
        handler.add_whitelist("testuser")
        
        wl_file = os.path.join(temp_dir, "whitelist.json")
        assert os.path.exists(wl_file)
        
        with open(wl_file) as f:
            data = json.load(f)
        assert "testuser" in data["users"]

    def test_persist_blacklist(self, temp_dir):
        """Test blacklist is persisted to disk."""
        handler = AdminHandler(data_dir=temp_dir)
        handler.add_blacklist("testuser")
        
        bl_file = os.path.join(temp_dir, "blacklist.json")
        assert os.path.exists(bl_file)
        
        with open(bl_file) as f:
            data = json.load(f)
        assert "testuser" in data["users"]

    def test_load_whitelist_from_disk(self, temp_dir):
        """Test loading whitelist from disk."""
        wl_file = os.path.join(temp_dir, "whitelist.json")
        with open(wl_file, "w") as f:
            json.dump({"users": ["user1", "user2"]}, f)
        
        handler = AdminHandler(data_dir=temp_dir)
        users = handler.get_whitelist_list()
        assert len(users) == 2

    def test_load_blacklist_from_disk(self, temp_dir):
        """Test loading blacklist from disk."""
        bl_file = os.path.join(temp_dir, "blacklist.json")
        with open(bl_file, "w") as f:
            json.dump({"users": ["banned1"]}, f)
        
        handler = AdminHandler(data_dir=temp_dir)
        users = handler.get_blacklist_list()
        assert len(users) == 1
        assert "banned1" in users

    def test_load_invalid_json(self, temp_dir):
        """Test loading invalid JSON gracefully."""
        wl_file = os.path.join(temp_dir, "whitelist.json")
        with open(wl_file, "w") as f:
            f.write("invalid json")
        
        handler = AdminHandler(data_dir=temp_dir)
        users = handler.get_whitelist_list()
        assert users == []
