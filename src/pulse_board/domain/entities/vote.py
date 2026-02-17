"""Vote entity — core business object for the Pulse Board voting system."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pulse_board.domain.exceptions import ValidationError

UPVOTE = 1
DOWNVOTE = -1
_VALID_VALUES = {UPVOTE, DOWNVOTE}


@dataclass
class Vote:
    """A vote cast by a user on a topic.

    Use the ``create`` classmethod for validated construction.
    The direct constructor skips validation so that repositories
    can reconstitute persisted entities without re-checking rules.
    """

    id: uuid.UUID
    topic_id: uuid.UUID
    fingerprint_id: str
    value: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        topic_id: uuid.UUID,
        fingerprint_id: str,
        value: int,
    ) -> "Vote":
        """Create a new Vote with validated inputs.

        Args:
            topic_id: The UUID of the topic being voted on.
            fingerprint_id: A non-empty string identifying
                the voter (browser fingerprint).
            value: The vote value, must be UPVOTE (+1)
                or DOWNVOTE (-1).

        Returns:
            A new Vote instance with a generated id and
            timestamps.

        Raises:
            ValidationError: If value is not +1/-1 or
                fingerprint_id is empty.
        """
        cleaned_fingerprint = fingerprint_id.strip()
        cls._validate_fingerprint_id(cleaned_fingerprint)
        cls._validate_value(value)
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4(),
            topic_id=topic_id,
            fingerprint_id=cleaned_fingerprint,
            value=value,
            created_at=now,
            updated_at=now,
        )

    def toggle(self) -> None:
        """Flip the vote value between UPVOTE and DOWNVOTE.

        Toggles +1 to -1 or -1 to +1 and updates the
        ``updated_at`` timestamp.
        """
        self.value = DOWNVOTE if self.value == UPVOTE else UPVOTE
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate_value(value: int) -> None:
        """Validate that the vote value is +1 or -1.

        Args:
            value: The vote value to validate.

        Raises:
            ValidationError: If value is not UPVOTE or
                DOWNVOTE.
        """
        if value not in _VALID_VALUES:
            raise ValidationError(
                f"Vote value must be {UPVOTE} or {DOWNVOTE} (got {value})"
            )

    @staticmethod
    def _validate_fingerprint_id(fingerprint_id: str) -> None:
        """Validate that the fingerprint ID is non-empty.

        Args:
            fingerprint_id: Pre-stripped fingerprint string.

        Raises:
            ValidationError: If fingerprint_id is empty.
        """
        if not fingerprint_id:
            raise ValidationError("Fingerprint ID cannot be empty")
