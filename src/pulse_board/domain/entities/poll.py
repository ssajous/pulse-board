"""Poll entity — represents a poll within a live event session."""

import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from pulse_board.domain.exceptions import ValidationError

MAX_QUESTION_LENGTH = 500
MIN_OPTIONS = 2
MAX_OPTIONS = 10
DEFAULT_POLL_TYPE = "multiple_choice"
VALID_POLL_TYPES = {"multiple_choice", "rating", "open_text", "word_cloud"}
RATING_OPTIONS = ["1", "2", "3", "4", "5"]


@dataclass
class PollOption:
    """A single selectable option within a poll.

    Attributes:
        id: Unique identifier for this option.
        text: Display text of the option.
    """

    id: uuid.UUID
    text: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a dict with string id and text."""
        return {"id": str(self.id), "text": self.text}


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
    options: list[PollOption]
    is_active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        event_id: uuid.UUID,
        question: str,
        option_texts: list[str],
        *,
        poll_type: str = DEFAULT_POLL_TYPE,
    ) -> "Poll":
        """Create a new Poll with validated fields.

        Args:
            event_id: The UUID of the parent event.
            question: The poll question text (1-500 chars).
            option_texts: List of option display texts (2-10 for
                multiple_choice; ignored for rating and open_text).
            poll_type: The type of poll. Must be one of
                ``multiple_choice``, ``rating``, ``open_text``, or
                ``word_cloud``. Defaults to ``multiple_choice``.

        Returns:
            A new Poll instance with generated id, option UUIDs,
            and timestamp.

        Raises:
            ValidationError: If question or options fail domain
                validation rules, or poll_type is unknown.
        """
        cls._validate_poll_type(poll_type)

        cleaned_question = question.strip()
        cls._validate_question(cleaned_question)

        if poll_type == "rating":
            effective_texts = RATING_OPTIONS
        elif poll_type in ("open_text", "word_cloud"):
            effective_texts = []
        else:
            cls._validate_options(option_texts)
            effective_texts = option_texts

        options = [
            PollOption(id=uuid.uuid4(), text=text.strip()) for text in effective_texts
        ]

        return cls(
            id=uuid.uuid4(),
            event_id=event_id,
            question=cleaned_question,
            poll_type=poll_type,
            options=options,
            is_active=False,
            created_at=datetime.now(UTC),
        )

    def activate(self) -> "Poll":
        """Return a new Poll with ``is_active`` set to True."""
        return replace(self, is_active=True)

    def deactivate(self) -> "Poll":
        """Return a new Poll with ``is_active`` set to False."""
        return replace(self, is_active=False)

    @staticmethod
    def _validate_poll_type(poll_type: str) -> None:
        """Validate poll type against allowed values.

        Args:
            poll_type: The poll type string to validate.

        Raises:
            ValidationError: If poll_type is not in VALID_POLL_TYPES.
        """
        if poll_type not in VALID_POLL_TYPES:
            valid = ", ".join(sorted(VALID_POLL_TYPES))
            raise ValidationError(
                f"Unknown poll type '{poll_type}'. Must be one of: {valid}"
            )

    @staticmethod
    def _validate_question(question: str) -> None:
        """Validate poll question against domain rules.

        Args:
            question: Pre-stripped question string.

        Raises:
            ValidationError: If question is empty or too long.
        """
        if not question:
            raise ValidationError("Poll question cannot be empty")
        if len(question) > MAX_QUESTION_LENGTH:
            raise ValidationError(
                f"Poll question must be {MAX_QUESTION_LENGTH} "
                f"characters or fewer (got {len(question)})"
            )

    @staticmethod
    def _validate_options(option_texts: list[str]) -> None:
        """Validate poll options against domain rules.

        Args:
            option_texts: List of option text strings.

        Raises:
            ValidationError: If option count is out of range
                or any option text is empty.
        """
        if len(option_texts) < MIN_OPTIONS:
            raise ValidationError(
                f"Poll must have at least {MIN_OPTIONS} options "
                f"(got {len(option_texts)})"
            )
        if len(option_texts) > MAX_OPTIONS:
            raise ValidationError(
                f"Poll must have at most {MAX_OPTIONS} options "
                f"(got {len(option_texts)})"
            )
        for i, text in enumerate(option_texts):
            if not text.strip():
                raise ValidationError(f"Option {i + 1} text cannot be empty")
