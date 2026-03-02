"""Port interface for Poll persistence operations."""

import uuid
from abc import ABC, abstractmethod

from pulse_board.domain.entities.poll import Poll


class PollRepository(ABC):
    """Abstract repository for Poll entity persistence.

    Implementations live in the infrastructure layer and
    provide concrete storage (e.g. PostgreSQL, in-memory).
    """

    @abstractmethod
    def create(self, poll: Poll) -> Poll:
        """Persist a new poll.

        Args:
            poll: The Poll entity to store.

        Returns:
            The persisted Poll (may include DB-generated
            fields).
        """
        ...

    @abstractmethod
    def get_by_id(self, id: uuid.UUID) -> Poll | None:
        """Look up a poll by its unique identifier.

        Args:
            id: The UUID of the poll.

        Returns:
            The matching Poll, or None if not found.
        """
        ...

    @abstractmethod
    def list_by_event(
        self,
        event_id: uuid.UUID,
    ) -> list[Poll]:
        """Return all polls belonging to a given event.

        Args:
            event_id: The UUID of the parent event.

        Returns:
            A list of Poll entities for the event ordered
            by creation date.
        """
        ...

    @abstractmethod
    def update_active_status(
        self,
        id: uuid.UUID,
        is_active: bool,
    ) -> Poll | None:
        """Update the active status of a poll.

        Args:
            id: The UUID of the poll to update.
            is_active: The new active status.

        Returns:
            The updated Poll, or None if not found.
        """
        ...
