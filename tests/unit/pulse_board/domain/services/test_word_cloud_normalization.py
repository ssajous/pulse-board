"""Tests for the normalize_word_cloud_text domain service function."""

from pulse_board.domain.services.word_cloud_normalization import (
    normalize_word_cloud_text,
)


class TestNormalizeWordCloudText:
    """Tests for normalize_word_cloud_text."""

    def test_strips_leading_whitespace(self) -> None:
        """Should remove leading whitespace from the raw string."""
        result = normalize_word_cloud_text("   hello")

        assert result == "hello"

    def test_strips_trailing_whitespace(self) -> None:
        """Should remove trailing whitespace from the raw string."""
        result = normalize_word_cloud_text("hello   ")

        assert result == "hello"

    def test_strips_leading_and_trailing_whitespace(self) -> None:
        """Should remove both leading and trailing whitespace."""
        result = normalize_word_cloud_text("  hello  ")

        assert result == "hello"

    def test_lowercases_text(self) -> None:
        """Should convert all characters to lowercase."""
        result = normalize_word_cloud_text("HELLO")

        assert result == "hello"

    def test_lowercases_mixed_case(self) -> None:
        """Should lowercase mixed-case input."""
        result = normalize_word_cloud_text("HeLLo WoRLd")

        assert result == "hello world"

    def test_collapses_internal_whitespace_to_single_space(self) -> None:
        """Should replace multiple spaces between words with a single space."""
        result = normalize_word_cloud_text("hello   world")

        assert result == "hello world"

    def test_empty_string_returns_empty_string(self) -> None:
        """Should return an empty string for empty input."""
        result = normalize_word_cloud_text("")

        assert result == ""

    def test_whitespace_only_returns_empty_string(self) -> None:
        """Should return an empty string for whitespace-only input."""
        result = normalize_word_cloud_text("   ")

        assert result == ""

    def test_handles_tabs(self) -> None:
        """Should treat tabs as whitespace and collapse them."""
        result = normalize_word_cloud_text("hello\tworld")

        assert result == "hello world"

    def test_handles_newlines(self) -> None:
        """Should treat newlines as whitespace and collapse them."""
        result = normalize_word_cloud_text("hello\nworld")

        assert result == "hello world"

    def test_handles_mixed_whitespace_types(self) -> None:
        """Should collapse mixed internal whitespace (spaces, tabs, newlines)."""
        result = normalize_word_cloud_text("hello \t \n world")

        assert result == "hello world"

    def test_complex_normalization(self) -> None:
        """Should strip, lowercase, and collapse internal whitespace together."""
        result = normalize_word_cloud_text("  MACHINE   Learning  ")

        assert result == "machine learning"

    def test_single_word_unchanged_aside_from_case(self) -> None:
        """Single word input should only be lowercased."""
        result = normalize_word_cloud_text("Python")

        assert result == "python"

    def test_already_normalized_string_is_unchanged(self) -> None:
        """String already in normalized form should pass through unchanged."""
        result = normalize_word_cloud_text("machine learning")

        assert result == "machine learning"
