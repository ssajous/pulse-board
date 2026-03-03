"""Tests for the check event creator use case."""

import uuid

import pytest

from pulse_board.application.use_cases.check_event_creator import (
    CheckEventCreatorResult,
    CheckEventCreatorUseCase,
)
from pulse_board.domain.entities.event import Event
from pulse_board.domain.exceptions import EventNotFoundError
from tests.unit.pulse_board.fakes import FakeEventRepository


class TestCheckEventCreatorUseCase:
    """Tests for CheckEventCreatorUseCase.execute."""

    def test_matching_fingerprint_returns_true(self) -> None:
        """Should return is_creator=True when creator_token matches."""
        repo = FakeEventRepository()
        event = Event.create(title="Test", code="123456")
        repo.create(event)

        use_case = CheckEventCreatorUseCase(event_repository=repo)
        result = use_case.execute(event.id, event.creator_token)  # type: ignore[arg-type]

        assert isinstance(result, CheckEventCreatorResult)
        assert result.is_creator is True

    def test_mismatched_fingerprint_returns_false(self) -> None:
        """Should return is_creator=False when creator_token does not match."""
        repo = FakeEventRepository()
        event = Event.create(title="Test", code="123456")
        repo.create(event)

        use_case = CheckEventCreatorUseCase(event_repository=repo)
        result = use_case.execute(event.id, "wrong-token")

        assert result.is_creator is False

    def test_null_creator_token_returns_false(self) -> None:
        """Should return is_creator=False when event has no creator token."""
        import dataclasses

        repo = FakeEventRepository()
        # Construct directly to force creator_token=None (bypassing create())
        base = Event.create(title="Test", code="123456")
        event = dataclasses.replace(base, creator_token=None)
        repo.create(event)

        use_case = CheckEventCreatorUseCase(event_repository=repo)
        result = use_case.execute(event.id, "any_token")

        assert result.is_creator is False

    def test_event_not_found_raises_error(self) -> None:
        """Should raise EventNotFoundError for nonexistent event."""
        repo = FakeEventRepository()
        use_case = CheckEventCreatorUseCase(event_repository=repo)

        with pytest.raises(EventNotFoundError):
            use_case.execute(uuid.uuid4(), "some_token")
