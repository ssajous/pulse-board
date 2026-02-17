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

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket and register, enforcing limits.

        Rejects the connection with close code 1013 (Try Again
        Later) when the global or per-IP limit is reached.  Limits
        are checked *before* the handshake is accepted to avoid
        wasting resources.
        """
        async with self._lock:
            if len(self._connections) >= self._max_connections:
                logger.warning(
                    "Max connections (%d) reached, rejecting",
                    self._max_connections,
                )
                await websocket.close(code=1013)
                return

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
                return

            await websocket.accept()
            self._connections.add(websocket)

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

    async def publish_score_update(
        self,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        """Broadcast a score change for a topic."""
        await self.broadcast(
            {
                "type": "score_update",
                "topic_id": str(topic_id),
                "score": score,
            }
        )

    async def publish_topic_censured(
        self,
        topic_id: uuid.UUID,
    ) -> None:
        """Broadcast that a topic has been censured."""
        await self.broadcast(
            {
                "type": "topic_censured",
                "topic_id": str(topic_id),
            }
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
            {
                "type": "new_topic",
                "topic": {
                    "id": str(topic_id),
                    "content": content,
                    "score": score,
                    "created_at": created_at.isoformat(),
                },
            }
        )
