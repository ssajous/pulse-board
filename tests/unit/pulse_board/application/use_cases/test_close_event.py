"""Tests for CloseEventUseCase."""

import uuid

import pytest

from pulse_board.application.use_cases.close_event import CloseEventUseCase
from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.exceptions import EventNotFoundError
from tests.unit.pulse_board.fakes import FakeEventRepository


@pytest.fixture
def repo() -> FakeEventRepository:
    """Provide a fresh in-memory event repository."""
    return FakeEventRepository()


@pytest.fixture
def use_case(repo: FakeEventRepository) -> CloseEventUseCase:
    """Provide a CloseEventUseCase wired to the fake repository."""
    return CloseEventUseCase(event_repository=repo)


class TestCloseEvent:
    """Tests for CloseEventUseCase.execute."""

    def test_success(
        self,
        repo: FakeEventRepository,
        use_case: CloseEventUseCase,
    ) -> None:
        """Should close an active event and return closed status."""
        event = Event.create("Test Event", "123456")
        repo.create(event)

        result = use_case.execute(event.id)

        assert result.event_id == event.id
        assert result.status == "closed"
        updated = repo.get_by_id(event.id)
        assert updated is not None
        assert updated.status == EventStatus.CLOSED

    def test_already_closed_idempotent(
        self,
        repo: FakeEventRepository,
        use_case: CloseEventUseCase,
    ) -> None:
        """Closing an already-closed event should be idempotent."""
        event = Event.create("Test Event", "123456")
        repo.create(event)
        repo.update_status(event.id, EventStatus.CLOSED)

        result = use_case.execute(event.id)

        assert result.status == "closed"

    def test_not_found_raises(self, use_case: CloseEventUseCase) -> None:
        """Should raise EventNotFoundError when event does not exist."""
        with pytest.raises(EventNotFoundError):
            use_case.execute(uuid.uuid4())

    def test_result_is_frozen(
        self,
        repo: FakeEventRepository,
        use_case: CloseEventUseCase,
    ) -> None:
        """CloseEventResult should be immutable."""
        event = Event.create("Frozen Event", "999999")
        repo.create(event)

        result = use_case.execute(event.id)

        with pytest.raises(AttributeError):
            result.status = "active"  # type: ignore[misc]

    def test_result_contains_event_id(
        self,
        repo: FakeEventRepository,
        use_case: CloseEventUseCase,
    ) -> None:
        """Result should carry back the same event_id provided."""
        event = Event.create("ID Check Event", "777777")
        repo.create(event)

        result = use_case.execute(event.id)

        assert result.event_id == event.id

    def test_closing_persists_to_repository(
        self,
        repo: FakeEventRepository,
        use_case: CloseEventUseCase,
    ) -> None:
        """Repository should reflect the closed status after execute."""
        event = Event.create("Persist Event", "555555")
        repo.create(event)

        use_case.execute(event.id)

        persisted = repo.get_by_id(event.id)
        assert persisted is not None
        assert persisted.status == EventStatus.CLOSED

    def test_idempotent_does_not_raise_on_second_call(
        self,
        repo: FakeEventRepository,
        use_case: CloseEventUseCase,
    ) -> None:
        """Calling close twice should not raise any error."""
        event = Event.create("Double Close", "444444")
        repo.create(event)

        use_case.execute(event.id)
        result = use_case.execute(event.id)

        assert result.status == "closed"
