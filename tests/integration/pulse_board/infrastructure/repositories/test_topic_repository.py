"""Integration tests for SQLAlchemyTopicRepository."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import sessionmaker

from pulse_board.domain.entities.topic import Topic
from pulse_board.infrastructure.repositories.topic_repository import (
    SQLAlchemyTopicRepository,
)


@pytest.fixture
def repo(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
    cleanup_topics: None,
) -> SQLAlchemyTopicRepository:
    """Create repository using the integration session factory."""
    return SQLAlchemyTopicRepository(session_factory=integration_session_factory)


def _make_topic(
    content: str = "Test topic",
    score: int = 0,
) -> Topic:
    """Create a Topic entity with optional overrides."""
    return Topic(
        id=uuid.uuid4(),
        content=content,
        score=score,
        created_at=datetime.now(UTC),
    )


class TestTopicRepositoryCreate:
    """Tests for the create method."""

    def test_create_persists_topic(self, repo: SQLAlchemyTopicRepository) -> None:
        topic = _make_topic()
        repo.create(topic)

        result = repo.get_by_id(topic.id)
        assert result is not None
        assert result.id == topic.id

    def test_create_returns_topic_with_correct_fields(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        topic = _make_topic(content="My important topic", score=5)
        created = repo.create(topic)

        assert created.id == topic.id
        assert created.content == "My important topic"
        assert created.score == 5
        assert created.created_at is not None

    def test_create_multiple_topics(self, repo: SQLAlchemyTopicRepository) -> None:
        topics = [_make_topic(content=f"Topic {i}") for i in range(3)]
        for t in topics:
            repo.create(t)

        active = repo.list_active()
        assert len(active) == 3


class TestTopicRepositoryGetById:
    """Tests for the get_by_id method."""

    def test_get_existing_topic(self, repo: SQLAlchemyTopicRepository) -> None:
        topic = _make_topic(content="Findable topic")
        repo.create(topic)

        result = repo.get_by_id(topic.id)
        assert result is not None
        assert result.content == "Findable topic"

    def test_get_nonexistent_returns_none(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        result = repo.get_by_id(uuid.uuid4())
        assert result is None


class TestTopicRepositoryListActive:
    """Tests for the list_active method."""

    def test_list_active_empty(self, repo: SQLAlchemyTopicRepository) -> None:
        result = repo.list_active()
        assert result == []

    def test_list_active_returns_all_positive(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        for i in range(3):
            repo.create(_make_topic(content=f"Positive {i}", score=i + 1))

        result = repo.list_active()
        assert len(result) == 3

    def test_list_active_includes_score_minus_4(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        repo.create(_make_topic(content="Borderline safe", score=-4))

        result = repo.list_active()
        assert len(result) == 1
        assert result[0].score == -4

    def test_list_active_excludes_score_minus_5(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        repo.create(_make_topic(content="At threshold", score=-5))

        result = repo.list_active()
        assert len(result) == 0

    def test_list_active_excludes_score_minus_10(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        repo.create(_make_topic(content="Very negative", score=-10))

        result = repo.list_active()
        assert len(result) == 0

    def test_list_active_includes_zero_score(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        repo.create(_make_topic(content="Neutral topic", score=0))

        result = repo.list_active()
        assert len(result) == 1
        assert result[0].score == 0


class TestTopicRepositoryDelete:
    """Tests for the delete method."""

    def test_delete_existing_topic(self, repo: SQLAlchemyTopicRepository) -> None:
        topic = _make_topic()
        repo.create(topic)

        repo.delete(topic.id)
        result = repo.get_by_id(topic.id)
        assert result is None

    def test_delete_nonexistent_does_not_raise(
        self, repo: SQLAlchemyTopicRepository
    ) -> None:
        repo.delete(uuid.uuid4())
