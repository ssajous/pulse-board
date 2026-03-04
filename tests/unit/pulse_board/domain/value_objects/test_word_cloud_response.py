"""Tests for the WordCloudResponse value object."""

import pytest

from pulse_board.domain.exceptions import ValidationError
from pulse_board.domain.value_objects.word_cloud_response import WordCloudResponse


class TestWordCloudResponseCreate:
    """Tests for WordCloudResponse.create class method."""

    def test_valid_single_word_response(self) -> None:
        """Should accept a single-word submission."""
        result = WordCloudResponse.create("python")

        assert result.text == "python"

    def test_valid_two_word_response(self) -> None:
        """Should accept a two-word submission."""
        result = WordCloudResponse.create("machine learning")

        assert result.text == "machine learning"

    def test_valid_three_word_response(self) -> None:
        """Should accept exactly three words (maximum)."""
        result = WordCloudResponse.create("deep neural networks")

        assert result.text == "deep neural networks"

    def test_rejects_empty_string(self) -> None:
        """Should raise ValidationError for an empty string."""
        with pytest.raises(ValidationError):
            WordCloudResponse.create("")

    def test_rejects_whitespace_only_string(self) -> None:
        """Should raise ValidationError for whitespace-only input."""
        with pytest.raises(ValidationError):
            WordCloudResponse.create("   ")

    def test_rejects_text_exceeding_thirty_chars(self) -> None:
        """Should raise ValidationError for text longer than 30 characters."""
        long_text = "a" * 31

        with pytest.raises(ValidationError):
            WordCloudResponse.create(long_text)

    def test_rejects_more_than_three_words(self) -> None:
        """Should raise ValidationError when input contains more than 3 words."""
        with pytest.raises(ValidationError):
            WordCloudResponse.create("one two three four")

    def test_text_is_lowercased(self) -> None:
        """Should normalize text to lowercase."""
        result = WordCloudResponse.create("PYTHON")

        assert result.text == "python"

    def test_text_is_stripped(self) -> None:
        """Should strip leading and trailing whitespace."""
        result = WordCloudResponse.create("  hello  ")

        assert result.text == "hello"

    def test_internal_whitespace_is_collapsed(self) -> None:
        """Should collapse multiple internal spaces to a single space."""
        result = WordCloudResponse.create("hello   world")

        assert result.text == "hello world"

    def test_full_normalization_applied(self) -> None:
        """Should apply strip, lowercase, and whitespace collapse together."""
        result = WordCloudResponse.create("  MACHINE   Learning  ")

        assert result.text == "machine learning"

    def test_text_at_exactly_thirty_chars_is_accepted(self) -> None:
        """Should accept text that is exactly 30 characters after normalization."""
        # 30-char single word (exact boundary)
        text = "a" * 30
        result = WordCloudResponse.create(text)

        assert result.text == text

    def test_result_is_frozen(self) -> None:
        """WordCloudResponse should be immutable (frozen dataclass)."""
        result = WordCloudResponse.create("python")

        with pytest.raises(AttributeError):
            result.text = "changed"  # type: ignore[misc]

    def test_four_word_input_raises_validation_error(self) -> None:
        """Should raise ValidationError explicitly for four-word input."""
        with pytest.raises(ValidationError, match="3 words or fewer"):
            WordCloudResponse.create("one two three four")

    def test_empty_after_normalization_raises_validation_error(self) -> None:
        """Should raise ValidationError when normalized result is empty."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            WordCloudResponse.create("\t\n  ")
