"""Port interface for Event persistence operations."""

import uuid
from abc import ABC, abstractmethod

from pulse_board.domain.entities.event import Event, EventStatus


class EventRepository(ABC):
    """Abstract repository for Event entity persistence.

    Implementations live in the infrastructure layer and
    provide concrete storage (e.g. PostgreSQL, in-memory).
    """

    @abstractmethod
    def create(self, event: Event) -> Event:
        """Persist a new event.

        Args:
            event: The Event entity to store.

        Returns:
            The persisted Event (may include DB-generated
            fields).
        """
        ...

    @abstractmethod
    def get_by_id(self, id: uuid.UUID) -> Event | None:
        """Look up an event by its unique identifier.

        Args:
            id: The UUID of the event.

        Returns:
            The matching Event, or None if not found.
        """
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> Event | None:
        """Look up an event by its join code.

        Args:
            code: The unique join code string.

        Returns:
            The matching Event, or None if not found.
        """
        ...

    @abstractmethod
    def list_active(self) -> list[Event]:
        """Return all events with ACTIVE status.

        Returns:
            A list of active Event entities ordered by
            creation date descending.
        """
        ...

    @abstractmethod
    def update_status(
        self,
        id: uuid.UUID,
        status: EventStatus,
    ) -> Event | None:
        """Update the status of an existing event.

        Args:
            id: The UUID of the event to update.
            status: The new EventStatus value.

        Returns:
            The updated Event, or None if not found.
        """
        ...

    @abstractmethod
    def is_code_unique(self, code: str) -> bool:
        """Check whether a join code is not yet in use.

        Args:
            code: The join code to check.

        Returns:
            True if no existing event uses this code.
        """
        ...
