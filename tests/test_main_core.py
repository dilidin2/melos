"""Tests for main_core module: SongRequest, RequestQueue, DuplicateCache."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from main.main_core import SongRequest, RequestQueue, DuplicateCache


class TestSongRequest:
    """Tests for SongRequest dataclass."""

    def test_create_song_request(self):
        """Test creating a SongRequest with required fields."""
        request = SongRequest(
            query="Bohemian Rhapsody",
            username="testuser",
            channel_id="12345",
            request_id=1
        )
        assert request.query == "Bohemian Rhapsody"
        assert request.username == "testuser"
        assert request.channel_id == "12345"
        assert request.request_id == 1
        assert request.added_at is None
        assert request.resolved_title is None
        assert request.resolved_duration is None

    def test_create_song_request_with_optional_fields(self):
        """Test creating a SongRequest with all fields."""
        now = datetime.now().isoformat()
        request = SongRequest(
            query="Bohemian Rhapsody",
            username="testuser",
            channel_id="12345",
            request_id=1,
            added_at=now,
            resolved_title="Bohemian Rhapsody",
            resolved_duration=354
        )
        assert request.added_at == now
        assert request.resolved_title == "Bohemian Rhapsody"
        assert request.resolved_duration == 354


class TestRequestQueue:
    """Tests for RequestQueue class."""

    @pytest.fixture
    def request_queue(self):
        """Create a RequestQueue instance."""
        return RequestQueue(max_size=10)

    def test_init_default_max_size(self):
        """Test RequestQueue initialization with default max_size."""
        queue = RequestQueue()
        assert queue.max_size == 999

    def test_init_custom_max_size(self):
        """Test RequestQueue initialization with custom max_size."""
        queue = RequestQueue(max_size=5)
        assert queue.max_size == 5

    @pytest.mark.asyncio
    async def test_put_success(self, request_queue):
        """Test successful addition to queue."""
        request = SongRequest("test", "user", "ch", 1)
        result = await request_queue.put(request)
        assert result is True

    @pytest.mark.asyncio
    async def test_put_timeout(self, request_queue):
        """Test put timeout when queue is full."""
        # Create a queue with size 1
        small_queue = RequestQueue(max_size=1)
        
        # Fill the queue
        request1 = SongRequest("test1", "user", "ch", 1)
        await small_queue.queue.put(request1)
        
        # Try to add another - should timeout
        request2 = SongRequest("test2", "user", "ch", 2)
        with patch.object(asyncio, 'wait_for', side_effect=asyncio.TimeoutError):
            result = await small_queue.put(request2)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_success(self, request_queue):
        """Test successful retrieval from queue."""
        request = SongRequest("test", "user", "ch", 1)
        await request_queue.queue.put(request)
        
        result = await request_queue.get()
        assert result is request

    @pytest.mark.asyncio
    async def test_get_timeout_empty(self, request_queue):
        """Test get returns None when queue is empty."""
        result = await request_queue.get()
        assert result is None

    def test_task_done(self, request_queue):
        """Test task_done calls queue.task_done."""
        request_queue.queue.task_done = MagicMock()
        request_queue.task_done()
        request_queue.queue.task_done.assert_called_once()

    def test_qsize(self, request_queue):
        """Test qsize returns correct value."""
        request_queue.queue.qsize = MagicMock(return_value=5)
        assert request_queue.qsize() == 5

    def test_is_processing_not_in_progress(self, request_queue):
        """Test is_processing returns False when not processing."""
        request_queue._in_progress = False
        assert request_queue.is_processing() is False

    def test_is_processing_in_progress(self, request_queue):
        """Test is_processing returns True when processing."""
        request_queue._in_progress = True
        assert request_queue.is_processing() is True

    def test_get_items(self, request_queue):
        """Test get_items returns first N items."""
        items = [
            SongRequest("q1", "u1", "c1", 1),
            SongRequest("q2", "u2", "c2", 2),
            SongRequest("q3", "u3", "c3", 3),
        ]
        request_queue.queue._queue = items
        result = request_queue.get_items(count=2)
        assert len(result) == 2
        assert result[0].query == "q1"
        assert result[1].query == "q2"

    def test_get_items_more_than_available(self, request_queue):
        """Test get_items returns all items if count exceeds available."""
        items = [SongRequest("q1", "u1", "c1", 1)]
        request_queue.queue._queue = items
        result = request_queue.get_items(count=10)
        assert len(result) == 1


class TestDuplicateCache:
    """Tests for DuplicateCache class."""

    def test_init_default_max_size(self):
        """Test DuplicateCache initialization."""
        cache = DuplicateCache()
        assert cache.max_size == 100
        assert cache.cache == {}

    def test_init_custom_max_size(self):
        """Test DuplicateCache with custom max_size."""
        cache = DuplicateCache(max_size=50)
        assert cache.max_size == 50

    def test_add_to_cache(self):
        """Test adding item to cache."""
        cache = DuplicateCache()
        cache.add("test query", "/path/to/file.mp3", "testuser")
        assert "test query" in cache.cache
        assert cache.cache["test query"] == ("/path/to/file.mp3", "testuser")

    def test_add_case_insensitive_key(self):
        """Test that cache keys are case-insensitive."""
        cache = DuplicateCache()
        cache.add("Test Query", "/path/to/file.mp3", "user")
        assert cache.get("test query") == ("/path/to/file.mp3", "user")
        assert cache.get("TEST QUERY") == ("/path/to/file.mp3", "user")

    def test_get_from_cache(self):
        """Test retrieving item from cache."""
        cache = DuplicateCache()
        cache.add("test query", "/path/to/file.mp3", "testuser")
        result = cache.get("test query")
        assert result == ("/path/to/file.mp3", "testuser")

    def test_get_not_in_cache(self):
        """Test get returns None when item not in cache."""
        cache = DuplicateCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_remove_from_cache(self):
        """Test removing item from cache."""
        cache = DuplicateCache()
        cache.add("test query", "/path/to/file.mp3", "testuser")
        cache.remove("test query")
        assert cache.get("test query") is None

    def test_remove_nonexistent(self):
        """Test removing nonexistent item doesn't raise."""
        cache = DuplicateCache()
        cache.remove("nonexistent")  # Should not raise

    def test_cache_eviction(self):
        """Test that oldest item is evicted when cache is full."""
        cache = DuplicateCache(max_size=2)
        cache.add("query1", "/path1.mp3", "user1")
        cache.add("query2", "/path2.mp3", "user2")
        cache.add("query3", "/path3.mp3", "user3")
        
        assert len(cache.cache) == 2
        assert "query1" not in cache.cache
        assert "query2" in cache.cache
        assert "query3" in cache.cache
