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
