"""Tests for the Poll domain entity."""

import uuid
from datetime import UTC, datetime

from pulse_board.domain.entities.poll import Poll


class TestPollCreate:
    """Tests for Poll.create factory method."""

    def test_create_returns_poll_with_generated_id(self) -> None:
        """Should generate a UUID id on creation."""
        event_id = uuid.uuid4()
        poll = Poll.create(
            event_id=event_id,
            question="Favorite color?",
            poll_type="multiple_choice",
        )

        assert isinstance(poll.id, uuid.UUID)

    def test_create_sets_event_id(self) -> None:
        """Should store the parent event_id."""
        event_id = uuid.uuid4()
        poll = Poll.create(
            event_id=event_id,
            question="Favorite color?",
            poll_type="multiple_choice",
        )

        assert poll.event_id == event_id

    def test_create_sets_question(self) -> None:
        """Should store the question text."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="What is your role?",
            poll_type="multiple_choice",
        )

        assert poll.question == "What is your role?"

    def test_create_sets_poll_type(self) -> None:
        """Should store the poll type."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            poll_type="word_cloud",
        )

        assert poll.poll_type == "word_cloud"

    def test_create_defaults_options_to_empty_list(self) -> None:
        """Should default options to an empty list when None."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            poll_type="multiple_choice",
        )

        assert poll.options == []

    def test_create_preserves_provided_options(self) -> None:
        """Should use the provided options list."""
        options = [
            {"id": "a", "text": "Red"},
            {"id": "b", "text": "Blue"},
        ]
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Favorite color?",
            poll_type="multiple_choice",
            options=options,
        )

        assert poll.options == options

    def test_create_defaults_is_active_to_false(self) -> None:
        """New polls should start inactive."""
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            poll_type="multiple_choice",
        )

        assert poll.is_active is False

    def test_create_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        poll = Poll.create(
            event_id=uuid.uuid4(),
            question="Q?",
            poll_type="multiple_choice",
        )
        after = datetime.now(UTC)

        assert before <= poll.created_at <= after

    def test_create_generates_unique_ids(self) -> None:
        """Each call to create should produce a different id."""
        event_id = uuid.uuid4()
        poll1 = Poll.create(
            event_id=event_id,
            question="Q?",
            poll_type="mc",
        )
        poll2 = Poll.create(
            event_id=event_id,
            question="Q?",
            poll_type="mc",
        )

        assert poll1.id != poll2.id


class TestPollDirectConstruction:
    """Tests for direct dataclass construction (repository reconstitution)."""

    def test_direct_construction_preserves_all_fields(self) -> None:
        """Should allow direct construction without validation."""
        poll_id = uuid.uuid4()
        event_id = uuid.uuid4()
        created_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        options = [{"id": "x", "text": "Option X"}]

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
