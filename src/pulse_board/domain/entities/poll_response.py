"""PollResponse entity — represents a participant's response to a poll."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pulse_board.domain.exceptions import ValidationError

MIN_RATING = 1
MAX_RATING = 5
MIN_TEXT_LENGTH = 1
MAX_TEXT_LENGTH = 500


@dataclass
class PollResponse:
    """A single response submitted by a participant for a poll.

    Use the ``create``, ``create_rating``, or ``create_open_text``
    classmethods for validated construction.  The direct constructor
    skips validation so that repositories can reconstitute persisted
    entities without re-checking rules.
    """

    id: uuid.UUID
    poll_id: uuid.UUID
    fingerprint_id: str
    option_id: uuid.UUID | None
    response_data: dict[str, object]
    created_at: datetime

    @classmethod
    def create(
        cls,
        poll_id: uuid.UUID,
        fingerprint_id: str,
        option_id: uuid.UUID,
    ) -> "PollResponse":
        """Create a new multiple-choice PollResponse.

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

    @classmethod
    def create_rating(
        cls,
        poll_id: uuid.UUID,
        fingerprint_id: str,
        rating: int,
    ) -> "PollResponse":
        """Create a new rating PollResponse.

        Args:
            poll_id: The UUID of the poll being answered.
            fingerprint_id: Identifier for the respondent.
            rating: Integer rating value (1-5 inclusive).

        Returns:
            A new PollResponse with option_id=None and
            response_data containing the rating.

        Raises:
            ValidationError: If rating is outside the 1-5 range.
        """
        if not (MIN_RATING <= rating <= MAX_RATING):
            raise ValidationError(
                f"Rating must be between {MIN_RATING} and {MAX_RATING} (got {rating})"
            )
        return cls(
            id=uuid.uuid4(),
            poll_id=poll_id,
            fingerprint_id=fingerprint_id,
            option_id=None,
            response_data={"rating": rating},
            created_at=datetime.now(UTC),
        )

    @classmethod
    def create_open_text(
        cls,
        poll_id: uuid.UUID,
        fingerprint_id: str,
        text: str,
    ) -> "PollResponse":
        """Create a new open-text PollResponse.

        Args:
            poll_id: The UUID of the poll being answered.
            fingerprint_id: Identifier for the respondent.
            text: The free-form text response (1-500 chars after strip).

        Returns:
            A new PollResponse with option_id=None and
            response_data containing the stripped text.

        Raises:
            ValidationError: If text is empty or exceeds 500 characters.
        """
        stripped = text.strip()
        if len(stripped) < MIN_TEXT_LENGTH:
            raise ValidationError("Response text cannot be empty")
        if len(stripped) > MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Response text must be {MAX_TEXT_LENGTH} characters or fewer "
                f"(got {len(stripped)})"
            )
        return cls(
            id=uuid.uuid4(),
            poll_id=poll_id,
            fingerprint_id=fingerprint_id,
            option_id=None,
            response_data={"text": stripped},
            created_at=datetime.now(UTC),
        )

    @property
    def selected_option_id(self) -> uuid.UUID | None:
        """Extract the selected option UUID from response_data.

        Useful for reconstituted entities where option_id may
        need to be derived from the persisted response_data.

        Returns:
            The UUID of the selected option, or None for rating/open-text
            responses.
        """
        option_id_val = self.response_data.get("option_id")
        if option_id_val is None:
            return None
        return uuid.UUID(str(option_id_val))
