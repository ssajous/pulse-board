"""PollResponse entity — represents a participant's response to a poll."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class PollResponse:
    """A single response submitted by a participant for a poll.

    Use the ``create`` classmethod for validated construction.
    The direct constructor skips validation so that repositories
    can reconstitute persisted entities without re-checking rules.
    """

    id: uuid.UUID
    poll_id: uuid.UUID
    fingerprint_id: str
    response_data: dict[str, str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        poll_id: uuid.UUID,
        fingerprint_id: str,
        response_data: dict[str, str] | None = None,
    ) -> "PollResponse":
        """Create a new PollResponse with default values.

        Args:
            poll_id: The UUID of the poll being answered.
            fingerprint_id: Identifier for the respondent.
            response_data: Optional response payload.

        Returns:
            A new PollResponse instance with a generated id
            and timestamp.
        """
        return cls(
            id=uuid.uuid4(),
            poll_id=poll_id,
            fingerprint_id=fingerprint_id,
            response_data=(response_data if response_data is not None else {}),
            created_at=datetime.now(UTC),
        )
