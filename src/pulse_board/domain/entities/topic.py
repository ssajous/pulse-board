"""Topic entity — core business object for the Pulse Board."""

import html
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pulse_board.domain.exceptions import ValidationError

MAX_CONTENT_LENGTH = 255


@dataclass
class Topic:
    """A discussion topic submitted by a community member.

    Use the ``create`` classmethod for validated construction.
    The direct constructor skips validation so that repositories
    can reconstitute persisted entities without re-checking rules.
    """

    id: uuid.UUID
    content: str
    score: int
    created_at: datetime
    event_id: uuid.UUID | None = None

    @classmethod
    def create(
        cls,
        content: str,
        *,
        event_id: uuid.UUID | None = None,
    ) -> "Topic":
        """Create a new Topic with validated content.

        Args:
            content: The topic text (max 255 characters).
            event_id: Optional UUID of the parent event.

        Returns:
            A new Topic instance with a generated id and timestamp.

        Raises:
            ValidationError: If content is empty or exceeds the
                maximum allowed length.
        """
        cleaned = content.strip()
        cls._validate_content(cleaned)
        sanitized = cls._sanitize_html(cleaned)
        return cls(
            id=uuid.uuid4(),
            content=sanitized,
            score=0,
            created_at=datetime.now(UTC),
            event_id=event_id,
        )

    @staticmethod
    def _validate_content(content: str) -> None:
        """Validate topic content against domain rules.

        Args:
            content: Pre-stripped content string.

        Raises:
            ValidationError: If content is empty or too long.
        """
        if not content:
            raise ValidationError("Topic content cannot be empty")
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Topic content must be {MAX_CONTENT_LENGTH} "
                f"characters or fewer (got {len(content)})"
            )

    @staticmethod
    def _sanitize_html(content: str) -> str:
        """Escape HTML special characters to prevent XSS.

        Args:
            content: Pre-validated content string.

        Returns:
            Content with HTML special characters escaped.
        """
        return html.escape(content, quote=True)
