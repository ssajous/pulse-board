"""Port interface for Topic persistence operations."""

import uuid
from abc import ABC, abstractmethod

from pulse_board.domain.entities.topic import Topic


class TopicRepository(ABC):
    """Abstract repository for Topic entity persistence.

    Implementations live in the infrastructure layer and
    provide concrete storage (e.g. PostgreSQL, in-memory).
    """

    @abstractmethod
    def create(self, topic: Topic) -> Topic:
        """Persist a new topic.

        Args:
            topic: The Topic entity to store.

        Returns:
            The persisted Topic (may include DB-generated fields).
        """
        ...

    @abstractmethod
    def list_active(self) -> list[Topic]:
        """Return all active topics ordered by relevance.

        Returns:
            A list of active Topic entities.
        """
        ...

    @abstractmethod
    def get_by_id(self, id: uuid.UUID) -> Topic | None:
        """Look up a topic by its unique identifier.

        Args:
            id: The UUID of the topic.

        Returns:
            The matching Topic, or None if not found.
        """
        ...

    @abstractmethod
    def delete(self, id: uuid.UUID) -> None:
        """Remove a topic by its unique identifier.

        Args:
            id: The UUID of the topic to delete.
        """
        ...

    @abstractmethod
    def list_by_event(self, event_id: uuid.UUID) -> list[Topic]:
        """Return active topics belonging to a specific event.

        Args:
            event_id: The UUID of the parent event.

        Returns:
            A list of Topic entities for the given event
            whose score is above the censure threshold.
        """
        ...

    @abstractmethod
    def update_score(self, id: uuid.UUID, delta: int) -> Topic | None:
        """Update a topic's score by a relative delta.

        Args:
            id: The UUID of the topic to update.
            delta: The score change to apply (positive or negative).

        Returns:
            The updated Topic, or None if not found.
        """
        ...
