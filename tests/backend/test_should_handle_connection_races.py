"""
TDD Tests for ConnectionManager race conditions.

These tests guard against the ValueError that occurs when disconnect() is
called twice on the same websocket (e.g.  double disconnect from client
+ send_message cleanup) or when send_message cleans up a stale reference.
"""

import pytest
from unittest.mock import MagicMock

from backend.connection_manager import ConnectionManager


class TestConnectionManagerRaceConditions:
    """Test ConnectionManager robustness under race / duplicate calls."""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_ws(self):
        ws = MagicMock()
        ws.send_text = MagicMock()
        return ws

    def test_should_not_raise_on_double_disconnect(self, manager, mock_ws):
        """
        GIVEN: A websocket that has already been disconnected
        WHEN: disconnect() is called a second time on the same websocket
        THEN: It should silently succeed (not raise ValueError)
        """
        # GIVEN
        manager.active_connections = [mock_ws]

        # WHEN - first disconnect
        manager.disconnect(mock_ws)
        assert mock_ws not in manager.active_connections

        # WHEN - second disconnect (race condition)
        try:
            manager.disconnect(mock_ws)
        except ValueError:
            pytest.fail("disconnect() must not raise ValueError on double disconnect")

        # THEN
        assert manager.active_connections == []

    @pytest.mark.asyncio
    async def test_should_not_raise_when_send_message_cleans_up_removed_ws(self, manager, mock_ws):
        """
        GIVEN: A websocket removed from active_connections externally
        WHEN: send_message tries to send and then cleans up
        THEN: It should silently succeed (not raise ValueError from .remove)
        """
        # GIVEN - ws is NOT in active_connections but send_message is called anyway
        assert mock_ws not in manager.active_connections

        # WHEN
        try:
            await manager.send_message({"type": "test"}, mock_ws)
        except ValueError:
            pytest.fail("send_message() must not raise ValueError when cleaning up stale websocket")

        # THEN
        assert manager.active_connections == []

    @pytest.mark.asyncio
    async def test_should_remove_websocket_on_send_failure(self, manager):
        """
        GIVEN: Multiple active connections where one is broken
        WHEN: send_message is called on the broken websocket
        THEN: Only the broken websocket is removed, others remain
        """
        # GIVEN
        good_ws = MagicMock()
        bad_ws = MagicMock()
        bad_ws.send_text = MagicMock(side_effect=RuntimeError("Connection lost"))

        manager.active_connections = [good_ws, bad_ws]

        # WHEN
        await manager.send_message({"type": "test"}, bad_ws)

        # THEN
        assert bad_ws not in manager.active_connections
        assert good_ws in manager.active_connections
        assert len(manager.active_connections) == 1
