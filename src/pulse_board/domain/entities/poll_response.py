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
    option_id: uuid.UUID
    response_data: dict[str, str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        poll_id: uuid.UUID,
        fingerprint_id: str,
        option_id: uuid.UUID,
    ) -> "PollResponse":
        """Create a new PollResponse with default values.

        Args:
            poll_id: The UUID of the poll being answered.
            fingerprint_id: Identifier for the respondent.
            option_id: The UUID of the selected option.

        Returns:
            A new PollResponse instance with a generated id,
            auto-built response_data, and timestamp.
        """
        return cls(
            id=uuid.uuid4(),
            poll_id=poll_id,
            fingerprint_id=fingerprint_id,
            option_id=option_id,
            response_data={"option_id": str(option_id)},
            created_at=datetime.now(UTC),
        )

    @property
    def selected_option_id(self) -> uuid.UUID:
        """Extract the selected option UUID from response_data.

        Useful for reconstituted entities where option_id may
        need to be derived from the persisted response_data.

        Returns:
            The UUID of the selected option.
        """
        return uuid.UUID(self.response_data["option_id"])
