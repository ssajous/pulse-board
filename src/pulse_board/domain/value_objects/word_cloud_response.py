"""WordCloudResponse value object — validated word cloud submission text."""

from dataclasses import dataclass

from pulse_board.domain.exceptions import ValidationError
from pulse_board.domain.services.word_cloud_normalization import (
    normalize_word_cloud_text,
)

MAX_CHARS = 30
MAX_WORDS = 3


@dataclass(frozen=True)
class WordCloudResponse:
    """An immutable, validated word cloud response text.

    Use the ``create`` classmethod for validated construction.
    The direct constructor skips validation so that repositories
    can reconstitute persisted entities without re-checking rules.

    Attributes:
        text: Normalized (lowercased, whitespace-collapsed) response text.
    """

    text: str

    @classmethod
    def create(cls, raw_text: str) -> "WordCloudResponse":
        """Create a validated WordCloudResponse from raw participant input.

        Normalizes the text before applying domain validation rules.

        Args:
            raw_text: The raw input string from the participant.

        Returns:
            A new WordCloudResponse with normalized text.

        Raises:
            ValidationError: If the normalized text is empty, exceeds
                30 characters, or contains more than 3 words.
        """
        normalized = normalize_word_cloud_text(raw_text)

        if not normalized:
            raise ValidationError("Word cloud response cannot be empty")

        if len(normalized) > MAX_CHARS:
            raise ValidationError(
                f"Word cloud response must be {MAX_CHARS} characters or fewer "
                f"(got {len(normalized)})"
            )

        word_count = len(normalized.split())
        if word_count > MAX_WORDS:
            raise ValidationError(
                f"Word cloud response must be {MAX_WORDS} words or fewer "
                f"(got {word_count})"
            )

        return cls(text=normalized)
