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

    @abstractmethod
    async def publish_score_update_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        """Broadcast a score update to a specific channel."""
        ...

    @abstractmethod
    async def publish_topic_censured_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
    ) -> None:
        """Broadcast a topic censure to a specific channel."""
        ...

    @abstractmethod
    async def publish_new_topic_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        """Broadcast a new topic creation to a specific channel."""
        ...

    @abstractmethod
    async def publish_poll_activated_to_channel(
        self,
        channel: str,
        poll_id: uuid.UUID,
        question: str,
        options: list[dict[str, str]],
    ) -> None:
        """Broadcast a poll activation to a specific channel."""
        ...

    @abstractmethod
    async def publish_poll_deactivated_to_channel(
        self,
        channel: str,
        poll_id: uuid.UUID,
    ) -> None:
        """Broadcast a poll deactivation to a specific channel."""
        ...

    @abstractmethod
    async def publish_poll_results_updated_to_channel(
        self,
        channel: str,
        poll_id: uuid.UUID,
        poll_type: str,
        results: dict[str, object],
    ) -> None:
        """Broadcast updated poll results to a specific channel."""
        ...

    @abstractmethod
    async def publish_topic_status_changed_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        new_status: str,
    ) -> None:
        """Broadcast a topic status change to a specific channel."""
        ...

    @abstractmethod
    async def publish_event_closed_to_channel(
        self,
        channel: str,
        event_id: uuid.UUID,
    ) -> None:
        """Broadcast event closure to a specific channel."""
        ...
