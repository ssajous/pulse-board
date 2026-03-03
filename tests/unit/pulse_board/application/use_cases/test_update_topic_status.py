"""Tests for UpdateTopicStatusUseCase."""

import uuid

import pytest

from pulse_board.application.use_cases.update_topic_status import (
    UpdateTopicStatusUseCase,
)
from pulse_board.domain.entities.topic import Topic, TopicStatus
from pulse_board.domain.exceptions import TopicNotFoundError
from tests.unit.pulse_board.fakes import FakeTopicRepository


@pytest.fixture
def repo() -> FakeTopicRepository:
    """Provide a fresh in-memory topic repository."""
    return FakeTopicRepository()


@pytest.fixture
def use_case(repo: FakeTopicRepository) -> UpdateTopicStatusUseCase:
    """Provide an UpdateTopicStatusUseCase wired to the fake repository."""
    return UpdateTopicStatusUseCase(topic_repository=repo)


class TestUpdateTopicStatus:
    """Tests for UpdateTopicStatusUseCase.execute."""

    def test_success(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """Should update status and return result with new status value."""
        event_id = uuid.uuid4()
        topic = Topic.create("Test topic", event_id=event_id)
        repo.create(topic)

        result = use_case.execute(topic.id, TopicStatus.HIGHLIGHTED, event_id)

        assert result.topic_id == topic.id
        assert result.new_status == "highlighted"
        updated = repo.get_by_id(topic.id)
        assert updated is not None
        assert updated.status == TopicStatus.HIGHLIGHTED

    def test_wrong_event_raises(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """Should raise TopicNotFoundError when topic belongs to different event."""
        event_id = uuid.uuid4()
        other_event_id = uuid.uuid4()
        topic = Topic.create("Test topic", event_id=event_id)
        repo.create(topic)

        with pytest.raises(TopicNotFoundError):
            use_case.execute(topic.id, TopicStatus.ANSWERED, other_event_id)

    def test_not_found_raises(self, use_case: UpdateTopicStatusUseCase) -> None:
        """Should raise TopicNotFoundError when topic does not exist."""
        with pytest.raises(TopicNotFoundError):
            use_case.execute(uuid.uuid4(), TopicStatus.ARCHIVED, uuid.uuid4())

    def test_status_answered(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """Should correctly update to answered status."""
        event_id = uuid.uuid4()
        topic = Topic.create("Another topic", event_id=event_id)
        repo.create(topic)

        result = use_case.execute(topic.id, TopicStatus.ANSWERED, event_id)

        assert result.new_status == "answered"
        updated = repo.get_by_id(topic.id)
        assert updated is not None
        assert updated.status == TopicStatus.ANSWERED

    def test_status_archived(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """Should correctly update to archived status."""
        event_id = uuid.uuid4()
        topic = Topic.create("Archived topic", event_id=event_id)
        repo.create(topic)

        result = use_case.execute(topic.id, TopicStatus.ARCHIVED, event_id)

        assert result.new_status == "archived"
        updated = repo.get_by_id(topic.id)
        assert updated is not None
        assert updated.status == TopicStatus.ARCHIVED

    def test_result_is_frozen(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """UpdateTopicStatusResult should be immutable."""
        event_id = uuid.uuid4()
        topic = Topic.create("Frozen test", event_id=event_id)
        repo.create(topic)

        result = use_case.execute(topic.id, TopicStatus.HIGHLIGHTED, event_id)

        with pytest.raises(AttributeError):
            result.new_status = "active"  # type: ignore[misc]

    def test_returns_correct_topic_id(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """Result should carry back the same topic_id provided."""
        event_id = uuid.uuid4()
        topic = Topic.create("ID check topic", event_id=event_id)
        repo.create(topic)

        result = use_case.execute(topic.id, TopicStatus.ACTIVE, event_id)

        assert result.topic_id == topic.id

    def test_original_topic_not_mutated_in_repo(
        self,
        repo: FakeTopicRepository,
        use_case: UpdateTopicStatusUseCase,
    ) -> None:
        """Repo should hold updated entity, not original."""
        event_id = uuid.uuid4()
        topic = Topic.create("Mutation test", event_id=event_id)
        repo.create(topic)
        assert topic.status == TopicStatus.ACTIVE

        use_case.execute(topic.id, TopicStatus.ANSWERED, event_id)

        updated = repo.get_by_id(topic.id)
        assert updated is not None
        assert updated.status == TopicStatus.ANSWERED
