"""Tests for the VotingService domain service."""

import uuid
from datetime import UTC, datetime

from pulse_board.domain.entities.vote import DOWNVOTE, UPVOTE, Vote
from pulse_board.domain.services.voting_service import (
    CENSURE_THRESHOLD,
    VoteCancelled,
    VoteCreated,
    VoteToggled,
    VotingService,
    is_censured,
)

TOPIC_ID = uuid.uuid4()
FINGERPRINT = "browser-fp-abc123"


def _make_vote(
    value: int = UPVOTE,
    topic_id: uuid.UUID | None = None,
) -> Vote:
    """Create a Vote entity for testing.

    Args:
        value: The vote value (+1 or -1).
        topic_id: Optional topic UUID; defaults to module constant.

    Returns:
        A Vote instance with known test data.
    """
    return Vote(
        id=uuid.uuid4(),
        topic_id=topic_id or TOPIC_ID,
        fingerprint_id=FINGERPRINT,
        value=value,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestProcessVoteCreateNew:
    """Tests for creating a new vote when no existing vote."""

    def setup_method(self) -> None:
        """Create a fresh VotingService for each test."""
        self.service = VotingService()

    def test_creates_new_upvote(self) -> None:
        """Should return VoteCreated with an upvote when no
        existing vote and direction is +1."""
        result = self.service.process_vote(
            existing_vote=None,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=UPVOTE,
        )

        assert isinstance(result, VoteCreated)
        assert result.vote.value == UPVOTE
        assert result.vote.topic_id == TOPIC_ID
        assert result.vote.fingerprint_id == FINGERPRINT

    def test_creates_new_downvote(self) -> None:
        """Should return VoteCreated with a downvote when no
        existing vote and direction is -1."""
        result = self.service.process_vote(
            existing_vote=None,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert isinstance(result, VoteCreated)
        assert result.vote.value == DOWNVOTE
        assert result.vote.topic_id == TOPIC_ID

    def test_created_upvote_score_delta_is_plus_one(self) -> None:
        """VoteCreated for an upvote should have score_delta +1."""
        result = self.service.process_vote(
            existing_vote=None,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=UPVOTE,
        )

        assert result.score_delta == 1

    def test_created_downvote_score_delta_is_minus_one(self) -> None:
        """VoteCreated for a downvote should have score_delta -1."""
        result = self.service.process_vote(
            existing_vote=None,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert result.score_delta == -1


class TestProcessVoteCancel:
    """Tests for cancelling a vote (same direction clicked again)."""

    def setup_method(self) -> None:
        """Create a fresh VotingService for each test."""
        self.service = VotingService()

    def test_cancels_upvote_when_same_direction(self) -> None:
        """Should return VoteCancelled when existing upvote
        matches the requested upvote direction."""
        existing = _make_vote(value=UPVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=UPVOTE,
        )

        assert isinstance(result, VoteCancelled)
        assert result.vote_id == existing.id

    def test_cancels_downvote_when_same_direction(self) -> None:
        """Should return VoteCancelled when existing downvote
        matches the requested downvote direction."""
        existing = _make_vote(value=DOWNVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert isinstance(result, VoteCancelled)
        assert result.vote_id == existing.id

    def test_cancelled_upvote_score_delta(self) -> None:
        """Cancelling an upvote should produce score_delta -1."""
        existing = _make_vote(value=UPVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=UPVOTE,
        )

        assert result.score_delta == -1

    def test_cancelled_downvote_score_delta(self) -> None:
        """Cancelling a downvote should produce score_delta +1."""
        existing = _make_vote(value=DOWNVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert result.score_delta == 1


class TestProcessVoteToggle:
    """Tests for toggling a vote (different direction)."""

    def setup_method(self) -> None:
        """Create a fresh VotingService for each test."""
        self.service = VotingService()

    def test_toggles_upvote_to_downvote(self) -> None:
        """Should return VoteToggled when existing upvote
        meets a downvote direction."""
        existing = _make_vote(value=UPVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert isinstance(result, VoteToggled)
        assert result.vote.value == DOWNVOTE

    def test_toggles_downvote_to_upvote(self) -> None:
        """Should return VoteToggled when existing downvote
        meets an upvote direction."""
        existing = _make_vote(value=DOWNVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=UPVOTE,
        )

        assert isinstance(result, VoteToggled)
        assert result.vote.value == UPVOTE

    def test_toggled_up_to_down_score_delta(self) -> None:
        """Toggling from upvote to downvote should produce
        score_delta -2."""
        existing = _make_vote(value=UPVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert result.score_delta == -2

    def test_toggled_down_to_up_score_delta(self) -> None:
        """Toggling from downvote to upvote should produce
        score_delta +2."""
        existing = _make_vote(value=DOWNVOTE)

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=UPVOTE,
        )

        assert result.score_delta == 2

    def test_toggled_vote_is_same_entity(self) -> None:
        """The toggled result should reference the same Vote
        object (mutated in place)."""
        existing = _make_vote(value=UPVOTE)
        original_id = existing.id

        result = self.service.process_vote(
            existing_vote=existing,
            topic_id=TOPIC_ID,
            fingerprint_id=FINGERPRINT,
            direction=DOWNVOTE,
        )

        assert isinstance(result, VoteToggled)
        assert result.vote.id == original_id


class TestIsCensured:
    """Tests for the is_censured helper function."""

    def test_censured_at_threshold(self) -> None:
        """Score equal to CENSURE_THRESHOLD should be censured."""
        assert is_censured(CENSURE_THRESHOLD) is True

    def test_censured_below_threshold(self) -> None:
        """Score below CENSURE_THRESHOLD should be censured."""
        assert is_censured(CENSURE_THRESHOLD - 1) is True
        assert is_censured(-100) is True

    def test_not_censured_above_threshold(self) -> None:
        """Score above CENSURE_THRESHOLD should not be censured."""
        assert is_censured(CENSURE_THRESHOLD + 1) is False

    def test_not_censured_at_zero(self) -> None:
        """Score of zero should not be censured."""
        assert is_censured(0) is False

    def test_not_censured_positive(self) -> None:
        """Positive scores should not be censured."""
        assert is_censured(10) is False

    def test_threshold_boundary(self) -> None:
        """Verify the exact boundary: -4 is not censured,
        -5 is censured."""
        assert is_censured(-4) is False
        assert is_censured(-5) is True
