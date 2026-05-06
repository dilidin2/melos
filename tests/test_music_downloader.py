"""Tests for music_downloader module."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import os

from main.music_downloader import (
    MusicDownloader,
    _SongTooLongError,
    _CategoryError,
    _NoValidCandidateError,
)


@pytest.fixture
def downloader():
    """Create a MusicDownloader instance."""
    with patch("main.music_downloader.os.makedirs"):
        with patch("main.music_downloader.yt_dlp.YoutubeDL"):
            downloader = MusicDownloader()
            return downloader


class TestMusicDownloaderInit:
    """Tests for MusicDownloader initialization."""

    def test_init_creates_download_dir(self):
        """Test that init creates the download directory."""
        with patch("main.music_downloader.os.makedirs") as mock_makedirs:
            MusicDownloader()
            mock_makedirs.assert_called_once()

    def test_init_sets_ydl_options(self, downloader):
        """Test that init sets yt-dlp options."""
        opts = downloader._get_ydl_options()
        assert "format" in opts
        assert "outtmpl" in opts
        assert "quiet" in opts
        assert "noplaylist" in opts


class TestMusicDownloaderInfoExtraction:
    """Tests for info extraction methods."""

    def test_extract_info_success(self, downloader):
        """Test successful info extraction."""
        mock_info = {"title": "Test Song", "duration": 240, "categories": ["Music"]}
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info = MagicMock(return_value=mock_info)
        with patch("main.music_downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value = mock_ydl_instance
            
            result = downloader._extract_info("https://youtube.com/watch?v=test")
            assert result == mock_info

    def test_extract_info_download_error(self, downloader):
        """Test info extraction with download error."""
        import yt_dlp
        with patch("main.music_downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__ = MagicMock(return_value=None)
            mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
            mock_ydl.return_value.extract_info = MagicMock(
                side_effect=yt_dlp.utils.DownloadError("Network error")
            )
            
            result = downloader._extract_info("https://youtube.com/watch?v=test")
            assert result is None

    def test_extract_info_generic_error(self, downloader):
        """Test info extraction with generic error."""
        with patch("main.music_downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__ = MagicMock(return_value=None)
            mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
            mock_ydl.return_value.extract_info = MagicMock(side_effect=ValueError("Error"))
            
            result = downloader._extract_info("https://youtube.com/watch?v=test")
            assert result is None

    def test_validate_song_valid(self, downloader):
        """Test song validation passes for valid song."""
        info = {"duration": 240, "categories": ["Music"]}
        is_valid, error = downloader._validate_song(info)
        assert is_valid is True
        assert error == ""

    def test_validate_song_too_long(self, downloader):
        """Test song validation fails for too long song."""
        info = {"duration": 1000, "categories": ["Music"]}
        is_valid, error = downloader._validate_song(info)
        assert is_valid is False
        assert "troppo lunga" in error

    def test_validate_song_wrong_category(self, downloader):
        """Test song validation fails for wrong category."""
        info = {"duration": 240, "categories": ["Gaming"]}
        is_valid, error = downloader._validate_song(info)
        assert is_valid is False
        assert "categoria" in error

    def test_validate_song_no_duration(self, downloader):
        """Test song validation fails for missing duration."""
        info = {"categories": ["Music"]}
        is_valid, error = downloader._validate_song(info)
        assert is_valid is False
        assert "Durata non disponibile" in error

    def test_is_url_true(self, downloader):
        """Test URL detection returns True for valid URLs."""
        assert downloader._is_url("https://www.youtube.com/watch?v=test") is True
        assert downloader._is_url("https://youtu.be/test") is True

    def test_is_url_false(self, downloader):
        """Test URL detection returns False for non-URLs."""
        assert downloader._is_url("Bohemian Rhapsody") is False
        assert downloader._is_url("just a title") is False

    def test_get_video_info_success(self, downloader):
        """Test get_video_info returns valid info."""
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_search_youtube", return_value="https://youtube.com/watch?v=test"):
                with patch.object(downloader, "_extract_info", return_value={"duration": 240, "categories": ["Music"]}):
                    result = downloader.get_video_info("test song")
                    assert result is not None

    def test_get_video_info_invalid(self, downloader):
        """Test get_video_info returns None for invalid song."""
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_search_youtube", return_value="https://youtube.com/watch?v=test"):
                with patch.object(downloader, "_extract_info", return_value={"duration": 240, "categories": ["Gaming"]}):
                    result = downloader.get_video_info("test song")
                    assert result is None


class TestMusicDownloaderSearch:
    """Tests for YouTube search methods."""

    def test_search_youtube_no_results(self, downloader):
        """Test search returns None when no results."""
        with patch.object(downloader, "_search_youtube_candidates", return_value=[]):
            result = downloader._search_youtube("nonexistent song")
            assert result is None

    def test_search_youtube_with_results(self, downloader):
        """Test search returns first URL when results exist."""
        with patch.object(downloader, "_search_youtube_candidates", return_value=["https://youtube.com/watch?v=test"]):
            result = downloader._search_youtube("test song")
            assert result == "https://youtube.com/watch?v=test"

    def test_search_youtube_candidates_with_info_empty(self, downloader):
        """Test candidate search returns empty list on error."""
        with patch("main.music_downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__ = MagicMock(return_value=None)
            mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
            mock_ydl.return_value.extract_info = MagicMock(return_value={})
            
            result = downloader._search_youtube_candidates_with_info("test", max_results=5)
            assert result == []


class TestMusicDownloaderDownload:
    """Tests for download method."""

    def test_download_no_search_results(self, downloader):
        """Test download returns None when no search results."""
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_search_youtube_candidates_with_info", return_value=[]):
                result = downloader.download("nonexistent")
                assert result is None

    def test_download_file_already_exists(self, downloader, temp_dir):
        """Test download returns existing file path if file already exists."""
        existing_file = os.path.join(temp_dir, "existing.mp3")
        with open(existing_file, "w") as f:
            f.write("test")
        
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_search_youtube_candidates_with_info", return_value=[]):
                with patch("main.music_downloader.DOWNLOAD_DIR", temp_dir):
                    with patch("os.path.exists", return_value=True):
                        result = downloader.download("existing")
                        assert result == existing_file

    def test_download_raises_song_too_long(self, downloader):
        """Test download raises _SongTooLongError when all candidates too long."""
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_search_youtube_candidates_with_info", return_value=[
                ("https://youtube.com/watch?v=1", {"duration": 1000, "categories": ["Music"]}),
                ("https://youtube.com/watch?v=2", {"duration": 1200, "categories": ["Music"]}),
            ]):
                with pytest.raises(_SongTooLongError):
                    downloader.download("long song")

    def test_download_raises_category_error(self, downloader):
        """Test download raises _CategoryError when all candidates wrong category."""
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_search_youtube_candidates_with_info", return_value=[
                ("https://youtube.com/watch?v=1", {"duration": 240, "categories": ["Gaming"]}),
                ("https://youtube.com/watch?v=2", {"duration": 300, "categories": ["Gaming"]}),
            ]):
                with pytest.raises(_CategoryError):
                    downloader.download("gaming video")


class TestMusicDownloaderUtilities:
    """Tests for utility methods."""

    def test_get_random_downloaded_file_no_files(self, downloader, temp_dir):
        """Test get_random_downloaded_file returns None when no files."""
        with patch("main.music_downloader.DOWNLOAD_DIR", temp_dir):
            result = downloader.get_random_downloaded_file()
            assert result is None

    def test_get_random_downloaded_file_with_files(self, downloader, temp_dir):
        """Test get_random_downloaded_file returns a file path."""
        test_file = os.path.join(temp_dir, "test.mp3")
        with open(test_file, "w") as f:
            f.write("test")
        
        with patch("main.music_downloader.DOWNLOAD_DIR", temp_dir):
            with patch("random.choice", return_value="test.mp3"):
                result = downloader.get_random_downloaded_file()
                assert result == test_file

    def test_get_search_results_empty(self, downloader):
        """Test get_search_results returns empty list on error."""
        with patch("main.music_downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__ = MagicMock(return_value=None)
            mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
            mock_ydl.return_value.extract_info = MagicMock(return_value={})
            
            result = downloader.get_search_results("test")
            assert result == []

    def test_get_song_info_local_file(self, downloader, temp_dir):
        """Test get_song_info returns info for local file."""
        local_file = os.path.join(temp_dir, "test song.mp3")
        with open(local_file, "w") as f:
            f.write("test")
        
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_find_matching_file", return_value=local_file):
                with patch("os.path.exists", return_value=True):
                    with patch.object(downloader, "_get_local_file_duration", return_value=240):
                        result = downloader.get_song_info("test song")
                        assert result is not None
                        assert result["title"] == "test song"

    def test_get_song_info_no_match(self, downloader):
        """Test get_song_info returns None when no match."""
        with patch.object(downloader, "_is_url", return_value=False):
            with patch.object(downloader, "_find_matching_file", return_value=None):
                with patch.object(downloader, "_search_youtube", return_value=None):
                    result = downloader.get_song_info("nonexistent")
                    assert result is None
