"""Tests for the WebSocket ConnectionManager."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from pulse_board.infrastructure.websocket.connection_manager import (
    ConnectionManager,
)


def _make_mock_websocket() -> AsyncMock:
    """Create a mock WebSocket with async methods."""
    return AsyncMock()


class TestConnect:
    """Tests for ConnectionManager.connect."""

    @pytest.mark.asyncio
    async def test_connect_accepts_and_tracks_websocket(self) -> None:
        """Should call accept() on the websocket and track it."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        await manager.connect(ws)

        ws.accept.assert_awaited_once()
        assert ws in manager._connections


class TestDisconnect:
    """Tests for ConnectionManager.disconnect."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self) -> None:
        """Should remove the websocket from tracked connections."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect(ws)

        await manager.disconnect(ws)

        assert ws not in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_is_noop(self) -> None:
        """Disconnecting a websocket that was never connected should not raise."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        await manager.disconnect(ws)

        assert len(manager._connections) == 0


class TestBroadcast:
    """Tests for ConnectionManager.broadcast."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self) -> None:
        """Should send the message to every connected websocket."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()
        ws3 = _make_mock_websocket()
        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)

        ws1.send_json.assert_awaited_once_with(message)
        ws2.send_json.assert_awaited_once_with(message)
        ws3.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self) -> None:
        """When send_json raises, the dead connection should be removed."""
        manager = ConnectionManager()
        alive_ws = _make_mock_websocket()
        dead_ws = _make_mock_websocket()
        dead_ws.send_json.side_effect = RuntimeError("connection closed")
        await manager.connect(alive_ws)
        await manager.connect(dead_ws)

        await manager.broadcast({"type": "test"})

        assert dead_ws not in manager._connections
        assert alive_ws in manager._connections
        alive_ws.send_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections_is_noop(self) -> None:
        """Broadcasting with no connections should not raise."""
        manager = ConnectionManager()

        await manager.broadcast({"type": "test"})

        # No exception means success


class TestPublishScoreUpdate:
    """Tests for ConnectionManager.publish_score_update."""

    @pytest.mark.asyncio
    async def test_publish_score_update_broadcasts_correct_format(
        self,
    ) -> None:
        """Should broadcast a score_update message with correct fields."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect(ws)

        topic_id = uuid.uuid4()
        await manager.publish_score_update(topic_id, score=42)

        ws.send_json.assert_awaited_once_with(
            {
                "type": "score_update",
                "topic_id": str(topic_id),
                "score": 42,
            }
        )


class TestPublishTopicCensured:
    """Tests for ConnectionManager.publish_topic_censured."""

    @pytest.mark.asyncio
    async def test_publish_topic_censured_broadcasts_correct_format(
        self,
    ) -> None:
        """Should broadcast a topic_censured message with correct fields."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect(ws)

        topic_id = uuid.uuid4()
        await manager.publish_topic_censured(topic_id)

        ws.send_json.assert_awaited_once_with(
            {
                "type": "topic_censured",
                "topic_id": str(topic_id),
            }
        )


class TestPublishNewTopic:
    """Tests for ConnectionManager.publish_new_topic."""

    @pytest.mark.asyncio
    async def test_publish_new_topic_broadcasts_correct_format(
        self,
    ) -> None:
        """Should broadcast a new_topic message with ISO datetime."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect(ws)

        topic_id = uuid.uuid4()
        created_at = datetime(2026, 2, 17, 12, 0, 0, tzinfo=UTC)
        await manager.publish_new_topic(
            topic_id=topic_id,
            content="Test topic",
            score=0,
            created_at=created_at,
        )

        ws.send_json.assert_awaited_once_with(
            {
                "type": "new_topic",
                "topic": {
                    "id": str(topic_id),
                    "content": "Test topic",
                    "score": 0,
                    "created_at": "2026-02-17T12:00:00+00:00",
                },
            }
        )

    @pytest.mark.asyncio
    async def test_publish_new_topic_with_naive_datetime(self) -> None:
        """Should handle naive datetime in isoformat output."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect(ws)

        topic_id = uuid.uuid4()
        created_at = datetime(2026, 1, 1, 0, 0, 0)  # noqa: DTZ001
        await manager.publish_new_topic(
            topic_id=topic_id,
            content="Naive dt",
            score=5,
            created_at=created_at,
        )

        sent_message = ws.send_json.call_args[0][0]
        assert sent_message["type"] == "new_topic"
        assert sent_message["topic"]["created_at"] == "2026-01-01T00:00:00"


class TestPublishNewTopicMultiClient:
    """Tests that publish_new_topic reaches multiple clients."""

    @pytest.mark.asyncio
    async def test_publish_new_topic_sends_to_all_clients(
        self,
    ) -> None:
        """Should send a new_topic message to all 3 connected clients."""
        manager = ConnectionManager()
        clients = [_make_mock_websocket() for _ in range(3)]
        for ws in clients:
            await manager.connect(ws)

        topic_id = uuid.uuid4()
        created_at = datetime(2026, 2, 17, 12, 0, 0, tzinfo=UTC)
        await manager.publish_new_topic(
            topic_id=topic_id,
            content="Multi-client topic",
            score=0,
            created_at=created_at,
        )

        expected = {
            "type": "new_topic",
            "topic": {
                "id": str(topic_id),
                "content": "Multi-client topic",
                "score": 0,
                "created_at": "2026-02-17T12:00:00+00:00",
            },
        }
        for ws in clients:
            ws.send_json.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_publish_new_topic_skips_dead_client(
        self,
    ) -> None:
        """Dead clients should be removed; live ones still receive."""
        manager = ConnectionManager()
        alive = _make_mock_websocket()
        dead = _make_mock_websocket()
        dead.send_json.side_effect = RuntimeError("closed")
        await manager.connect(alive)
        await manager.connect(dead)

        topic_id = uuid.uuid4()
        created_at = datetime(2026, 2, 17, 12, 0, 0, tzinfo=UTC)
        await manager.publish_new_topic(
            topic_id=topic_id,
            content="Partial",
            score=0,
            created_at=created_at,
        )

        alive.send_json.assert_awaited_once()
        assert dead not in manager._connections
        assert alive in manager._connections


class TestPublishScoreUpdateMultiClient:
    """Tests that publish_score_update reaches multiple clients."""

    @pytest.mark.asyncio
    async def test_publish_score_update_sends_to_all_clients(
        self,
    ) -> None:
        """Should send score_update to both connected clients."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        topic_id = uuid.uuid4()
        await manager.publish_score_update(topic_id, score=7)

        expected = {
            "type": "score_update",
            "topic_id": str(topic_id),
            "score": 7,
        }
        ws1.send_json.assert_awaited_once_with(expected)
        ws2.send_json.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_publish_score_update_skips_dead_client(
        self,
    ) -> None:
        """Dead clients should be removed during score_update."""
        manager = ConnectionManager()
        alive = _make_mock_websocket()
        dead = _make_mock_websocket()
        dead.send_json.side_effect = RuntimeError("closed")
        await manager.connect(alive)
        await manager.connect(dead)

        topic_id = uuid.uuid4()
        await manager.publish_score_update(topic_id, score=3)

        alive.send_json.assert_awaited_once()
        assert dead not in manager._connections
        assert alive in manager._connections


class TestPublishTopicCensuredMultiClient:
    """Tests that publish_topic_censured reaches multiple clients."""

    @pytest.mark.asyncio
    async def test_publish_topic_censured_sends_to_all_clients(
        self,
    ) -> None:
        """Should send topic_censured to both connected clients."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        topic_id = uuid.uuid4()
        await manager.publish_topic_censured(topic_id)

        expected = {
            "type": "topic_censured",
            "topic_id": str(topic_id),
        }
        ws1.send_json.assert_awaited_once_with(expected)
        ws2.send_json.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_publish_topic_censured_skips_dead_client(
        self,
    ) -> None:
        """Dead clients should be removed during topic_censured."""
        manager = ConnectionManager()
        alive = _make_mock_websocket()
        dead = _make_mock_websocket()
        dead.send_json.side_effect = RuntimeError("closed")
        await manager.connect(alive)
        await manager.connect(dead)

        topic_id = uuid.uuid4()
        await manager.publish_topic_censured(topic_id)

        alive.send_json.assert_awaited_once()
        assert dead not in manager._connections
        assert alive in manager._connections


def _make_mock_websocket_with_ip(ip: str) -> AsyncMock:
    """Create a mock WebSocket with a specific client IP."""
    ws = _make_mock_websocket()
    client = MagicMock()
    client.host = ip
    ws.client = client
    return ws


class TestConnectionLimits:
    """Tests for ConnectionManager connection limits."""

    @pytest.mark.asyncio
    async def test_rejects_when_max_connections_reached(
        self,
    ) -> None:
        """Should reject with code 1013 at global limit."""
        manager = ConnectionManager(
            max_connections=2,
            max_connections_per_ip=100,
        )
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()
        ws3 = _make_mock_websocket()

        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        ws1.accept.assert_awaited_once()
        ws2.accept.assert_awaited_once()
        ws3.accept.assert_not_awaited()
        ws3.close.assert_awaited_once_with(code=1013)
        assert len(manager._connections) == 2

    @pytest.mark.asyncio
    async def test_rejects_when_per_ip_limit_reached(
        self,
    ) -> None:
        """Should reject with code 1013 at per-IP limit."""
        manager = ConnectionManager(
            max_connections=100,
            max_connections_per_ip=2,
        )
        ws1 = _make_mock_websocket_with_ip("1.2.3.4")
        ws2 = _make_mock_websocket_with_ip("1.2.3.4")
        ws3 = _make_mock_websocket_with_ip("1.2.3.4")

        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        ws1.accept.assert_awaited_once()
        ws2.accept.assert_awaited_once()
        ws3.accept.assert_not_awaited()
        ws3.close.assert_awaited_once_with(code=1013)

    @pytest.mark.asyncio
    async def test_allows_different_ips_when_per_ip_limit_reached(
        self,
    ) -> None:
        """Different IPs should not share per-IP limits."""
        manager = ConnectionManager(
            max_connections=100,
            max_connections_per_ip=1,
        )
        ws1 = _make_mock_websocket_with_ip("1.2.3.4")
        ws2 = _make_mock_websocket_with_ip("5.6.7.8")

        await manager.connect(ws1)
        await manager.connect(ws2)

        ws1.accept.assert_awaited_once()
        ws2.accept.assert_awaited_once()
        assert len(manager._connections) == 2

    @pytest.mark.asyncio
    async def test_accepts_after_disconnect_frees_slot(
        self,
    ) -> None:
        """Disconnecting should free a slot for new connections."""
        manager = ConnectionManager(
            max_connections=1,
            max_connections_per_ip=100,
        )
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()

        await manager.connect(ws1)
        await manager.disconnect(ws1)
        await manager.connect(ws2)

        ws2.accept.assert_awaited_once()
        assert ws2 in manager._connections


class TestConnectToChannel:
    """Tests for ConnectionManager.connect_to_channel."""

    @pytest.mark.asyncio
    async def test_connects_websocket_to_channel(self) -> None:
        """Should accept, track globally, and register in channel."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        await manager.connect_to_channel(ws, "event:123")

        ws.accept.assert_awaited_once()
        assert ws in manager._connections
        assert ws in manager._channels["event:123"]

    @pytest.mark.asyncio
    async def test_creates_channel_on_first_connect(self) -> None:
        """Should create the channel set if it does not exist."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        assert "new-channel" not in manager._channels
        await manager.connect_to_channel(ws, "new-channel")

        assert "new-channel" in manager._channels

    @pytest.mark.asyncio
    async def test_multiple_websockets_same_channel(self) -> None:
        """Should track multiple connections in the same channel."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()

        await manager.connect_to_channel(ws1, "event:abc")
        await manager.connect_to_channel(ws2, "event:abc")

        assert len(manager._channels["event:abc"]) == 2

    @pytest.mark.asyncio
    async def test_rejects_at_global_limit(self) -> None:
        """Should reject channel connection at global limit."""
        manager = ConnectionManager(
            max_connections=1,
            max_connections_per_ip=100,
        )
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()

        await manager.connect_to_channel(ws1, "event:1")
        await manager.connect_to_channel(ws2, "event:1")

        ws2.accept.assert_not_awaited()
        ws2.close.assert_awaited_once_with(code=1013)
        assert "event:1" in manager._channels
        assert len(manager._channels["event:1"]) == 1


class TestDisconnectFromChannel:
    """Tests for ConnectionManager.disconnect_from_channel."""

    @pytest.mark.asyncio
    async def test_removes_from_channel_and_global(self) -> None:
        """Should remove websocket from both channel and global set."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        await manager.connect_to_channel(ws, "event:123")
        await manager.disconnect_from_channel(ws, "event:123")

        assert ws not in manager._connections
        assert "event:123" not in manager._channels

    @pytest.mark.asyncio
    async def test_removes_empty_channel(self) -> None:
        """Should clean up channel dict when last connection leaves."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        await manager.connect_to_channel(ws, "event:cleanup")
        await manager.disconnect_from_channel(ws, "event:cleanup")

        assert "event:cleanup" not in manager._channels

    @pytest.mark.asyncio
    async def test_other_connections_remain_in_channel(self) -> None:
        """Should not affect other connections in the same channel."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()

        await manager.connect_to_channel(ws1, "event:stay")
        await manager.connect_to_channel(ws2, "event:stay")
        await manager.disconnect_from_channel(ws1, "event:stay")

        assert ws2 in manager._channels["event:stay"]
        assert ws1 not in manager._channels["event:stay"]

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_channel_is_noop(self) -> None:
        """Disconnecting from an unregistered channel should not raise."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()

        await manager.disconnect_from_channel(ws, "nonexistent")

        assert len(manager._connections) == 0


class TestBroadcastToChannel:
    """Tests for ConnectionManager.broadcast_to_channel."""

    @pytest.mark.asyncio
    async def test_sends_to_all_channel_connections(self) -> None:
        """Should send message to every websocket in the channel."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()

        await manager.connect_to_channel(ws1, "event:abc")
        await manager.connect_to_channel(ws2, "event:abc")

        msg = {"type": "test", "data": "hello"}
        await manager.broadcast_to_channel("event:abc", msg)

        ws1.send_json.assert_awaited_once_with(msg)
        ws2.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_does_not_send_to_other_channels(self) -> None:
        """Should not send messages to connections in other channels."""
        manager = ConnectionManager()
        ws1 = _make_mock_websocket()
        ws2 = _make_mock_websocket()

        await manager.connect_to_channel(ws1, "event:target")
        await manager.connect_to_channel(ws2, "event:other")

        await manager.broadcast_to_channel(
            "event:target",
            {"type": "targeted"},
        )

        ws1.send_json.assert_awaited_once()
        ws2.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_noop_for_empty_channel(self) -> None:
        """Should not raise when broadcasting to nonexistent channel."""
        manager = ConnectionManager()

        await manager.broadcast_to_channel(
            "nonexistent",
            {"type": "test"},
        )

    @pytest.mark.asyncio
    async def test_removes_dead_connections_from_channel(self) -> None:
        """Dead connections should be removed from both channel and global."""
        manager = ConnectionManager()
        alive = _make_mock_websocket()
        dead = _make_mock_websocket()
        dead.send_json.side_effect = RuntimeError("closed")

        await manager.connect_to_channel(alive, "event:cleanup")
        await manager.connect_to_channel(dead, "event:cleanup")

        await manager.broadcast_to_channel(
            "event:cleanup",
            {"type": "test"},
        )

        assert dead not in manager._connections
        assert dead not in manager._channels.get("event:cleanup", set())
        assert alive in manager._channels["event:cleanup"]

    @pytest.mark.asyncio
    async def test_cleans_up_empty_channel_after_dead_removal(
        self,
    ) -> None:
        """Should delete channel key when all connections are dead."""
        manager = ConnectionManager()
        dead = _make_mock_websocket()
        dead.send_json.side_effect = RuntimeError("closed")

        await manager.connect_to_channel(dead, "event:doomed")

        await manager.broadcast_to_channel(
            "event:doomed",
            {"type": "test"},
        )

        assert "event:doomed" not in manager._channels


class TestChannelPublishMethods:
    """Tests for channel-scoped publish convenience methods."""

    @pytest.mark.asyncio
    async def test_publish_score_update_to_channel(self) -> None:
        """Should broadcast score_update to the correct channel."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect_to_channel(ws, "event:abc")

        topic_id = uuid.uuid4()
        await manager.publish_score_update_to_channel(
            "event:abc",
            topic_id,
            score=42,
        )

        ws.send_json.assert_awaited_once_with(
            {
                "type": "score_update",
                "topic_id": str(topic_id),
                "score": 42,
            }
        )

    @pytest.mark.asyncio
    async def test_publish_topic_censured_to_channel(self) -> None:
        """Should broadcast topic_censured to the correct channel."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect_to_channel(ws, "event:xyz")

        topic_id = uuid.uuid4()
        await manager.publish_topic_censured_to_channel(
            "event:xyz",
            topic_id,
        )

        ws.send_json.assert_awaited_once_with(
            {
                "type": "topic_censured",
                "topic_id": str(topic_id),
            }
        )

    @pytest.mark.asyncio
    async def test_publish_new_topic_to_channel(self) -> None:
        """Should broadcast new_topic to the correct channel."""
        manager = ConnectionManager()
        ws = _make_mock_websocket()
        await manager.connect_to_channel(ws, "event:new")

        topic_id = uuid.uuid4()
        created_at = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
        await manager.publish_new_topic_to_channel(
            "event:new",
            topic_id,
            "Channel topic",
            0,
            created_at,
        )

        ws.send_json.assert_awaited_once_with(
            {
                "type": "new_topic",
                "topic": {
                    "id": str(topic_id),
                    "content": "Channel topic",
                    "score": 0,
                    "created_at": "2026-03-01T12:00:00+00:00",
                },
            }
        )
