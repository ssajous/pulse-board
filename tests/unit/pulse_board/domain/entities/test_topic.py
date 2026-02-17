"""Tests for the Topic domain entity."""

import uuid
from datetime import UTC, datetime

import pytest

from pulse_board.domain.entities.topic import MAX_CONTENT_LENGTH, Topic
from pulse_board.domain.exceptions import ValidationError


class TestTopicCreate:
    """Tests for Topic.create factory method."""

    def test_create_valid_topic(self) -> None:
        """Should create a topic with the given content."""
        topic = Topic.create("My topic")

        assert topic.content == "My topic"
        assert isinstance(topic.id, uuid.UUID)
        assert topic.score == 0
        assert isinstance(topic.created_at, datetime)

    def test_create_strips_whitespace(self) -> None:
        """Should strip leading and trailing whitespace from content."""
        topic = Topic.create("  hello  ")

        assert topic.content == "hello"

    def test_create_generates_uuid(self) -> None:
        """Should generate a UUID4 identifier."""
        topic = Topic.create("test")

        assert topic.id.version == 4

    def test_create_default_score_is_zero(self) -> None:
        """New topics should start with a score of zero."""
        topic = Topic.create("test")

        assert topic.score == 0

    def test_create_sets_created_at(self) -> None:
        """Should set created_at to approximately the current time."""
        before = datetime.now(UTC)
        topic = Topic.create("test")
        after = datetime.now(UTC)

        assert before <= topic.created_at <= after

    def test_create_empty_content_raises(self) -> None:
        """Should raise ValidationError for empty content."""
        with pytest.raises(ValidationError):
            Topic.create("")

    def test_create_whitespace_only_raises(self) -> None:
        """Should raise ValidationError for whitespace-only content."""
        with pytest.raises(ValidationError):
            Topic.create("   ")

    def test_create_exceeds_max_length_raises(self) -> None:
        """Should raise ValidationError when content exceeds max length."""
        content = "a" * (MAX_CONTENT_LENGTH + 1)

        with pytest.raises(ValidationError):
            Topic.create(content)

    def test_create_at_max_length_succeeds(self) -> None:
        """Should allow content at exactly the maximum length."""
        content = "a" * MAX_CONTENT_LENGTH
        topic = Topic.create(content)

        assert len(topic.content) == MAX_CONTENT_LENGTH

    def test_direct_constructor_skips_validation(self) -> None:
        """Direct constructor should not validate, for repository reconstitution."""
        topic = Topic(
            id=uuid.uuid4(),
            content="",
            score=0,
            created_at=datetime.now(UTC),
        )

        assert topic.content == ""

    def test_score_is_mutable(self) -> None:
        """Topic score should be mutable (not a frozen dataclass)."""
        topic = Topic.create("test")
        topic.score = 5

        assert topic.score == 5

    def test_validation_error_has_message(self) -> None:
        """ValidationError should carry a descriptive message."""
        with pytest.raises(ValidationError) as exc_info:
            Topic.create("")

        assert "empty" in exc_info.value.message.lower()


class TestTopicSanitization:
    """Tests for HTML sanitization in Topic.create."""

    def test_create_escapes_html_tags(self) -> None:
        """Script tags should be escaped to prevent XSS."""
        topic = Topic.create("<script>alert(1)</script>")
        assert "<script>" not in topic.content
        assert "&lt;script&gt;" in topic.content

    def test_create_escapes_ampersand(self) -> None:
        """Ampersands should be escaped to HTML entity."""
        topic = Topic.create("A & B")
        assert topic.content == "A &amp; B"

    def test_create_escapes_quotes(self) -> None:
        """Double quotes should be escaped to HTML entity."""
        topic = Topic.create('He said "hello"')
        assert topic.content == "He said &quot;hello&quot;"

    def test_create_escapes_single_quotes(self) -> None:
        """Single quotes should be escaped to HTML entity."""
        topic = Topic.create("It's")
        assert topic.content == "It&#x27;s"

    def test_create_validates_length_before_sanitizing(self) -> None:
        """Length validation runs on raw input, not escaped output."""
        content = "a" * (MAX_CONTENT_LENGTH - 1) + "<"
        topic = Topic.create(content)
        assert topic.content.endswith("&lt;")
        # Stored content is longer than 255 due to escaping,
        # but validation passed because it checks raw length
        assert len(topic.content) > MAX_CONTENT_LENGTH

    def test_plain_text_unchanged(self) -> None:
        """Plain text without special characters should pass through."""
        topic = Topic.create("Hello world")
        assert topic.content == "Hello world"
