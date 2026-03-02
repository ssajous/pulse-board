"""Tests for the Event domain entity."""

import uuid
from datetime import UTC, datetime

import pytest

from pulse_board.domain.entities.event import (
    MAX_TITLE_LENGTH,
    Event,
    EventStatus,
)
from pulse_board.domain.exceptions import ValidationError


class TestEventCreate:
    """Tests for Event.create factory method."""

    def test_create_returns_event_with_generated_id(self) -> None:
        """Should generate a UUID id on creation."""
        event = Event.create(title="My Event", code="123456")

        assert isinstance(event.id, uuid.UUID)

    def test_create_sets_title(self) -> None:
        """Should store the event title."""
        event = Event.create(title="My Event", code="123456")

        assert event.title == "My Event"

    def test_create_sets_code(self) -> None:
        """Should store the join code."""
        event = Event.create(title="My Event", code="654321")

        assert event.code == "654321"

    def test_create_defaults_description_to_none(self) -> None:
        """Should default description to None when not provided."""
        event = Event.create(title="My Event", code="123456")

        assert event.description is None

    def test_create_stores_description(self) -> None:
        """Should store a provided description."""
        event = Event.create(
            title="My Event",
            code="123456",
            description="A great event",
        )

        assert event.description == "A great event"

    def test_create_defaults_dates_to_none(self) -> None:
        """Should default start_date and end_date to None."""
        event = Event.create(title="My Event", code="123456")

        assert event.start_date is None
        assert event.end_date is None

    def test_create_stores_dates(self) -> None:
        """Should store provided start and end dates."""
        start = datetime(2026, 6, 1, 9, 0, 0, tzinfo=UTC)
        end = datetime(2026, 6, 1, 17, 0, 0, tzinfo=UTC)
        event = Event.create(
            title="Conference",
            code="123456",
            start_date=start,
            end_date=end,
        )

        assert event.start_date == start
        assert event.end_date == end

    def test_create_defaults_status_to_active(self) -> None:
        """New events should start with ACTIVE status."""
        event = Event.create(title="My Event", code="123456")

        assert event.status == EventStatus.ACTIVE

    def test_create_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        event = Event.create(title="My Event", code="123456")
        after = datetime.now(UTC)

        assert before <= event.created_at <= after

    def test_create_generates_unique_ids(self) -> None:
        """Each call to create should produce a different id."""
        event1 = Event.create(title="Event", code="111111")
        event2 = Event.create(title="Event", code="222222")

        assert event1.id != event2.id

    def test_create_strips_whitespace_from_title(self) -> None:
        """Should strip leading/trailing whitespace from the title."""
        event = Event.create(title="  Padded Title  ", code="123456")

        assert event.title == "Padded Title"

    def test_create_strips_whitespace_from_description(self) -> None:
        """Should strip whitespace from description when provided."""
        event = Event.create(
            title="Event",
            code="123456",
            description="  spaced  ",
        )

        assert event.description == "spaced"


class TestEventTitleValidation:
    """Tests for title validation rules."""

    def test_empty_title_raises_validation_error(self) -> None:
        """Should reject empty string titles."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            Event.create(title="", code="123456")

    def test_whitespace_only_title_raises_validation_error(self) -> None:
        """Should reject titles that are only whitespace (empty after strip)."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            Event.create(title="   ", code="123456")

    def test_title_at_max_length_succeeds(self) -> None:
        """Should accept a title exactly at the max length."""
        title = "A" * MAX_TITLE_LENGTH
        event = Event.create(title=title, code="123456")

        assert len(event.title) == MAX_TITLE_LENGTH

    def test_title_exceeding_max_length_raises_validation_error(self) -> None:
        """Should reject titles longer than MAX_TITLE_LENGTH."""
        title = "A" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(
            ValidationError,
            match=f"{MAX_TITLE_LENGTH} characters or fewer",
        ):
            Event.create(title=title, code="123456")

    def test_title_one_char_succeeds(self) -> None:
        """Should accept a single-character title."""
        event = Event.create(title="X", code="123456")

        assert event.title == "X"


class TestEventSpecialCharacters:
    """Tests that special characters are preserved as-is."""

    def test_title_preserves_special_characters(self) -> None:
        """Should store special characters verbatim."""
        event = Event.create(
            title="<script>alert('xss')</script>",
            code="123456",
        )

        assert event.title == "<script>alert('xss')</script>"

    def test_title_preserves_ampersand(self) -> None:
        """Should store ampersands verbatim."""
        event = Event.create(title="Q&A Session", code="123456")

        assert event.title == "Q&A Session"

    def test_title_preserves_quotes(self) -> None:
        """Should store quotes verbatim."""
        event = Event.create(title='Say "hello"', code="123456")

        assert event.title == 'Say "hello"'

    def test_description_preserves_special_characters(self) -> None:
        """Should store description special characters verbatim."""
        event = Event.create(
            title="Safe Event",
            code="123456",
            description='It\'s <b>bold</b> & "cool"',
        )

        assert event.description == 'It\'s <b>bold</b> & "cool"'

    def test_description_none_remains_none(self) -> None:
        """Should leave None descriptions as None."""
        event = Event.create(title="Event", code="123456")

        assert event.description is None


class TestEventStatus:
    """Tests for EventStatus enum."""

    def test_active_value(self) -> None:
        """ACTIVE should have string value 'active'."""
        assert EventStatus.ACTIVE == "active"
        assert EventStatus.ACTIVE.value == "active"

    def test_closed_value(self) -> None:
        """CLOSED should have string value 'closed'."""
        assert EventStatus.CLOSED == "closed"
        assert EventStatus.CLOSED.value == "closed"


class TestEventDirectConstruction:
    """Tests for direct dataclass construction (repository reconstitution)."""

    def test_direct_construction_preserves_all_fields(self) -> None:
        """Should allow direct construction without validation."""
        event_id = uuid.uuid4()
        created_at = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)

        event = Event(
            id=event_id,
            title="Reconstituted",
            code="999999",
            description="Desc",
            start_date=None,
            end_date=None,
            status=EventStatus.CLOSED,
            created_at=created_at,
        )

        assert event.id == event_id
        assert event.title == "Reconstituted"
        assert event.code == "999999"
        assert event.description == "Desc"
        assert event.status == EventStatus.CLOSED
        assert event.created_at == created_at
