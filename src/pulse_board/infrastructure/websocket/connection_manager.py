"""WebSocket connection manager implementing EventPublisher."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from starlette.websockets import WebSocket

from pulse_board.domain.ports.event_publisher_port import (
    EventPublisher,
)

logger = logging.getLogger(__name__)


class ConnectionManager(EventPublisher):
    """Manages WebSocket connections and broadcasts domain events.

    Implements the ``EventPublisher`` port by serialising domain
    events to JSON and sending them to every active WebSocket
    client.  Dead connections are detected on send failure and
    removed automatically.

    Thread safety is guaranteed through an ``asyncio.Lock`` that
    protects the mutable connection set.
    """

    def __init__(
        self,
        max_connections: int = 1000,
        max_connections_per_ip: int = 10,
    ) -> None:
        self._connections: set[WebSocket] = set()
        self._channels: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._max_connections = max_connections
        self._max_connections_per_ip = max_connections_per_ip

    def _count_connections_for_ip(self, ip: str) -> int:
        """Count active connections from a given IP address."""
        count = 0
        for ws in self._connections:
            client = ws.client
            if client and client.host == ip:
                count += 1
        return count

    async def _accept_connection(
        self,
        websocket: WebSocket,
    ) -> bool:
        """Check limits, accept WebSocket, and register globally.

        Returns True if the connection was accepted, False if rejected.
        Must be called while holding ``self._lock``.
        """
        if len(self._connections) >= self._max_connections:
            logger.warning(
                "Max connections (%d) reached, rejecting",
                self._max_connections,
            )
            await websocket.close(code=1013)
            return False

        client_ip = websocket.client.host if websocket.client else "unknown"
        if (
            client_ip != "unknown"
            and self._count_connections_for_ip(client_ip)
            >= self._max_connections_per_ip
        ):
            logger.warning(
                "Per-IP limit (%d) reached for %s, rejecting",
                self._max_connections_per_ip,
                client_ip,
            )
            await websocket.close(code=1013)
            return False

        await websocket.accept()
        self._connections.add(websocket)
        return True

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket and register, enforcing limits.

        Rejects the connection with close code 1013 (Try Again
        Later) when the global or per-IP limit is reached.  Limits
        are checked *before* the handshake is accepted to avoid
        wasting resources.
        """
        async with self._lock:
            accepted = await self._accept_connection(websocket)
        if accepted:
            logger.info(
                "WebSocket connected. Active connections: %d",
                len(self._connections),
            )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from the active connection set."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(
            "WebSocket disconnected. Active connections: %d",
            len(self._connections),
        )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every active connection.

        Dead connections are logged and removed from the active set.
        """
        async with self._lock:
            connections = set(self._connections)

        logger.info(
            "Broadcasting message type=%s to %d connections",
            message.get("type", "unknown"),
            len(connections),
        )

        dead: set[WebSocket] = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("Failed to send to client, removing connection")
                dead.add(ws)

        if dead:
            async with self._lock:
                self._connections -= dead

    # ------------------------------------------------------------------
    # Message builders
    # ------------------------------------------------------------------

    @staticmethod
    def _score_update_message(
        topic_id: uuid.UUID,
        score: int,
    ) -> dict[str, Any]:
        return {
            "type": "score_update",
            "topic_id": str(topic_id),
            "score": score,
        }

    @staticmethod
    def _topic_censured_message(
        topic_id: uuid.UUID,
    ) -> dict[str, Any]:
        return {
            "type": "topic_censured",
            "topic_id": str(topic_id),
        }

    @staticmethod
    def _new_topic_message(
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> dict[str, Any]:
        return {
            "type": "new_topic",
            "topic": {
                "id": str(topic_id),
                "content": content,
                "score": score,
                "created_at": created_at.isoformat(),
            },
        }

    # ------------------------------------------------------------------
    # Global publish methods
    # ------------------------------------------------------------------

    async def publish_score_update(
        self,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        """Broadcast a score change for a topic."""
        await self.broadcast(
            self._score_update_message(topic_id, score),
        )

    async def publish_topic_censured(
        self,
        topic_id: uuid.UUID,
    ) -> None:
        """Broadcast that a topic has been censured."""
        await self.broadcast(
            self._topic_censured_message(topic_id),
        )

    async def publish_new_topic(
        self,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        """Broadcast a newly created topic."""
        await self.broadcast(
            self._new_topic_message(topic_id, content, score, created_at),
        )

    # ------------------------------------------------------------------
    # Channel-based connection management
    # ------------------------------------------------------------------

    async def connect_to_channel(
        self,
        websocket: WebSocket,
        channel: str,
    ) -> None:
        """Accept a WebSocket and register it to a named channel.

        Enforces the same global and per-IP connection limits as
        the regular ``connect`` method.  Rejects with close code
        1013 when a limit is reached.
        """
        async with self._lock:
            accepted = await self._accept_connection(websocket)
            if accepted:
                if channel not in self._channels:
                    self._channels[channel] = set()
                self._channels[channel].add(websocket)

        if accepted:
            logger.info(
                "WebSocket connected to channel %s. Active: %d",
                channel,
                len(self._connections),
            )

    async def disconnect_from_channel(
        self,
        websocket: WebSocket,
        channel: str,
    ) -> None:
        """Remove a WebSocket from both the channel and global set."""
        async with self._lock:
            self._connections.discard(websocket)
            if channel in self._channels:
                self._channels[channel].discard(websocket)
                if not self._channels[channel]:
                    del self._channels[channel]

        logger.info(
            "WebSocket disconnected from channel %s. Active: %d",
            channel,
            len(self._connections),
        )

    async def broadcast_to_channel(
        self,
        channel: str,
        message: dict[str, Any],
    ) -> None:
        """Send a JSON message to all connections in a channel.

        Dead connections are detected on send failure and removed
        from both the channel and global connection set.
        """
        async with self._lock:
            connections = set(self._channels.get(channel, set()))

        if not connections:
            return

        logger.info(
            "Broadcasting type=%s to channel %s (%d clients)",
            message.get("type", "unknown"),
            channel,
            len(connections),
        )

        dead: set[WebSocket] = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("Failed to send to channel client, removing")
                dead.add(ws)

        if dead:
            async with self._lock:
                self._connections -= dead
                if channel in self._channels:
                    self._channels[channel] -= dead
                    if not self._channels[channel]:
                        del self._channels[channel]

    async def publish_score_update_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        """Broadcast a score update to a specific channel."""
        await self.broadcast_to_channel(
            channel,
            self._score_update_message(topic_id, score),
        )

    async def publish_topic_censured_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
    ) -> None:
        """Broadcast a topic censure to a specific channel."""
        await self.broadcast_to_channel(
            channel,
            self._topic_censured_message(topic_id),
        )

    async def publish_new_topic_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        """Broadcast a new topic creation to a specific channel."""
        await self.broadcast_to_channel(
            channel,
            self._new_topic_message(topic_id, content, score, created_at),
        )
