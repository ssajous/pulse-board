"""Tests for the Poll domain entity."""

import uuid
from datetime import UTC, datetime

import pytest

from pulse_board.domain.entities.poll import (
    MAX_QUESTION_LENGTH,
    RATING_OPTIONS,
    VALID_POLL_TYPES,
    Poll,
    PollOption,
)
from pulse_board.domain.exceptions import ValidationError


class TestPollCreate:
    """Tests for Poll.create factory method."""

    def test_create_returns_poll_with_generated_id(self) -> None:
        """Should generate a UUID id on creation."""
        event_id = uuid.uuid4()
        poll = Poll.create(
            event_id=event_id,
            question="Favorite color?",
            option_texts=["Red", "Blue"],
        )

        assert isinstance(poll.id, uuid.UUID)

    def test_create_sets_event_id(self) -> None:
        """Should store the parent event_id."""
        event_id = uuid.uuid4()
        poll = Poll.create(
            event_id=event_id,
            question="Favorite color?",
            option_texts=["Red", "Blue"],
        )

        assert poll.event_id == event_id

    def test_create_sets_question(self) -> None:
        """Should store the question text."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="What is your role?",
            option_texts=["Dev", "PM"],
        )

        assert poll.question == "What is your role?"

    def test_create_sets_poll_type_default(self) -> None:
        """Should default poll_type to multiple_choice."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=["A", "B"],
        )

        assert poll.poll_type == "multiple_choice"

    def test_create_sets_poll_type_rating(self) -> None:
        """Should accept 'rating' as a valid poll type."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=[],
            poll_type="rating",
        )

        assert poll.poll_type == "rating"

    def test_create_sets_poll_type_open_text(self) -> None:
        """Should accept 'open_text' as a valid poll type."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=[],
            poll_type="open_text",
        )

        assert poll.poll_type == "open_text"

    def test_create_generates_poll_options(self) -> None:
        """Should create PollOption objects with UUIDs."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Favorite color?",
            option_texts=["Red", "Blue", "Green"],
        )

        assert len(poll.options) == 3
        assert all(isinstance(opt, PollOption) for opt in poll.options)
        assert all(isinstance(opt.id, uuid.UUID) for opt in poll.options)
        assert [opt.text for opt in poll.options] == ["Red", "Blue", "Green"]

    def test_create_defaults_is_active_to_false(self) -> None:
        """New polls should start inactive."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=["A", "B"],
        )

        assert poll.is_active is False

    def test_create_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=["A", "B"],
        )
        after = datetime.now(UTC)

        assert before <= poll.created_at <= after

    def test_create_generates_unique_ids(self) -> None:
        """Each call to create should produce a different id."""
        event_id = uuid.uuid4()
        poll1 = Poll.create(
            event_id=event_id,
            question="Q?",
            option_texts=["A", "B"],
        )
        poll2 = Poll.create(
            event_id=event_id,
            question="Q?",
            option_texts=["A", "B"],
        )

        assert poll1.id != poll2.id

    def test_create_strips_question_whitespace(self) -> None:
        """Should strip leading/trailing whitespace from question."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="  Trimmed?  ",
            option_texts=["A", "B"],
        )

        assert poll.question == "Trimmed?"

    def test_create_strips_option_text_whitespace(self) -> None:
        """Should strip whitespace from option texts."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=["  Red  ", " Blue "],
        )

        assert [opt.text for opt in poll.options] == ["Red", "Blue"]

    def test_create_rating_poll_uses_rating_options(self) -> None:
        """Rating polls should use RATING_OPTIONS (1-5) ignoring option_texts."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="How do you rate this?",
            option_texts=["ignored"],
            poll_type="rating",
        )

        assert len(poll.options) == len(RATING_OPTIONS)
        assert [opt.text for opt in poll.options] == RATING_OPTIONS

    def test_create_open_text_poll_has_no_options(self) -> None:
        """Open text polls should have an empty options list."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Tell us your thoughts.",
            option_texts=["ignored"],
            poll_type="open_text",
        )

        assert poll.options == []


class TestPollCreateValidation:
    """Tests for Poll.create validation rules."""

    def test_empty_question_raises_validation_error(self) -> None:
        """Should raise ValidationError for empty question."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="",
                option_texts=["A", "B"],
            )

    def test_whitespace_only_question_raises_validation_error(self) -> None:
        """Should raise ValidationError for whitespace-only question."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="   ",
                option_texts=["A", "B"],
            )

    def test_too_long_question_raises_validation_error(self) -> None:
        """Should raise ValidationError for question exceeding max length."""
        long_question = "Q" * (MAX_QUESTION_LENGTH + 1)
        with pytest.raises(ValidationError, match="500 characters or fewer"):
            Poll.create(
                event_id=uuid.uuid4(),
                question=long_question,
                option_texts=["A", "B"],
            )

    def test_too_few_options_raises_validation_error(self) -> None:
        """Should raise ValidationError for fewer than 2 options."""
        with pytest.raises(ValidationError, match="at least 2 options"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="Q?",
                option_texts=["Only one"],
            )

    def test_too_many_options_raises_validation_error(self) -> None:
        """Should raise ValidationError for more than 10 options."""
        options = [f"Option {i}" for i in range(11)]
        with pytest.raises(ValidationError, match="at most 10 options"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="Q?",
                option_texts=options,
            )

    def test_empty_option_text_raises_validation_error(self) -> None:
        """Should raise ValidationError for empty option text."""
        with pytest.raises(ValidationError, match="Option 2 text cannot be empty"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="Q?",
                option_texts=["Valid", ""],
            )

    def test_whitespace_only_option_raises_validation_error(self) -> None:
        """Should raise ValidationError for whitespace-only option."""
        with pytest.raises(ValidationError, match="Option 1 text cannot be empty"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="Q?",
                option_texts=["   ", "Valid"],
            )

    def test_unknown_poll_type_raises_validation_error(self) -> None:
        """Should raise ValidationError for an entirely unknown poll type."""
        with pytest.raises(ValidationError, match="Unknown poll type 'bogus_type'"):
            Poll.create(
                event_id=uuid.uuid4(),
                question="Q?",
                option_texts=["A", "B"],
                poll_type="bogus_type",
            )

    def test_valid_poll_types_constant_contains_expected_types(self) -> None:
        """VALID_POLL_TYPES should contain the four supported types."""
        assert "multiple_choice" in VALID_POLL_TYPES
        assert "rating" in VALID_POLL_TYPES
        assert "open_text" in VALID_POLL_TYPES
        assert "word_cloud" in VALID_POLL_TYPES


class TestPollActivateDeactivate:
    """Tests for Poll.activate and Poll.deactivate methods."""

    def test_activate_returns_new_poll_with_is_active_true(self) -> None:
        """Should return a new Poll with is_active=True."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=["A", "B"],
        )
        activated = poll.activate()

        assert activated.is_active is True
        assert poll.is_active is False  # original unchanged

    def test_deactivate_returns_new_poll_with_is_active_false(self) -> None:
        """Should return a new Poll with is_active=False."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            option_texts=["A", "B"],
        )
        activated = poll.activate()
        deactivated = activated.deactivate()

        assert deactivated.is_active is False
        assert activated.is_active is True  # original unchanged


class TestPollDirectConstruction:
    """Tests for direct dataclass construction (repository reconstitution)."""

    def test_direct_construction_preserves_all_fields(self) -> None:
        """Should allow direct construction without validation."""
        poll_id = uuid.uuid4()
        event_id = uuid.uuid4()
        opt_id = uuid.uuid4()
        created_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        options = [PollOption(id=opt_id, text="Option X")]

        poll = Poll(
            id=poll_id,
            event_id=event_id,
            question="Reconstituted?",
            poll_type="rating",
            options=options,
            is_active=True,
            created_at=created_at,
        )

        assert poll.id == poll_id
        assert poll.event_id == event_id
        assert poll.question == "Reconstituted?"
        assert poll.poll_type == "rating"
        assert poll.options == options
        assert poll.is_active is True
        assert poll.created_at == created_at
