"""Port interface for Vote persistence operations."""

import uuid
from abc import ABC, abstractmethod

from pulse_board.domain.entities.vote import Vote


class VoteRepository(ABC):
    """Abstract repository for Vote entity persistence.

    Implementations live in the infrastructure layer and
    provide concrete storage (e.g. PostgreSQL, in-memory).
    """

    @abstractmethod
    def save(self, vote: Vote) -> Vote:
        """Persist a new or updated vote.

        Args:
            vote: The Vote entity to store.

        Returns:
            The persisted Vote (may include DB-generated fields).
        """
        ...

    @abstractmethod
    def find_by_topic_and_fingerprint(
        self,
        topic_id: uuid.UUID,
        fingerprint_id: str,
    ) -> Vote | None:
        """Look up an existing vote by topic and fingerprint.

        Args:
            topic_id: The UUID of the topic.
            fingerprint_id: The voter's browser fingerprint.

        Returns:
            The matching Vote, or None if not found.
        """
        ...

    @abstractmethod
    def delete(self, vote_id: uuid.UUID) -> None:
        """Remove a vote by its unique identifier.

        Args:
            vote_id: The UUID of the vote to delete.
        """
        ...

    @abstractmethod
    def count_by_topic(self, topic_id: uuid.UUID) -> int:
        """Count total votes for a topic.

        Args:
            topic_id: The UUID of the topic.

        Returns:
            The number of votes cast for the topic.
        """
        ...
