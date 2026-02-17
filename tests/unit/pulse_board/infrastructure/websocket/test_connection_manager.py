"""Tests for the WebSocket ConnectionManager."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

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
