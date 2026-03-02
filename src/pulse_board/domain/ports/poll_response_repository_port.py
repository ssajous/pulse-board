"""Port interface for PollResponse persistence operations."""

import uuid
from abc import ABC, abstractmethod

from pulse_board.domain.entities.poll_response import PollResponse


class PollResponseRepository(ABC):
    """Abstract repository for PollResponse entity persistence.

    Implementations live in the infrastructure layer and
    provide concrete storage (e.g. PostgreSQL, in-memory).
    """

    @abstractmethod
    def create(
        self,
        poll_response: PollResponse,
    ) -> PollResponse:
        """Persist a new poll response.

        Args:
            poll_response: The PollResponse entity to store.

        Returns:
            The persisted PollResponse (may include
            DB-generated fields).
        """
        ...

    @abstractmethod
    def list_by_poll(
        self,
        poll_id: uuid.UUID,
    ) -> list[PollResponse]:
        """Return all responses for a given poll.

        Args:
            poll_id: The UUID of the poll.

        Returns:
            A list of PollResponse entities for the poll
            ordered by creation date.
        """
        ...
