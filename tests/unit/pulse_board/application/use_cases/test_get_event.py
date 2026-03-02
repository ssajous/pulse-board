"""Tests for the get event use case."""

import uuid

import pytest

from pulse_board.application.use_cases.get_event import (
    GetEventResult,
    GetEventUseCase,
)
from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.exceptions import EventNotFoundError
from tests.unit.pulse_board.fakes import FakeEventRepository


class TestGetEventUseCase:
    """Tests for GetEventUseCase.execute."""

    def test_returns_event_when_found(self) -> None:
        """Should return event details when it exists in the repo."""
        repo = FakeEventRepository()
        event = Event.create(title="Test Event", code="123456")
        repo.create(event)
        use_case = GetEventUseCase(event_repository=repo)

        result = use_case.execute(event.id)

        assert isinstance(result, GetEventResult)
        assert result.id == event.id
        assert result.title == "Test Event"
        assert result.code == "123456"
        assert result.status == EventStatus.ACTIVE

    def test_returns_all_event_fields(self) -> None:
        """Should populate all fields of the result."""
        repo = FakeEventRepository()
        event = Event.create(
            title="Full Event",
            code="654321",
            description="Description here",
        )
        repo.create(event)
        use_case = GetEventUseCase(event_repository=repo)

        result = use_case.execute(event.id)

        assert result.description == "Description here"
        assert result.start_date is None
        assert result.end_date is None
        assert result.created_at == event.created_at

    def test_raises_when_event_not_found(self) -> None:
        """Should raise EventNotFoundError for unknown event_id."""
        repo = FakeEventRepository()
        use_case = GetEventUseCase(event_repository=repo)
        missing_id = uuid.uuid4()

        with pytest.raises(
            EventNotFoundError,
            match=str(missing_id),
        ):
            use_case.execute(missing_id)

    def test_result_is_frozen(self) -> None:
        """GetEventResult should be immutable."""
        repo = FakeEventRepository()
        event = Event.create(title="Frozen", code="111111")
        repo.create(event)
        use_case = GetEventUseCase(event_repository=repo)

        result = use_case.execute(event.id)

        with pytest.raises(AttributeError):
            result.title = "changed"  # type: ignore[misc]
