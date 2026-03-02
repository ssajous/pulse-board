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

    @abstractmethod
    def find_by_poll_and_fingerprint(
        self,
        poll_id: uuid.UUID,
        fingerprint_id: str,
    ) -> PollResponse | None:
        """Look up a response by poll and fingerprint.

        Args:
            poll_id: The UUID of the poll.
            fingerprint_id: The respondent identifier.

        Returns:
            The matching PollResponse, or None if not found.
        """
        ...

    @abstractmethod
    def count_by_option(
        self,
        poll_id: uuid.UUID,
        option_id: uuid.UUID,
    ) -> int:
        """Count responses for a specific option.

        Args:
            poll_id: The UUID of the poll.
            option_id: The UUID of the option.

        Returns:
            The number of responses selecting this option.
        """
        ...

    @abstractmethod
    def count_all_by_poll(
        self,
        poll_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        """Count responses grouped by option for a poll.

        Args:
            poll_id: The UUID of the poll.

        Returns:
            A dict mapping option_id to vote count.
        """
        ...
