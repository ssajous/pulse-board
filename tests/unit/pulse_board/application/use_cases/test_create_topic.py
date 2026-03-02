"""Tests for the create topic use case."""

import dataclasses
import uuid

import pytest

from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.exceptions import (
    EventNotActiveError,
    EventNotFoundError,
    ValidationError,
)
from tests.unit.pulse_board.fakes import (
    FakeEventRepository,
    FakeTopicRepository,
)


class TestCreateTopicUseCase:
    """Tests for CreateTopicUseCase."""

    def test_create_topic_success(self) -> None:
        """Should create a topic and return a result with all fields."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        result = use_case.execute("My new topic")

        assert result.content == "My new topic"
        assert result.score == 0
        assert result.id is not None
        assert result.created_at is not None

    def test_create_topic_result_is_frozen(self) -> None:
        """CreateTopicResult should be immutable."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)
        result = use_case.execute("test")

        with pytest.raises(AttributeError):
            result.content = "changed"  # type: ignore[misc]

    def test_create_topic_persists_to_repo(self) -> None:
        """Should persist the topic in the repository."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        result = use_case.execute("Persisted topic")

        saved = repo.get_by_id(result.id)
        assert saved is not None
        assert saved.content == "Persisted topic"

    def test_create_topic_strips_content(self) -> None:
        """Should strip whitespace from content before persisting."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        result = use_case.execute("  spaced out  ")

        assert result.content == "spaced out"

    def test_create_empty_content_raises_validation_error(self) -> None:
        """Should propagate ValidationError for empty content."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        with pytest.raises(ValidationError):
            use_case.execute("")

    def test_repo_not_touched_on_validation_error(self) -> None:
        """Repository should remain empty when validation fails."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        with pytest.raises(ValidationError):
            use_case.execute("")

        assert repo.list_active() == []


class TestCreateTopicWithEventValidation:
    """Tests for CreateTopicUseCase with event_id validation."""

    def test_create_topic_with_valid_active_event(self) -> None:
        """Should create topic when event exists and is active."""
        topic_repo = FakeTopicRepository()
        event_repo = FakeEventRepository()
        event = Event.create(title="Active Event", code="123456")
        event_repo.create(event)

        use_case = CreateTopicUseCase(
            repository=topic_repo,
            event_repository=event_repo,
        )

        result = use_case.execute("Topic for event", event_id=event.id)

        assert result.content == "Topic for event"
        assert result.event_id == event.id

    def test_raises_when_event_repo_not_configured(self) -> None:
        """Should raise EventNotFoundError when event_id given but no event repo."""
        topic_repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(
            repository=topic_repo,
            event_repository=None,
        )

        with pytest.raises(
            EventNotFoundError,
            match="not configured",
        ):
            use_case.execute("Topic", event_id=uuid.uuid4())

    def test_raises_when_event_not_found(self) -> None:
        """Should raise EventNotFoundError for unknown event_id."""
        topic_repo = FakeTopicRepository()
        event_repo = FakeEventRepository()
        use_case = CreateTopicUseCase(
            repository=topic_repo,
            event_repository=event_repo,
        )
        missing_id = uuid.uuid4()

        with pytest.raises(
            EventNotFoundError,
            match=str(missing_id),
        ):
            use_case.execute("Topic", event_id=missing_id)

    def test_raises_when_event_not_active(self) -> None:
        """Should raise EventNotActiveError for closed events."""
        topic_repo = FakeTopicRepository()
        event_repo = FakeEventRepository()
        event = Event.create(title="Closed Event", code="111111")
        event_repo.create(event)
        # Close the event
        closed = dataclasses.replace(event, status=EventStatus.CLOSED)
        event_repo._events[event.id] = closed

        use_case = CreateTopicUseCase(
            repository=topic_repo,
            event_repository=event_repo,
        )

        with pytest.raises(
            EventNotActiveError,
            match="not active",
        ):
            use_case.execute("Topic", event_id=event.id)

    def test_topic_not_persisted_when_event_validation_fails(self) -> None:
        """Repository should stay empty when event validation fails."""
        topic_repo = FakeTopicRepository()
        event_repo = FakeEventRepository()
        use_case = CreateTopicUseCase(
            repository=topic_repo,
            event_repository=event_repo,
        )

        with pytest.raises(EventNotFoundError):
            use_case.execute("Topic", event_id=uuid.uuid4())

        assert topic_repo.list_active() == []

    def test_no_event_id_skips_validation(self) -> None:
        """Should skip event validation when event_id is None."""
        topic_repo = FakeTopicRepository()
        event_repo = FakeEventRepository()
        use_case = CreateTopicUseCase(
            repository=topic_repo,
            event_repository=event_repo,
        )

        result = use_case.execute("Global topic")

        assert result.event_id is None
