"""Event entity — core business object for live event sessions."""

import enum
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pulse_board.domain.exceptions import ValidationError

MAX_TITLE_LENGTH = 200


class EventStatus(enum.StrEnum):
    """Lifecycle status of a live event session."""

    ACTIVE = "active"
    CLOSED = "closed"


@dataclass
class Event:
    """A live event session that participants can join.

    Use the ``create`` classmethod for validated construction.
    The direct constructor skips validation so that repositories
    can reconstitute persisted entities without re-checking rules.
    """

    id: uuid.UUID
    title: str
    code: str
    description: str | None
    start_date: datetime | None
    end_date: datetime | None
    status: EventStatus
    created_at: datetime
    creator_fingerprint: str | None
    creator_token: str | None

    @classmethod
    def create(
        cls,
        title: str,
        code: str,
        *,
        description: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        creator_fingerprint: str | None = None,
    ) -> "Event":
        """Create a new Event with validated fields.

        Args:
            title: The event title (max 200 characters).
            code: The unique join code for participants.
            description: Optional event description.
            start_date: Optional scheduled start time.
            end_date: Optional scheduled end time.
            creator_fingerprint: Optional browser fingerprint
                of the event creator for vote deduplication.

        Returns:
            A new Event instance with a generated id, timestamp,
            and server-issued creator token.

        Raises:
            ValidationError: If the title is empty or exceeds
                the maximum allowed length.
        """
        cleaned_title = title.strip()
        cls._validate_title(cleaned_title)
        cleaned_desc: str | None = None
        if description is not None:
            cleaned_desc = description.strip()
        return cls(
            id=uuid.uuid4(),
            title=cleaned_title,
            code=code,
            description=cleaned_desc,
            start_date=start_date,
            end_date=end_date,
            status=EventStatus.ACTIVE,
            created_at=datetime.now(UTC),
            creator_fingerprint=creator_fingerprint,
            creator_token=str(uuid.uuid4()),
        )

    @staticmethod
    def _validate_title(title: str) -> None:
        """Validate event title against domain rules.

        Args:
            title: Pre-stripped title string.

        Raises:
            ValidationError: If title is empty or too long.
        """
        if not title:
            raise ValidationError("Event title cannot be empty")
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Event title must be {MAX_TITLE_LENGTH} "
                f"characters or fewer (got {len(title)})"
            )
