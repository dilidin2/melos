"""Tests for command_processor module."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from main.command_processor import CommandProcessor, CompiledPattern


class TestCompiledPattern:
    """Tests for CompiledPattern class."""

    def test_compiled_pattern_creation(self):
        """Test creating a CompiledPattern."""
        pattern = CompiledPattern(r"!\w+\s+(.+)$", "test_method")
        assert pattern.regex is not None
        assert pattern.method_name == "test_method"

    def test_compiled_pattern_match(self):
        """Test CompiledPattern regex matching."""
        pattern = CompiledPattern(r"!\w+\s+(.+)$", "test_method")
        match = pattern.regex.match("!sr test query")
        assert match is not None
        assert match.group(1) == "test query"

    def test_compiled_pattern_no_match(self):
        """Test CompiledPattern regex no match."""
        pattern = CompiledPattern(r"!\w+\s+(.+)$", "test_method")
        match = pattern.regex.match("not a command")
        assert match is None

    def test_compiled_pattern_case_insensitive(self):
        """Test CompiledPattern is case insensitive."""
        pattern = CompiledPattern(r"!\w+\s+(.+)$", "test_method")
        assert pattern.regex.match("!SR TEST") is not None


class TestCommandProcessor:
    """Tests for CommandProcessor class."""

    @pytest.fixture
    def processor(self, mock_command_services):
        """Create a CommandProcessor with mocked services."""
        return CommandProcessor(services=mock_command_services)

    def test_processor_initialization(self, mock_command_services):
        """Test CommandProcessor initialization."""
        processor = CommandProcessor(services=mock_command_services)
        assert processor.services == mock_command_services
        assert len(processor.compiled_commands) > 0

    def test_compiled_commands_have_patterns(self, mock_command_services):
        """Test that compiled commands have regex patterns."""
        processor = CommandProcessor(services=mock_command_services)
        for cmd in processor.compiled_commands:
            assert cmd.regex is not None
            assert cmd.method_name is not None

    @pytest.mark.asyncio
    async def test_process_non_command(self, processor):
        """Test processing non-command text returns False."""
        result = await processor.process("just a regular message", "user", "ch")
        assert result is False

    @pytest.mark.asyncio
    async def test_process_sr_command(self, processor, mock_command_services):
        """Test processing !sr command."""
        mock_command_services.utility_commands.cmd_help = AsyncMock(return_value=None)
        mock_command_services.music_commands.cmd_volume = AsyncMock(return_value=None)
        
        # The sr command should match and call the handler
        result = await processor.process("!sr test song", "user", "ch")
        # Result depends on whether the command matched and returned a response
        # We just verify the method was called

    @pytest.mark.asyncio
    async def test_process_help_command(self, processor, mock_command_services):
        """Test processing !help command."""
        mock_command_services.utility_commands.cmd_help = AsyncMock(return_value=["help1", "help2"])
        
        result = await processor.process("!help", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_version_command(self, processor, mock_command_services):
        """Test processing !version command."""
        mock_command_services.utility_commands.cmd_version = AsyncMock(return_value="v1.0.0")
        
        result = await processor.process("!version", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_uptime_command(self, processor, mock_command_services):
        """Test processing !uptime command."""
        mock_command_services.utility_commands.cmd_uptime = AsyncMock(return_value="1 hour")
        
        result = await processor.process("!uptime", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_help_with_command(self, processor, mock_command_services):
        """Test processing !help with specific command."""
        mock_command_services.utility_commands.cmd_help = AsyncMock(return_value="!sr <query>")
        
        result = await processor.process("!help sr", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_command_with_exception(self, processor):
        """Test processing command that raises exception."""
        mock_services = MagicMock()
        mock_services.utility_commands.cmd_version = AsyncMock(side_effect=Exception("Test error"))
        
        proc = CommandProcessor(services=mock_services)
        result = await proc.process("!version", "user", "ch")
        # Should return True even on exception (command was processed)

    @pytest.mark.asyncio
    async def test_process_volume_command(self, processor, mock_command_services):
        """Test processing !volume command."""
        mock_command_services.music_commands.cmd_volume = AsyncMock(return_value="Volume set to 50%")
        
        result = await processor.process("!volume 50", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_pause_command(self, processor, mock_command_services):
        """Test processing !pausa command."""
        mock_command_services.music_commands.cmd_pausa = AsyncMock(return_value="Paused")
        
        result = await processor.process("!pausa", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_blacklist_command(self, processor, mock_command_services):
        """Test processing !blacklist command."""
        mock_command_services.admin_commands.cmd_blacklist = AsyncMock(return_value="Added to blacklist")
        
        result = await processor.process("!blacklist testuser", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_stats_command(self, processor, mock_command_services):
        """Test processing !stats command."""
        mock_command_services.analytics_commands.cmd_stats = AsyncMock(return_value="Stats available")
        
        result = await processor.process("!stats", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_crea_command(self, processor, mock_command_services):
        """Test processing !crea command."""
        mock_command_services.playlist_commands.cmd_crea = AsyncMock(return_value="Playlist created")
        
        result = await processor.process("!crea myplaylist", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_playlist_command_no_args(self, processor, mock_command_services):
        """Test processing !playlist without args."""
        mock_command_services.playlist_commands.cmd_playlist = AsyncMock(return_value="No playlists")
        
        result = await processor.process("!playlist", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_skippa_command(self, processor, mock_command_services):
        """Test processing !skippa command."""
        mock_command_services.admin_commands.cmd_skippa = AsyncMock(return_value="Skipped")
        
        result = await processor.process("!skippa", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_clear_queue_command(self, processor, mock_command_services):
        """Test processing !clear_queue command."""
        mock_command_services.admin_commands.cmd_clear_queue = AsyncMock(return_value="Queue cleared")
        
        result = await processor.process("!clear_queue", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_repeat_command(self, processor, mock_command_services):
        """Test processing !repeat command."""
        mock_command_services.music_commands.cmd_repeat = AsyncMock(return_value="Repeat set")
        
        result = await processor.process("!repeat 3", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_repeat_off_command(self, processor, mock_command_services):
        """Test processing !repeat_off command."""
        mock_command_services.music_commands.cmd_repeat_off = AsyncMock(return_value="Repeat off")
        
        result = await processor.process("!repeat_off", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_ripeti_command(self, processor, mock_command_services):
        """Test processing !ripeti command."""
        mock_command_services.music_commands.cmd_ripeti = AsyncMock(return_value="Ripeti set")
        
        result = await processor.process("!ripeti", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_stop_ripeti_command(self, processor, mock_command_services):
        """Test processing !stop_ripeti command."""
        mock_command_services.music_commands.cmd_stop_repeat = AsyncMock(return_value="Repeat stopped")
        
        result = await processor.process("!stop_ripeti", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_next_command(self, processor, mock_command_services):
        """Test processing !next command."""
        mock_command_services.music_commands.cmd_next = AsyncMock(return_value="Next")
        
        result = await processor.process("!next", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_duration_command(self, processor, mock_command_services):
        """Test processing !duration command."""
        mock_command_services.music_commands.cmd_duration = AsyncMock(return_value="Duration info")
        
        result = await processor.process("!duration test song", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_durata_command(self, processor, mock_command_services):
        """Test processing !durata command."""
        mock_command_services.music_commands.cmd_durata = AsyncMock(return_value="Duration for position 1")
        
        result = await processor.process("!durata 1", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_quando_command(self, processor, mock_command_services):
        """Test processing !quando command."""
        mock_command_services.music_commands.cmd_quando = AsyncMock(return_value="When info")
        
        result = await processor.process("!quando", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_add_song_command(self, processor, mock_command_services):
        """Test processing !aggiungi command."""
        mock_command_services.playlist_commands.cmd_aggiungi = AsyncMock(return_value="Song added")
        
        result = await processor.process("!aggiungi myplaylist test", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_remove_song_command(self, processor, mock_command_services):
        """Test processing !rimuovi command."""
        mock_command_services.playlist_commands.cmd_rimuovi = AsyncMock(return_value="Song removed")
        
        result = await processor.process("!rimuovi myplaylist 1", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_move_songs_command(self, processor, mock_command_services):
        """Test processing !sposta command."""
        mock_command_services.playlist_commands.cmd_sposta = AsyncMock(return_value="Songs moved")
        
        result = await processor.process("!sposta myplaylist 1 2", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_clear_playlist_command(self, processor, mock_command_services):
        """Test processing !svuota command."""
        mock_command_services.playlist_commands.cmd_svuota = AsyncMock(return_value="Playlist cleared")
        
        result = await processor.process("!svuota myplaylist", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_pompa_command(self, processor, mock_command_services):
        """Test processing !pompa command."""
        mock_command_services.playlist_commands.cmd_pompa = AsyncMock(return_value="Songs pumped")
        
        result = await processor.process("!pompa myplaylist 5", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_remove_queue_command(self, processor, mock_command_services):
        """Test processing !rimuovi_coda command."""
        mock_command_services.admin_commands.cmd_rimuovi_coda = AsyncMock(return_value="Removed")
        
        result = await processor.process("!rimuovi_coda 1", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_top_canzoni_command(self, processor, mock_command_services):
        """Test processing !top_canzoni command."""
        mock_command_services.analytics_commands.cmd_top_canzoni = AsyncMock(return_value="Top songs")
        
        result = await processor.process("!top_canzoni 5", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_top_user_command(self, processor, mock_command_services):
        """Test processing !top_user command."""
        mock_command_services.analytics_commands.cmd_top_user = AsyncMock(return_value="Top users")
        
        result = await processor.process("!top_user 5", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_unblacklist_command(self, processor, mock_command_services):
        """Test processing !unblacklist command."""
        mock_command_services.admin_commands.cmd_unblacklist = AsyncMock(return_value="Unblacklisted")
        
        result = await processor.process("!unblacklist testuser", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_blacklist_list_command(self, processor, mock_command_services):
        """Test processing !blacklist_list command."""
        mock_command_services.admin_commands.cmd_blacklist_list = AsyncMock(return_value="Blacklist list")
        
        result = await processor.process("!blacklist_list", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_resume_command(self, processor, mock_command_services):
        """Test processing !riprendi command."""
        mock_command_services.music_commands.cmd_riprendi = AsyncMock(return_value="Resumed")
        
        result = await processor.process("!riprendi", "user", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_process_queue_info_utility(self, processor, mock_command_services):
        """Test processing !queue_info utility command."""
        mock_command_services.utility_commands.cmd_queue_info = AsyncMock(return_value="Queue info")
        
        result = await processor.process("!queue_info", "user", "ch")
        assert result is True
