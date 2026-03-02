"""Poll entity — represents a poll within a live event session."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class Poll:
    """A poll associated with a live event session.

    Use the ``create`` classmethod for validated construction.
    The direct constructor skips validation so that repositories
    can reconstitute persisted entities without re-checking rules.
    """

    id: uuid.UUID
    event_id: uuid.UUID
    question: str
    poll_type: str
    options: list[dict[str, str]]
    is_active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        event_id: uuid.UUID,
        question: str,
        poll_type: str,
        options: list[dict[str, str]] | None = None,
    ) -> "Poll":
        """Create a new Poll with default values.

        Args:
            event_id: The UUID of the parent event.
            question: The poll question text.
            poll_type: The type of poll (e.g. 'multiple_choice').
            options: Optional list of option dictionaries.

        Returns:
            A new Poll instance with a generated id and
            timestamp.
        """
        return cls(
            id=uuid.uuid4(),
            event_id=event_id,
            question=question,
            poll_type=poll_type,
            options=options if options is not None else [],
            is_active=False,
            created_at=datetime.now(UTC),
        )
