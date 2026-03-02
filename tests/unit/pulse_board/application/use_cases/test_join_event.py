"""Tests for the join event use case."""

import dataclasses

import pytest

from pulse_board.application.use_cases.join_event import (
    JoinEventResult,
    JoinEventUseCase,
)
from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.exceptions import (
    EventNotActiveError,
    EventNotFoundError,
)
from tests.unit.pulse_board.fakes import FakeEventRepository


class TestJoinEventUseCase:
    """Tests for JoinEventUseCase.execute."""

    def test_join_active_event_by_code(self) -> None:
        """Should return event details when code matches an active event."""
        repo = FakeEventRepository()
        event = Event.create(title="Active Event", code="123456")
        repo.create(event)
        use_case = JoinEventUseCase(event_repository=repo)

        result = use_case.execute("123456")

        assert isinstance(result, JoinEventResult)
        assert result.id == event.id
        assert result.title == "Active Event"
        assert result.code == "123456"
        assert result.status == EventStatus.ACTIVE

    def test_returns_all_event_fields(self) -> None:
        """Should populate all fields of the result."""
        repo = FakeEventRepository()
        event = Event.create(
            title="Full Join",
            code="654321",
            description="Join me",
        )
        repo.create(event)
        use_case = JoinEventUseCase(event_repository=repo)

        result = use_case.execute("654321")

        assert result.description == "Join me"
        assert result.start_date is None
        assert result.end_date is None
        assert result.created_at == event.created_at

    def test_raises_when_code_not_found(self) -> None:
        """Should raise EventNotFoundError for unknown join code."""
        repo = FakeEventRepository()
        use_case = JoinEventUseCase(event_repository=repo)

        with pytest.raises(EventNotFoundError, match="999999"):
            use_case.execute("999999")

    def test_raises_when_event_not_active(self) -> None:
        """Should raise EventNotActiveError for closed events."""
        repo = FakeEventRepository()
        event = Event.create(title="Closed Event", code="111111")
        repo.create(event)
        # Close the event
        closed = dataclasses.replace(event, status=EventStatus.CLOSED)
        repo._events[event.id] = closed
        use_case = JoinEventUseCase(event_repository=repo)

        with pytest.raises(EventNotActiveError, match="no longer active"):
            use_case.execute("111111")

    def test_result_is_frozen(self) -> None:
        """JoinEventResult should be immutable."""
        repo = FakeEventRepository()
        event = Event.create(title="Frozen", code="222222")
        repo.create(event)
        use_case = JoinEventUseCase(event_repository=repo)

        result = use_case.execute("222222")

        with pytest.raises(AttributeError):
            result.title = "changed"  # type: ignore[misc]
