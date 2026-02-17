"""Tests for domain events."""

import uuid
from datetime import UTC, datetime

import pytest

from pulse_board.domain.events import DomainEvent, TopicCensuredEvent


class TestDomainEvent:
    """Tests for the DomainEvent base class."""

    def test_occurred_at_defaults_to_now(self) -> None:
        before = datetime.now(UTC)
        event = DomainEvent()
        after = datetime.now(UTC)

        assert before <= event.occurred_at <= after

    def test_occurred_at_is_utc(self) -> None:
        event = DomainEvent()

        assert event.occurred_at.tzinfo is UTC

    def test_is_frozen(self) -> None:
        event = DomainEvent()

        with pytest.raises(AttributeError):
            event.occurred_at = datetime.now(UTC)  # type: ignore[misc]

    def test_explicit_occurred_at(self) -> None:
        timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
        event = DomainEvent(occurred_at=timestamp)

        assert event.occurred_at == timestamp


class TestTopicCensuredEvent:
    """Tests for the TopicCensuredEvent."""

    def test_create_with_required_fields(self) -> None:
        topic_id = uuid.uuid4()
        event = TopicCensuredEvent(
            topic_id=topic_id,
            final_score=-5,
        )

        assert event.topic_id == topic_id
        assert event.final_score == -5

    def test_inherits_occurred_at(self) -> None:
        before = datetime.now(UTC)
        event = TopicCensuredEvent(
            topic_id=uuid.uuid4(),
            final_score=-3,
        )
        after = datetime.now(UTC)

        assert before <= event.occurred_at <= after

    def test_is_frozen(self) -> None:
        event = TopicCensuredEvent(
            topic_id=uuid.uuid4(),
            final_score=-5,
        )

        with pytest.raises(AttributeError):
            event.final_score = 0  # type: ignore[misc]

        with pytest.raises(AttributeError):
            event.topic_id = uuid.uuid4()  # type: ignore[misc]

    def test_is_instance_of_domain_event(self) -> None:
        event = TopicCensuredEvent(
            topic_id=uuid.uuid4(),
            final_score=-5,
        )

        assert isinstance(event, DomainEvent)

    def test_explicit_occurred_at(self) -> None:
        timestamp = datetime(2025, 6, 1, 8, 30, 0, tzinfo=UTC)
        topic_id = uuid.uuid4()
        event = TopicCensuredEvent(
            topic_id=topic_id,
            final_score=-10,
            occurred_at=timestamp,
        )

        assert event.occurred_at == timestamp
        assert event.topic_id == topic_id
        assert event.final_score == -10

    def test_equality(self) -> None:
        timestamp = datetime(2025, 1, 1, tzinfo=UTC)
        topic_id = uuid.uuid4()
        event_a = TopicCensuredEvent(
            topic_id=topic_id,
            final_score=-5,
            occurred_at=timestamp,
        )
        event_b = TopicCensuredEvent(
            topic_id=topic_id,
            final_score=-5,
            occurred_at=timestamp,
        )

        assert event_a == event_b

    def test_inequality_on_different_score(self) -> None:
        timestamp = datetime(2025, 1, 1, tzinfo=UTC)
        topic_id = uuid.uuid4()
        event_a = TopicCensuredEvent(
            topic_id=topic_id,
            final_score=-5,
            occurred_at=timestamp,
        )
        event_b = TopicCensuredEvent(
            topic_id=topic_id,
            final_score=-3,
            occurred_at=timestamp,
        )

        assert event_a != event_b
