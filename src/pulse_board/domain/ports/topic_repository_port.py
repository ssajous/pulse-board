"""Port interface for Topic persistence operations."""

import uuid
from abc import ABC, abstractmethod

from pulse_board.domain.entities.topic import Topic, TopicStatus


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
        """Return non-archived topics belonging to a specific event.

        Args:
            event_id: The UUID of the parent event.

        Returns:
            A list of Topic entities for the given event
            whose score is above the censure threshold and are
            not archived.
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

    @abstractmethod
    def update_status(self, id: uuid.UUID, status: TopicStatus) -> Topic | None:
        """Update the lifecycle status of a topic.

        Args:
            id: The UUID of the topic to update.
            status: The new TopicStatus value.

        Returns:
            The updated Topic, or None if not found.
        """
        ...

    @abstractmethod
    def count_by_event(self, event_id: uuid.UUID) -> int:
        """Count all topics belonging to a specific event.

        Args:
            event_id: The UUID of the parent event.

        Returns:
            Total number of topics for the event.
        """
        ...

    @abstractmethod
    def count_by_event_and_status(
        self, event_id: uuid.UUID, status: TopicStatus
    ) -> int:
        """Count topics for an event filtered by status.

        Args:
            event_id: The UUID of the parent event.
            status: The TopicStatus to filter by.

        Returns:
            Number of topics matching the event and status.
        """
        ...

    @abstractmethod
    def list_all_by_event(self, event_id: uuid.UUID) -> list[Topic]:
        """Return all topics for an event regardless of status.

        Args:
            event_id: The UUID of the parent event.

        Returns:
            A list of all Topic entities for the given event.
        """
        ...
