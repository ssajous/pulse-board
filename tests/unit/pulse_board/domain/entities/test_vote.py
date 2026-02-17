"""Tests for the Vote domain entity."""

import uuid
from datetime import UTC, datetime
from time import sleep

import pytest

from pulse_board.domain.entities.vote import (
    DOWNVOTE,
    UPVOTE,
    Vote,
)
from pulse_board.domain.exceptions import ValidationError


class TestVoteCreate:
    """Tests for Vote.create factory method."""

    def test_create_valid_upvote(self) -> None:
        """Should create a vote with UPVOTE value."""
        topic_id = uuid.uuid4()
        vote = Vote.create(
            topic_id=topic_id,
            fingerprint_id="abc123",
            value=UPVOTE,
        )

        assert vote.topic_id == topic_id
        assert vote.fingerprint_id == "abc123"
        assert vote.value == UPVOTE

    def test_create_valid_downvote(self) -> None:
        """Should create a vote with DOWNVOTE value."""
        topic_id = uuid.uuid4()
        vote = Vote.create(
            topic_id=topic_id,
            fingerprint_id="abc123",
            value=DOWNVOTE,
        )

        assert vote.value == DOWNVOTE

    def test_create_generates_unique_id(self) -> None:
        """Should generate a unique UUID4 for each vote."""
        topic_id = uuid.uuid4()
        vote_a = Vote.create(
            topic_id=topic_id,
            fingerprint_id="fp1",
            value=UPVOTE,
        )
        vote_b = Vote.create(
            topic_id=topic_id,
            fingerprint_id="fp2",
            value=UPVOTE,
        )

        assert vote_a.id != vote_b.id
        assert vote_a.id.version == 4
        assert vote_b.id.version == 4

    def test_create_sets_timestamps(self) -> None:
        """Should set created_at and updated_at to current time."""
        before = datetime.now(UTC)
        vote = Vote.create(
            topic_id=uuid.uuid4(),
            fingerprint_id="fp1",
            value=UPVOTE,
        )
        after = datetime.now(UTC)

        assert before <= vote.created_at <= after
        assert before <= vote.updated_at <= after
        assert vote.created_at == vote.updated_at

    def test_create_rejects_invalid_value_zero(self) -> None:
        """Should raise ValidationError for value of 0."""
        with pytest.raises(ValidationError, match="Vote value"):
            Vote.create(
                topic_id=uuid.uuid4(),
                fingerprint_id="fp1",
                value=0,
            )

    def test_create_rejects_invalid_value_two(self) -> None:
        """Should raise ValidationError for value of 2."""
        with pytest.raises(ValidationError, match="Vote value"):
            Vote.create(
                topic_id=uuid.uuid4(),
                fingerprint_id="fp1",
                value=2,
            )

    def test_create_rejects_empty_fingerprint(self) -> None:
        """Should raise ValidationError for empty fingerprint."""
        with pytest.raises(ValidationError, match="Fingerprint"):
            Vote.create(
                topic_id=uuid.uuid4(),
                fingerprint_id="",
                value=UPVOTE,
            )

    def test_create_rejects_whitespace_fingerprint(self) -> None:
        """Should raise ValidationError for whitespace-only fingerprint."""
        with pytest.raises(ValidationError, match="Fingerprint"):
            Vote.create(
                topic_id=uuid.uuid4(),
                fingerprint_id="   ",
                value=UPVOTE,
            )


class TestVoteToggle:
    """Tests for Vote.toggle method."""

    def test_toggle_upvote_to_downvote(self) -> None:
        """Should flip UPVOTE to DOWNVOTE."""
        vote = Vote.create(
            topic_id=uuid.uuid4(),
            fingerprint_id="fp1",
            value=UPVOTE,
        )

        vote.toggle()

        assert vote.value == DOWNVOTE

    def test_toggle_downvote_to_upvote(self) -> None:
        """Should flip DOWNVOTE to UPVOTE."""
        vote = Vote.create(
            topic_id=uuid.uuid4(),
            fingerprint_id="fp1",
            value=DOWNVOTE,
        )

        vote.toggle()

        assert vote.value == UPVOTE

    def test_toggle_updates_updated_at(self) -> None:
        """Should update updated_at to a later timestamp."""
        vote = Vote.create(
            topic_id=uuid.uuid4(),
            fingerprint_id="fp1",
            value=UPVOTE,
        )
        original_updated_at = vote.updated_at

        # Small sleep to guarantee timestamp difference
        sleep(0.001)
        vote.toggle()

        assert vote.updated_at > original_updated_at
        assert vote.created_at < vote.updated_at


class TestVoteReconstitution:
    """Tests for direct constructor (repository reconstitution)."""

    def test_direct_constructor_skips_validation(self) -> None:
        """Direct constructor should not validate, for repository reconstitution."""
        now = datetime.now(UTC)
        vote = Vote(
            id=uuid.uuid4(),
            topic_id=uuid.uuid4(),
            fingerprint_id="",
            value=99,
            created_at=now,
            updated_at=now,
        )

        assert vote.fingerprint_id == ""
        assert vote.value == 99
