"""Admin Handler - Handles administration and moderation commands."""

import json
from pathlib import Path
from typing import Optional


class AdminHandler:
    """Manages whitelist, blacklist and admin commands."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._whitelist: set[str] = set()
        self._blacklist: set[str] = set()

        self._load_lists()

    def _get_whitelist_file(self) -> Path:
        return self.data_dir / "whitelist.json"

    def _get_blacklist_file(self) -> Path:
        return self.data_dir / "blacklist.json"

    def _load_lists(self):
        """Loads whitelist and blacklist from disk."""
        # Whitelist
        wl_file = self._get_whitelist_file()
        if wl_file.exists():
            try:
                with open(wl_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._whitelist = set(data.get("users", []))
            except (json.JSONDecodeError, KeyError):
                pass

        # Blacklist
        bl_file = self._get_blacklist_file()
        if bl_file.exists():
            try:
                with open(bl_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._blacklist = set(data.get("users", []))
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_whitelist(self):
        """Saves whitelist to disk."""
        wl_file = self._get_whitelist_file()
        with open(wl_file, "w", encoding="utf-8") as f:
            json.dump({"users": list(self._whitelist)}, f, indent=2)

    def _save_blacklist(self):
        """Saves blacklist to disk."""
        bl_file = self._get_blacklist_file()
        with open(bl_file, "w", encoding="utf-8") as f:
            json.dump({"users": list(self._blacklist)}, f, indent=2)

    def add_whitelist(self, username: str) -> bool:
        """Adds a user to the whitelist."""
        if username.lower() not in [u.lower() for u in self._whitelist]:
            self._whitelist.add(username.lower())
            self._save_whitelist()
            return True
        return False

    def remove_whitelist(self, username: str) -> bool:
        """Removes a user from the whitelist."""
        if username.lower() in [u.lower() for u in self._whitelist]:
            self._whitelist.discard(username.lower())
            self._save_whitelist()
            return True
        return False

    def add_blacklist(self, username: str) -> bool:
        """Adds a user to the blacklist."""
        if username.lower() not in [u.lower() for u in self._blacklist]:
            self._blacklist.add(username.lower())
            self._save_blacklist()
            return True
        return False

    def remove_blacklist(self, username: str) -> bool:
        """Removes a user from the blacklist."""
        if username.lower() in [u.lower() for u in self._blacklist]:
            self._blacklist.discard(username.lower())
            self._save_blacklist()
            return True
        return False

    def is_whitelisted(self, username: str) -> bool:
        """Checks if a user is on the whitelist."""
        return username.lower() in [u.lower() for u in self._whitelist]

    def is_blacklisted(self, username: str) -> bool:
        """Checks if a user is on the blacklist."""
        return username.lower() in [u.lower() for u in self._blacklist]

    def get_whitelist_list(self) -> list[str]:
        """Gets the list of whitelisted users."""
        return list(self._whitelist)

    def get_blacklist_list(self) -> list[str]:
        """Gets the list of blacklisted users."""
        return list(self._blacklist)
