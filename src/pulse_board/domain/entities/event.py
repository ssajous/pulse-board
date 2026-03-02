"""Event entity — core business object for live event sessions."""

import enum
import html
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

    @classmethod
    def create(
        cls,
        title: str,
        code: str,
        *,
        description: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> "Event":
        """Create a new Event with validated fields.

        Args:
            title: The event title (max 200 characters).
            code: The unique join code for participants.
            description: Optional event description.
            start_date: Optional scheduled start time.
            end_date: Optional scheduled end time.

        Returns:
            A new Event instance with a generated id and
            timestamp.

        Raises:
            ValidationError: If the title is empty or exceeds
                the maximum allowed length.
        """
        cleaned_title = title.strip()
        cls._validate_title(cleaned_title)
        sanitized_title = cls._sanitize_html(cleaned_title)
        sanitized_desc: str | None = None
        if description is not None:
            sanitized_desc = cls._sanitize_html(description.strip())
        return cls(
            id=uuid.uuid4(),
            title=sanitized_title,
            code=code,
            description=sanitized_desc,
            start_date=start_date,
            end_date=end_date,
            status=EventStatus.ACTIVE,
            created_at=datetime.now(UTC),
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

    @staticmethod
    def _sanitize_html(text: str) -> str:
        """Escape HTML special characters to prevent XSS.

        Args:
            text: Pre-validated text string.

        Returns:
            Text with HTML special characters escaped.
        """
        return html.escape(text, quote=True)
