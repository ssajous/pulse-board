"""Integration tests for SQLAlchemyVoteRepository."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.entities.vote import Vote
from pulse_board.infrastructure.repositories.topic_repository import (
    SQLAlchemyTopicRepository,
)
from pulse_board.infrastructure.repositories.vote_repository import (
    SQLAlchemyVoteRepository,
)


@pytest.fixture
def topic_repo(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
    cleanup_votes: None,
) -> SQLAlchemyTopicRepository:
    """Create topic repository for FK setup."""
    return SQLAlchemyTopicRepository(
        session_factory=integration_session_factory,
    )


@pytest.fixture
def vote_repo(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
    cleanup_votes: None,
) -> SQLAlchemyVoteRepository:
    """Create vote repository using the integration session."""
    return SQLAlchemyVoteRepository(
        session_factory=integration_session_factory,
    )


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


def _make_vote(
    topic_id: uuid.UUID,
    fingerprint_id: str = "fp-abc123",
    value: int = 1,
) -> Vote:
    """Create a Vote entity for the given topic."""
    now = datetime.now(UTC)
    return Vote(
        id=uuid.uuid4(),
        topic_id=topic_id,
        fingerprint_id=fingerprint_id,
        value=value,
        created_at=now,
        updated_at=now,
    )


class TestVoteRepositorySave:
    """Tests for the save method."""

    def test_save_creates_new_vote(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(topic_id=topic.id)
        saved = vote_repo.save(vote)

        assert saved.id == vote.id
        assert saved.topic_id == topic.id
        assert saved.fingerprint_id == vote.fingerprint_id
        assert saved.value == vote.value

    def test_save_updates_existing_vote(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(topic_id=topic.id, value=1)
        vote_repo.save(vote)

        vote.value = -1
        vote.updated_at = datetime.now(UTC)
        updated = vote_repo.save(vote)

        assert updated.id == vote.id
        assert updated.value == -1

    def test_save_preserves_all_fields(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(
            topic_id=topic.id,
            fingerprint_id="fp-unique-xyz",
            value=-1,
        )
        saved = vote_repo.save(vote)

        assert saved.fingerprint_id == "fp-unique-xyz"
        assert saved.value == -1
        assert saved.created_at is not None
        assert saved.updated_at is not None


class TestVoteRepositoryFindByTopicAndFingerprint:
    """Tests for the find_by_topic_and_fingerprint method."""

    def test_find_existing_vote(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(
            topic_id=topic.id,
            fingerprint_id="fp-findme",
        )
        vote_repo.save(vote)

        found = vote_repo.find_by_topic_and_fingerprint(
            topic_id=topic.id,
            fingerprint_id="fp-findme",
        )
        assert found is not None
        assert found.id == vote.id
        assert found.fingerprint_id == "fp-findme"

    def test_find_returns_none_when_not_found(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        result = vote_repo.find_by_topic_and_fingerprint(
            topic_id=topic.id,
            fingerprint_id="fp-nonexistent",
        )
        assert result is None

    def test_find_returns_none_for_wrong_topic(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(
            topic_id=topic.id,
            fingerprint_id="fp-topic-check",
        )
        vote_repo.save(vote)

        result = vote_repo.find_by_topic_and_fingerprint(
            topic_id=uuid.uuid4(),
            fingerprint_id="fp-topic-check",
        )
        assert result is None


class TestVoteRepositoryDelete:
    """Tests for the delete method."""

    def test_delete_removes_vote(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(topic_id=topic.id)
        vote_repo.save(vote)
        vote_repo.delete(vote.id)

        found = vote_repo.find_by_topic_and_fingerprint(
            topic_id=topic.id,
            fingerprint_id=vote.fingerprint_id,
        )
        assert found is None

    def test_delete_nonexistent_does_not_raise(
        self,
        vote_repo: SQLAlchemyVoteRepository,
    ) -> None:
        vote_repo.delete(uuid.uuid4())


class TestVoteRepositoryCountByTopic:
    """Tests for the count_by_topic method."""

    def test_count_returns_correct_count(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        for i in range(3):
            vote = _make_vote(
                topic_id=topic.id,
                fingerprint_id=f"fp-count-{i}",
            )
            vote_repo.save(vote)

        assert vote_repo.count_by_topic(topic.id) == 3

    def test_count_returns_zero_for_no_votes(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        assert vote_repo.count_by_topic(topic.id) == 0


class TestVoteRepositoryConstraints:
    """Tests for database constraints."""

    def test_unique_constraint_prevents_duplicate(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
        integration_session_factory: sessionmaker,  # type: ignore[type-arg]
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote1 = _make_vote(
            topic_id=topic.id,
            fingerprint_id="fp-dup-test",
        )
        vote_repo.save(vote1)

        # Insert a second vote with a different id but same
        # (topic_id, fingerprint_id) directly via ORM to bypass
        # merge semantics and trigger the constraint.
        from pulse_board.infrastructure.database.models.vote_model import (
            VoteModel,
        )

        now = datetime.now(UTC)
        duplicate = VoteModel(
            id=uuid.uuid4(),
            topic_id=topic.id,
            fingerprint_id="fp-dup-test",
            value=1,
            created_at=now,
            updated_at=now,
        )
        with pytest.raises(IntegrityError):
            with integration_session_factory() as session:
                session.add(duplicate)
                session.commit()

    def test_cascade_delete_removes_votes(
        self,
        vote_repo: SQLAlchemyVoteRepository,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic()
        topic_repo.create(topic)

        vote = _make_vote(topic_id=topic.id)
        vote_repo.save(vote)

        topic_repo.delete(topic.id)

        found = vote_repo.find_by_topic_and_fingerprint(
            topic_id=topic.id,
            fingerprint_id=vote.fingerprint_id,
        )
        assert found is None
        assert vote_repo.count_by_topic(topic.id) == 0


class TestTopicRepositoryUpdateScore:
    """Tests for the update_score method on TopicRepository."""

    def test_update_score_increments(
        self,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic(score=0)
        topic_repo.create(topic)

        updated = topic_repo.update_score(topic.id, delta=1)
        assert updated is not None
        assert updated.score == 1

    def test_update_score_decrements(
        self,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        topic = _make_topic(score=5)
        topic_repo.create(topic)

        updated = topic_repo.update_score(topic.id, delta=-3)
        assert updated is not None
        assert updated.score == 2

    def test_update_score_returns_none_for_missing(
        self,
        topic_repo: SQLAlchemyTopicRepository,
    ) -> None:
        result = topic_repo.update_score(uuid.uuid4(), delta=1)
        assert result is None
