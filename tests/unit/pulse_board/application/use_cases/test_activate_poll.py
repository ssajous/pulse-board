"""Tests for the activate poll use case."""

import uuid

import pytest

from pulse_board.application.use_cases.activate_poll import (
    ActivatePollResult,
    ActivatePollUseCase,
)
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.exceptions import EntityNotFoundError
from tests.unit.pulse_board.fakes import FakePollRepository


def _setup() -> tuple[ActivatePollUseCase, FakePollRepository]:
    """Create an ActivatePollUseCase with a fresh fake repository."""
    poll_repo = FakePollRepository()
    use_case = ActivatePollUseCase(poll_repository=poll_repo)
    return use_case, poll_repo


def _create_poll(
    poll_repo: FakePollRepository,
    event_id: uuid.UUID | None = None,
    *,
    is_active: bool = False,
) -> Poll:
    """Create and persist a poll with the given active status."""
    eid = event_id or uuid.uuid4()
    poll = Poll.create(
        event_id=eid,
        question="Test question?",
        option_texts=["A", "B"],
    )
    saved = poll_repo.create(poll)
    if is_active:
        poll_repo.update_active_status(saved.id, True)
        return poll_repo.get_by_id(saved.id)  # type: ignore[return-value]
    return saved


class TestActivatePollUseCase:
    """Tests for ActivatePollUseCase.execute."""

    def test_activate_inactive_poll(self) -> None:
        """Should activate an inactive poll."""
        use_case, poll_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id, activate=True)

        assert isinstance(result, ActivatePollResult)
        assert result.is_active is True
        assert result.id == poll.id

    def test_deactivate_active_poll(self) -> None:
        """Should deactivate an active poll."""
        use_case, poll_repo = _setup()
        poll = _create_poll(poll_repo, is_active=True)

        result = use_case.execute(poll.id, activate=False)

        assert result.is_active is False
        assert result.id == poll.id

    def test_activating_deactivates_currently_active_poll(self) -> None:
        """Should deactivate the current active poll when activating another."""
        use_case, poll_repo = _setup()
        event_id = uuid.uuid4()
        poll1 = _create_poll(poll_repo, event_id, is_active=True)
        poll2 = _create_poll(poll_repo, event_id, is_active=False)

        result = use_case.execute(poll2.id, activate=True)

        assert result.is_active is True
        assert result.id == poll2.id
        # Previous poll should now be deactivated
        old = poll_repo.get_by_id(poll1.id)
        assert old is not None
        assert old.is_active is False

    def test_activating_when_no_other_poll_is_active(self) -> None:
        """Should activate cleanly when no other poll is active."""
        use_case, poll_repo = _setup()
        event_id = uuid.uuid4()
        poll1 = _create_poll(poll_repo, event_id, is_active=False)
        _create_poll(poll_repo, event_id, is_active=False)

        result = use_case.execute(poll1.id, activate=True)

        assert result.is_active is True

    def test_activating_same_poll_already_active_stays_active(self) -> None:
        """Should keep a poll active if it is already the active one."""
        use_case, poll_repo = _setup()
        event_id = uuid.uuid4()
        poll = _create_poll(poll_repo, event_id, is_active=True)

        result = use_case.execute(poll.id, activate=True)

        assert result.is_active is True
        assert result.id == poll.id

    def test_poll_not_found_raises_error(self) -> None:
        """Should raise EntityNotFoundError for nonexistent poll."""
        use_case, _poll_repo = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundError, match="Poll"):
            use_case.execute(missing_id, activate=True)

    def test_result_includes_all_fields(self) -> None:
        """Result should include id, event_id, question, options, etc."""
        use_case, poll_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id, activate=True)

        assert result.event_id == poll.event_id
        assert result.question == poll.question
        assert len(result.options) == 2
        assert result.created_at is not None

    def test_result_is_frozen(self) -> None:
        """ActivatePollResult should be immutable."""
        use_case, poll_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id, activate=True)

        with pytest.raises(AttributeError):
            result.is_active = False  # type: ignore[misc]

    def test_deactivating_nonexistent_poll_raises_error(self) -> None:
        """Should raise EntityNotFoundError when deactivating missing poll."""
        use_case, _poll_repo = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundError, match="Poll"):
            use_case.execute(missing_id, activate=False)

    def test_activating_poll_does_not_affect_other_events(self) -> None:
        """Activating a poll should not deactivate polls in other events."""
        use_case, poll_repo = _setup()
        event1_id = uuid.uuid4()
        event2_id = uuid.uuid4()
        poll1 = _create_poll(poll_repo, event1_id, is_active=True)
        poll2 = _create_poll(poll_repo, event2_id, is_active=False)

        use_case.execute(poll2.id, activate=True)

        # Poll in event1 should remain active
        event1_poll = poll_repo.get_by_id(poll1.id)
        assert event1_poll is not None
        assert event1_poll.is_active is True
