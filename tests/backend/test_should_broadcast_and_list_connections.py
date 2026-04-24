"""
Test ConnectionManager broadcast and connections list.
"""

import pytest
from backend.connection_manager import ConnectionManager


class TestConnectionManagerBroadcast:
    """Broadcasting and connection inspection."""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_ws(self):
        class MockWS:
            def __init__(self):
                self.sent = []
                self.closed = False
            async def accept(self):
                pass
            async def send_text(self, msg):
                self.sent.append(msg)
            def close(self):
                self.closed = True
        return MockWS()

    @pytest.mark.asyncio
    async def test_should_broadcast_message_to_all_connections(self, manager, mock_ws):
        ws1 = mock_ws
        ws2 = type(mock_ws)()
        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.broadcast({"test": "data"})
        assert len(ws1.sent) == 1
        assert ws1.sent[0] == '{"test": "data"}'
        assert len(ws2.sent) == 1

    def test_should_return_empty_list_when_no_connections(self, manager):
        assert manager.get_connections() == []

    @pytest.mark.asyncio
    async def test_should_return_active_connections_list(self, manager, mock_ws):
        await manager.connect(mock_ws)
        conns = manager.get_connections()
        assert len(conns) == 1
        assert conns[0] is mock_ws
