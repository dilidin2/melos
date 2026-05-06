"""Tests for playlist commands module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from commands.playlists import PlaylistCommands


class TestPlaylistCommands:
    """Tests for PlaylistCommands class."""

    @pytest.fixture
    def mock_cmd(self):
        """Create a mock command object."""
        cmd = MagicMock()
        cmd.user.name = "testuser"
        cmd.room.room_id = "12345"
        cmd.parameter = ""
        return cmd

    @pytest.mark.asyncio
    async def test_cmd_crea(self, mock_cmd):
        """Test !crea command."""
        mock_cmd.parameter = "My Playlist"
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.create_playlist = MagicMock(return_value=MagicMock(id="123"))
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_crea(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_crea_no_name(self, mock_cmd):
        """Test !crea without name."""
        mock_cmd.parameter = ""
        mock_command_services = MagicMock()
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_crea(mock_cmd)
        assert result is not None
        assert "Errore" in result

    @pytest.mark.asyncio
    async def test_cmd_playlist(self, mock_cmd):
        """Test !playlist command."""
        mock_cmd.parameter = ""
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.get_user_playlists = MagicMock(return_value=[
            MagicMock(id="1", nome="Playlist 1"),
            MagicMock(id="2", nome="Playlist 2"),
        ])
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_playlist(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_playlist_no_playlists(self, mock_cmd):
        """Test !playlist with no playlists."""
        mock_cmd.parameter = ""
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.get_user_playlists = MagicMock(return_value=[])
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_playlist(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_aggiungi(self, mock_cmd):
        """Test !aggiungi command."""
        mock_cmd.parameter = "My Playlist Test Song"
        mock_command_services = MagicMock()
        mock_command_services.music_downloader.get_song_info = MagicMock(return_value={
            "title": "Test Song",
            "duration": 240,
        })
        mock_command_services.playlist_manager.add_song_to_playlist = MagicMock(return_value=True)
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_aggiungi(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_rimuovi(self, mock_cmd):
        """Test !rimuovi command."""
        mock_cmd.parameter = "My Playlist 1"
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.remove_song_from_playlist = MagicMock(return_value=True)
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_rimuovi(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_sposta(self, mock_cmd):
        """Test !sposta command."""
        mock_cmd.parameter = "My Playlist 1 2"
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.swap_songs_in_playlist = MagicMock(return_value=True)
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_sposta(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_svuota(self, mock_cmd):
        """Test !svuota command."""
        mock_cmd.parameter = "My Playlist"
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.clear_playlist = MagicMock(return_value=True)
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_svuota(mock_cmd)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_pompa(self, mock_cmd):
        """Test !pompa command."""
        mock_cmd.parameter = "My Playlist 5"
        mock_command_services = MagicMock()
        mock_command_services.playlist_manager.pompa_songs = MagicMock(return_value=[
            MagicMock(query="Song 1"),
            MagicMock(query="Song 2"),
        ])
        mock_command_services.request_queue.put = MagicMock()
        commands = PlaylistCommands(services=mock_command_services)
        
        result = await commands.cmd_pompa(mock_cmd)
        assert result is not None
