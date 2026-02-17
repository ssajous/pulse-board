"""Tests for the cast vote use case."""

import uuid

import pytest

from pulse_board.application.use_cases.cast_vote import (
    CastVoteUseCase,
)
from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.entities.vote import DOWNVOTE, UPVOTE
from pulse_board.domain.events import TopicCensuredEvent
from pulse_board.domain.exceptions import EntityNotFoundError
from pulse_board.domain.services.voting_service import (
    CENSURE_THRESHOLD,
    VotingService,
)
from tests.unit.pulse_board.fakes import (
    FakeTopicRepository,
    FakeVoteRepository,
)

FINGERPRINT = "test-fingerprint-abc"


def _setup() -> tuple[
    CastVoteUseCase,
    FakeVoteRepository,
    FakeTopicRepository,
]:
    """Create a CastVoteUseCase with fresh fake repositories."""
    vote_repo = FakeVoteRepository()
    topic_repo = FakeTopicRepository()
    voting_service = VotingService()
    use_case = CastVoteUseCase(
        vote_repo=vote_repo,
        topic_repo=topic_repo,
        voting_service=voting_service,
    )
    return use_case, vote_repo, topic_repo


def _create_topic(
    topic_repo: FakeTopicRepository,
    score: int = 0,
) -> Topic:
    """Create and persist a topic with a given initial score."""
    topic = Topic.create("Test topic")
    topic.score = score
    return topic_repo.create(topic)


class TestCastVoteUseCase:
    """Tests for CastVoteUseCase."""

    def test_cast_vote_creates_new_upvote(self) -> None:
        """Should create a new upvote and return score of 1."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo)

        result = use_case.execute(topic.id, FINGERPRINT, UPVOTE)

        assert result.topic_id == topic.id
        assert result.new_score == 1
        assert result.vote_status == "created"
        assert result.vote_direction == UPVOTE
        assert result.censured is False
        assert result.event is None

    def test_cast_vote_creates_new_downvote(self) -> None:
        """Should create a new downvote and return score of -1."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo)

        result = use_case.execute(topic.id, FINGERPRINT, DOWNVOTE)

        assert result.new_score == -1
        assert result.vote_status == "created"
        assert result.vote_direction == DOWNVOTE

    def test_cast_vote_toggles_existing_vote(self) -> None:
        """Should toggle upvote to downvote with score delta of -2."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo)

        use_case.execute(topic.id, FINGERPRINT, UPVOTE)
        result = use_case.execute(topic.id, FINGERPRINT, DOWNVOTE)

        assert result.new_score == -1
        assert result.vote_status == "toggled"
        assert result.vote_direction == DOWNVOTE

    def test_cast_vote_cancels_same_direction(self) -> None:
        """Should cancel vote when same direction is cast again."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo)

        use_case.execute(topic.id, FINGERPRINT, UPVOTE)
        result = use_case.execute(topic.id, FINGERPRINT, UPVOTE)

        assert result.new_score == 0
        assert result.vote_status == "cancelled"
        assert result.vote_direction is None

    def test_cast_vote_returns_censured_when_score_hits_threshold(
        self,
    ) -> None:
        """Should report censured when score reaches threshold."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo, score=CENSURE_THRESHOLD)

        result = use_case.execute(topic.id, FINGERPRINT, DOWNVOTE)

        assert result.censured is True
        assert result.new_score == CENSURE_THRESHOLD + DOWNVOTE

    def test_cast_vote_returns_censure_event_when_censured(
        self,
    ) -> None:
        """Should include TopicCensuredEvent when topic is censured."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo, score=CENSURE_THRESHOLD)

        result = use_case.execute(topic.id, FINGERPRINT, DOWNVOTE)

        assert result.event is not None
        assert isinstance(result.event, TopicCensuredEvent)
        assert result.event.topic_id == topic.id
        assert result.event.final_score == result.new_score

    def test_cast_vote_raises_not_found_for_missing_topic(
        self,
    ) -> None:
        """Should raise EntityNotFoundError for nonexistent topic."""
        use_case, _vote_repo, _topic_repo = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundError, match="Topic not found"):
            use_case.execute(missing_id, FINGERPRINT, UPVOTE)

    def test_cast_vote_result_is_frozen(self) -> None:
        """CastVoteResult should be immutable."""
        use_case, _vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo)

        result = use_case.execute(topic.id, FINGERPRINT, UPVOTE)

        with pytest.raises(AttributeError):
            result.new_score = 99  # type: ignore[misc]

    def test_cast_vote_persists_vote_to_repo(self) -> None:
        """Should persist the vote in the vote repository."""
        use_case, vote_repo, topic_repo = _setup()
        topic = _create_topic(topic_repo)

        use_case.execute(topic.id, FINGERPRINT, UPVOTE)

        saved = vote_repo.find_by_topic_and_fingerprint(topic.id, FINGERPRINT)
        assert saved is not None
        assert saved.value == UPVOTE
        assert saved.topic_id == topic.id
        assert saved.fingerprint_id == FINGERPRINT
