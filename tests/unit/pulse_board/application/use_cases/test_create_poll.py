"""Tests for the create poll use case."""

import uuid

import pytest

from pulse_board.application.use_cases.create_poll import (
    CreatePollResult,
    CreatePollUseCase,
)
from pulse_board.domain.entities.event import Event
from pulse_board.domain.exceptions import EventNotFoundError, ValidationError
from tests.unit.pulse_board.fakes import (
    FakeEventRepository,
    FakePollRepository,
)


def _setup() -> tuple[
    CreatePollUseCase,
    FakePollRepository,
    FakeEventRepository,
]:
    """Create a CreatePollUseCase with fresh fake repositories."""
    poll_repo = FakePollRepository()
    event_repo = FakeEventRepository()
    use_case = CreatePollUseCase(
        poll_repository=poll_repo,
        event_repository=event_repo,
    )
    return use_case, poll_repo, event_repo


def _create_event(event_repo: FakeEventRepository) -> Event:
    """Create and persist a valid event."""
    event = Event.create(title="Test Event", code="ABC123")
    return event_repo.create(event)


class TestCreatePollUseCase:
    """Tests for CreatePollUseCase.execute."""

    def test_creates_poll_successfully(self) -> None:
        """Should create a poll and return a result with all fields."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "What is your favorite color?",
            ["Red", "Blue", "Green"],
        )

        assert isinstance(result, CreatePollResult)
        assert result.event_id == event.id
        assert result.question == "What is your favorite color?"
        assert result.poll_type == "multiple_choice"
        assert result.is_active is False
        assert result.id is not None
        assert result.created_at is not None

    def test_creates_poll_with_correct_options(self) -> None:
        """Should include all options in the result with id and text."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Pick one",
            ["Alpha", "Bravo", "Charlie"],
        )

        assert len(result.options) == 3
        texts = [opt["text"] for opt in result.options]
        assert texts == ["Alpha", "Bravo", "Charlie"]
        for opt in result.options:
            assert "id" in opt
            assert "text" in opt
            # Each option id should be a valid UUID string
            uuid.UUID(opt["id"])

    def test_persists_poll_to_repository(self) -> None:
        """Should persist the poll in the repository."""
        use_case, poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Persisted?",
            ["Yes", "No"],
        )

        saved = poll_repo.get_by_id(result.id)
        assert saved is not None
        assert saved.question == "Persisted?"
        assert saved.event_id == event.id

    def test_event_not_found_raises_error(self) -> None:
        """Should raise EventNotFoundError for nonexistent event."""
        use_case, _poll_repo, _event_repo = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EventNotFoundError):
            use_case.execute(
                missing_id,
                "Question?",
                ["A", "B"],
            )

    def test_empty_question_raises_validation_error(self) -> None:
        """Should propagate ValidationError for empty question."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        with pytest.raises(ValidationError):
            use_case.execute(event.id, "", ["A", "B"])

    def test_too_few_options_raises_validation_error(self) -> None:
        """Should propagate ValidationError for fewer than 2 options."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        with pytest.raises(ValidationError, match="at least 2 options"):
            use_case.execute(event.id, "Question?", ["Only one"])

    def test_too_many_options_raises_validation_error(self) -> None:
        """Should propagate ValidationError for more than 10 options."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)
        options = [f"Option {i}" for i in range(11)]

        with pytest.raises(ValidationError, match="at most 10 options"):
            use_case.execute(event.id, "Question?", options)

    def test_too_long_question_raises_validation_error(self) -> None:
        """Should propagate ValidationError for question over 500 chars."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)
        long_question = "Q" * 501

        with pytest.raises(ValidationError, match="500 characters or fewer"):
            use_case.execute(event.id, long_question, ["A", "B"])

    def test_result_is_frozen(self) -> None:
        """CreatePollResult should be immutable."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Frozen?",
            ["Yes", "No"],
        )

        with pytest.raises(AttributeError):
            result.question = "changed"  # type: ignore[misc]

    def test_new_poll_starts_inactive(self) -> None:
        """Newly created polls should not be active."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Active?",
            ["Yes", "No"],
        )

        assert result.is_active is False

    def test_boundary_two_options_accepted(self) -> None:
        """Should accept exactly 2 options (minimum boundary)."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Two options?",
            ["A", "B"],
        )

        assert len(result.options) == 2

    def test_boundary_ten_options_accepted(self) -> None:
        """Should accept exactly 10 options (maximum boundary)."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)
        options = [f"Option {i}" for i in range(10)]

        result = use_case.execute(
            event.id,
            "Ten options?",
            options,
        )

        assert len(result.options) == 10

    def test_question_at_max_length_accepted(self) -> None:
        """Should accept a question at exactly 500 characters."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)
        question = "Q" * 500

        result = use_case.execute(
            event.id,
            question,
            ["A", "B"],
        )

        assert len(result.question) == 500
