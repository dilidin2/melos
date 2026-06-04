"""Tests for admin permission system (defense in depth)."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from main.command_processor import CommandProcessor


class TestAdminPermissionsCommandProcessor:
    """Tests for permission checks in CommandProcessor.process()."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services with proper async mocks."""
        services = MagicMock()
        services.bot = MagicMock()
        services.bot.chat_message = MagicMock()
        services.bot.chat_message.send_public = AsyncMock()
        services.admin_commands = MagicMock()
        services.music_commands = MagicMock()
        services.utility_commands = MagicMock()
        services.playlist_commands = MagicMock()
        services.analytics_commands = MagicMock()
        return services

    def _make_processor(self, services, admin_users):
        """Create a CommandProcessor with mocked ADMIN_USERS."""
        with patch("main.command_processor.ADMIN_USERS", admin_users):
            return CommandProcessor(services=services)

    # --- Non-admin blocked ---

    @pytest.mark.asyncio
    async def test_non_admin_blocked_blacklist(self, mock_services):
        """Non-admin user gets permission error on !blacklist."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!blacklist targetuser", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    @pytest.mark.asyncio
    async def test_non_admin_blocked_unblacklist(self, mock_services):
        """Non-admin user gets permission error on !unblacklist."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!unblacklist targetuser", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    @pytest.mark.asyncio
    async def test_non_admin_blocked_blacklist_list(self, mock_services):
        """Non-admin user gets permission error on !blacklist_list."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!blacklist_list", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    @pytest.mark.asyncio
    async def test_non_admin_blocked_skippa(self, mock_services):
        """Non-admin user gets permission error on !skippa."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!skippa", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    @pytest.mark.asyncio
    async def test_non_admin_blocked_skip(self, mock_services):
        """Non-admin user gets permission error on !skip (alias)."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!skip", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    @pytest.mark.asyncio
    async def test_non_admin_blocked_rimuovi_coda(self, mock_services):
        """Non-admin user gets permission error on !rimuovi_coda."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!rimuovi_coda 1", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    @pytest.mark.asyncio
    async def test_non_admin_blocked_clear_queue(self, mock_services):
        """Non-admin user gets permission error on !clear_queue."""
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!clear_queue", "randomuser", "ch")
        assert result is True
        msg = mock_services.bot.chat_message.send_public.call_args[0][1]
        assert "⛔ Non hai i permessi" in msg

    # --- Admin allowed ---

    @pytest.mark.asyncio
    async def test_admin_allowed_skippa(self, mock_services):
        """Admin user can execute !skippa."""
        mock_services.admin_commands.cmd_skippa = AsyncMock(
            return_value="⏭️ Canzone saltata!"
        )
        proc = self._make_processor(mock_services, admin_users=["admin1"])
        result = await proc.process("!skippa", "admin1", "ch")
        assert result is True
        mock_services.admin_commands.cmd_skippa.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_allowed_skip_alias(self, mock_services):
        """Admin user can execute !skip (alias for skippa)."""
        mock_services.admin_commands.cmd_skippa = AsyncMock(
            return_value="⏭️ Canzone saltata!"
        )
        proc = self._make_processor(mock_services, admin_users=["admin1"])
        result = await proc.process("!skip", "admin1", "ch")
        assert result is True
        mock_services.admin_commands.cmd_skippa.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_allowed_clear_queue(self, mock_services):
        """Admin user can execute !clear_queue."""
        mock_services.admin_commands.cmd_clear_queue = AsyncMock(
            return_value="🗑️ Coda svuotata: **0** canzoni rimosse"
        )
        proc = self._make_processor(mock_services, admin_users=["admin1"])
        result = await proc.process("!clear_queue", "admin1", "ch")
        assert result is True
        mock_services.admin_commands.cmd_clear_queue.assert_called_once()

    # --- Case insensitivity ---

    @pytest.mark.asyncio
    async def test_admin_check_case_insensitive(self, mock_services):
        """Admin check should be case-insensitive."""
        mock_services.admin_commands.cmd_skippa = AsyncMock(
            return_value="⏭️ Canzone saltata!"
        )
        proc = self._make_processor(mock_services, admin_users=["AdminOne"])
        # "adminone" should match "AdminOne"
        result = await proc.process("!skippa", "adminone", "ch")
        assert result is True
        mock_services.admin_commands.cmd_skippa.assert_called_once()

    # --- Non-admin commands still work ---

    @pytest.mark.asyncio
    async def test_non_admin_can_use_help(self, mock_services):
        """Non-admin user can still use !help."""
        mock_services.utility_commands.cmd_help = AsyncMock(
            return_value="Help text"
        )
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!help", "randomuser", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_non_admin_can_use_version(self, mock_services):
        """Non-admin user can still use !version."""
        mock_services.utility_commands.cmd_version = AsyncMock(
            return_value="v1.0.0"
        )
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!version", "randomuser", "ch")
        assert result is True

    @pytest.mark.asyncio
    async def test_non_admin_can_use_stats(self, mock_services):
        """Non-admin user can still use !stats."""
        mock_services.analytics_commands.cmd_stats = AsyncMock(
            return_value="Stats"
        )
        proc = self._make_processor(mock_services, admin_users=[])
        result = await proc.process("!stats", "randomuser", "ch")
        assert result is True


class TestAdminPermissionsAdminCommands:
    """Tests for defense-in-depth permission checks in AdminCommands."""

    @pytest.fixture
    def mock_admin_handler(self):
        handler = MagicMock()
        handler.add_blacklist = MagicMock(return_value=True)
        handler.remove_blacklist = MagicMock(return_value=True)
        handler.get_blacklist_list = MagicMock(return_value=[])
        return handler

    @pytest.fixture
    def mock_audio_player(self):
        player = MagicMock()
        player.is_playing = MagicMock(return_value=True)
        player.stop = MagicMock()
        return player

    @pytest.fixture
    def mock_request_queue(self):
        queue = MagicMock()
        queue.qsize = MagicMock(return_value=0)
        queue.is_processing = MagicMock(return_value=False)
        return queue

    def _make_admin_commands(self, admin_handler, audio_player, request_queue, admin_users):
        """Create AdminCommands with mocked ADMIN_USERS."""
        from commands.admin import AdminCommands
        with patch("commands.admin.ADMIN_USERS", admin_users):
            return AdminCommands(
                admin_handler=admin_handler,
                audio_player=audio_player,
                request_queue=request_queue,
            )

    @pytest.mark.asyncio
    async def test_admin_blacklist_blocks_non_admin(self, mock_admin_handler):
        """cmd_blacklist blocks non-admin at method level."""
        cmd = self._make_admin_commands(mock_admin_handler, None, None, admin_users=["admin1"])
        result = await cmd.cmd_blacklist("randomuser", "target")
        assert "⛔ Non hai i permessi" in result

    @pytest.mark.asyncio
    async def test_admin_skippa_blocks_non_admin(self, mock_audio_player):
        """cmd_skippa blocks non-admin at method level."""
        cmd = self._make_admin_commands(None, mock_audio_player, None, admin_users=["admin1"])
        result = await cmd.cmd_skippa("randomuser")
        assert "⛔ Non hai i permessi" in result

    @pytest.mark.asyncio
    async def test_admin_skippa_allows_admin(self, mock_audio_player):
        """cmd_skippa allows admin at method level."""
        cmd = self._make_admin_commands(None, mock_audio_player, None, admin_users=["admin1"])
        result = await cmd.cmd_skippa("admin1")
        assert "⏭️" in result

    @pytest.mark.asyncio
    async def test_admin_clear_queue_blocks_non_admin(self, mock_request_queue):
        """cmd_clear_queue blocks non-admin at method level."""
        cmd = self._make_admin_commands(None, None, mock_request_queue, admin_users=["admin1"])
        result = await cmd.cmd_clear_queue("randomuser")
        assert "⛔ Non hai i permessi" in result

    @pytest.mark.asyncio
    async def test_admin_rimuovi_coda_blocks_non_admin(self, mock_request_queue):
        """cmd_rimuovi_coda blocks non-admin at method level."""
        cmd = self._make_admin_commands(None, None, mock_request_queue, admin_users=["admin1"])
        result = await cmd.cmd_rimuovi_coda("randomuser", "1")
        assert "⛔ Non hai i permessi" in result

    @pytest.mark.asyncio
    async def test_admin_blacklist_list_blocks_non_admin(self, mock_admin_handler):
        """cmd_blacklist_list blocks non-admin at method level."""
        cmd = self._make_admin_commands(mock_admin_handler, None, None, admin_users=["admin1"])
        result = await cmd.cmd_blacklist_list("randomuser")
        assert "⛔ Non hai i permessi" in result

    @pytest.mark.asyncio
    async def test_admin_unblacklist_blocks_non_admin(self, mock_admin_handler):
        """cmd_unblacklist blocks non-admin at method level."""
        cmd = self._make_admin_commands(mock_admin_handler, None, None, admin_users=["admin1"])
        result = await cmd.cmd_unblacklist("randomuser", "target")
        assert "⛔ Non hai i permessi" in result


class TestAdminSkipAlias:
    """Tests for !skip alias mapping to cmd_skippa."""

    @pytest.fixture
    def mock_services(self):
        services = MagicMock()
        services.bot = MagicMock()
        services.bot.chat_message = MagicMock()
        services.bot.chat_message.send_public = AsyncMock()
        services.admin_commands = MagicMock()
        services.music_commands = MagicMock()
        services.utility_commands = MagicMock()
        services.playlist_commands = MagicMock()
        services.analytics_commands = MagicMock()
        return services

    def _make_processor(self, services, admin_users):
        with patch("main.command_processor.ADMIN_USERS", admin_users):
            return CommandProcessor(services=services)

    @pytest.mark.asyncio
    async def test_skip_alias_resolved_to_skippa(self, mock_services):
        """!skip should be resolved to cmd_skippa (same as !skippa)."""
        mock_services.admin_commands.cmd_skippa = AsyncMock(
            return_value="⏭️ Canzone saltata!"
        )
        proc = self._make_processor(mock_services, admin_users=["admin1"])
        result = await proc.process("!skip", "admin1", "ch")
        assert result is True
        mock_services.admin_commands.cmd_skippa.assert_called_once()

    @pytest.mark.asyncio
    async def test_skippa_still_works(self, mock_services):
        """!skippa should still work as before."""
        mock_services.admin_commands.cmd_skippa = AsyncMock(
            return_value="⏭️ Canzone saltata!"
        )
        proc = self._make_processor(mock_services, admin_users=["admin1"])
        result = await proc.process("!skippa", "admin1", "ch")
        assert result is True
        mock_services.admin_commands.cmd_skippa.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_case_insensitive(self, mock_services):
        """!SKIP should also work (case insensitive)."""
        mock_services.admin_commands.cmd_skippa = AsyncMock(
            return_value="⏭️ Canzone saltata!"
        )
        proc = self._make_processor(mock_services, admin_users=["admin1"])
        result = await proc.process("!SKIP", "admin1", "ch")
        assert result is True
        mock_services.admin_commands.cmd_skippa.assert_called_once()
