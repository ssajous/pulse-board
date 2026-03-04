"""Tests for creating word cloud polls via the CreatePollUseCase."""

import pytest

from pulse_board.application.use_cases.create_poll import (
    CreatePollResult,
    CreatePollUseCase,
)
from pulse_board.domain.entities.event import Event
from pulse_board.domain.exceptions import ValidationError
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
    event = Event.create(title="Test Event", code="WC1234")
    return event_repo.create(event)


class TestCreateWordCloudPoll:
    """Tests for creating word cloud polls through CreatePollUseCase."""

    def test_word_cloud_type_accepted_with_empty_options(self) -> None:
        """Should create a word cloud poll successfully with no options."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "What one word describes this session?",
            [],
            poll_type="word_cloud",
        )

        assert isinstance(result, CreatePollResult)
        assert result.poll_type == "word_cloud"
        assert result.event_id == event.id

    def test_word_cloud_poll_has_no_options(self) -> None:
        """Word cloud polls should store no selectable options."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "One word for today?",
            [],
            poll_type="word_cloud",
        )

        assert result.options == []

    def test_word_cloud_poll_starts_inactive(self) -> None:
        """Newly created word cloud polls should not be active."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "How do you feel?",
            [],
            poll_type="word_cloud",
        )

        assert result.is_active is False

    def test_word_cloud_poll_options_are_ignored(self) -> None:
        """Provided option texts should be ignored for word cloud polls."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "One word?",
            ["Option A", "Option B"],
            poll_type="word_cloud",
        )

        # Options should not appear in the result for word cloud polls
        assert result.options == []
        assert result.poll_type == "word_cloud"

    def test_word_cloud_poll_persisted_to_repository(self) -> None:
        """Should persist the word cloud poll to the repository."""
        use_case, poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Describe in one word?",
            [],
            poll_type="word_cloud",
        )

        saved = poll_repo.get_by_id(result.id)
        assert saved is not None
        assert saved.poll_type == "word_cloud"
        assert saved.question == "Describe in one word?"

    def test_word_cloud_poll_result_has_id_and_created_at(self) -> None:
        """Result should include a valid id and created_at timestamp."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Tag word?",
            [],
            poll_type="word_cloud",
        )

        assert result.id is not None
        assert result.created_at is not None

    def test_word_cloud_question_validation_applies(self) -> None:
        """Should raise ValidationError for an empty question."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        with pytest.raises(ValidationError):
            use_case.execute(event.id, "", [], poll_type="word_cloud")

    def test_word_cloud_question_too_long_raises_validation_error(self) -> None:
        """Should raise ValidationError for question over 500 characters."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)
        long_question = "Q" * 501

        with pytest.raises(ValidationError, match="500 characters or fewer"):
            use_case.execute(event.id, long_question, [], poll_type="word_cloud")

    def test_word_cloud_result_is_frozen(self) -> None:
        """CreatePollResult should be immutable for word cloud polls."""
        use_case, _poll_repo, event_repo = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(
            event.id,
            "Frozen?",
            [],
            poll_type="word_cloud",
        )

        with pytest.raises(AttributeError):
            result.question = "changed"  # type: ignore[misc]
