"""Port interface for publishing real-time domain events."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class EventPublisher(ABC):
    """Abstract publisher for broadcasting real-time domain events.

    Implementations live in the infrastructure layer and
    provide concrete delivery (e.g. WebSocket, SSE, message queue).
    """

    @abstractmethod
    async def publish_score_update(
        self,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        """Broadcast a score update for a topic."""
        ...

    @abstractmethod
    async def publish_topic_censured(
        self,
        topic_id: uuid.UUID,
    ) -> None:
        """Broadcast that a topic has been censured."""
        ...

    @abstractmethod
    async def publish_new_topic(
        self,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        """Broadcast a new topic creation."""
        ...
