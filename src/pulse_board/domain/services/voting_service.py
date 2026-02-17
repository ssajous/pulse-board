"""Voting domain service — pure business logic for vote processing.

This service encapsulates all vote-related business rules as pure
functions. It has no side effects, no repository calls, and no
framework dependencies. It receives inputs and returns
discriminated union results describing the action taken.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from pulse_board.domain.entities.vote import Vote

CENSURE_THRESHOLD = -5


@dataclass(frozen=True)
class VoteCreated:
    """Result when a new vote is cast on a topic.

    Attributes:
        vote: The newly created Vote entity.
        score_delta: The change to apply to the topic score
            (+1 for upvote, -1 for downvote).
    """

    vote: Vote
    score_delta: int


@dataclass(frozen=True)
class VoteToggled:
    """Result when an existing vote is flipped to the opposite direction.

    Attributes:
        vote: The toggled Vote entity (value already flipped).
        score_delta: The change to apply to the topic score
            (+2 for down-to-up, -2 for up-to-down).
    """

    vote: Vote
    score_delta: int


@dataclass(frozen=True)
class VoteCancelled:
    """Result when an existing vote is removed (same direction click).

    Attributes:
        vote_id: The UUID of the cancelled vote.
        score_delta: The change to apply to the topic score
            (reverses the old value: -1 if was upvote, +1 if was
            downvote).
    """

    vote_id: uuid.UUID
    score_delta: int


VoteAction = VoteCreated | VoteToggled | VoteCancelled


class VotingService:
    """Pure domain service that processes vote actions.

    All methods are stateless and produce result types describing
    what happened. The caller (use case layer) is responsible for
    persisting the changes and updating topic scores.
    """

    def process_vote(
        self,
        existing_vote: Vote | None,
        topic_id: uuid.UUID,
        fingerprint_id: str,
        direction: int,
    ) -> VoteAction:
        """Determine and execute the vote action for a given input.

        Business rules:
        - No existing vote: create a new vote.
        - Existing vote, same direction: cancel the vote.
        - Existing vote, different direction: toggle the vote.

        Args:
            existing_vote: The voter's current vote on the topic,
                or None if they haven't voted yet.
            topic_id: The UUID of the topic being voted on.
            fingerprint_id: A non-empty string identifying the
                voter (browser fingerprint).
            direction: The requested vote direction, must be
                +1 (upvote) or -1 (downvote).

        Returns:
            A VoteAction discriminated union describing the
            action taken and the resulting score delta.
        """
        if existing_vote is None:
            return self._create_vote(topic_id, fingerprint_id, direction)

        if existing_vote.value == direction:
            return self._cancel_vote(existing_vote)

        return self._toggle_vote(existing_vote)

    def _create_vote(
        self,
        topic_id: uuid.UUID,
        fingerprint_id: str,
        direction: int,
    ) -> VoteCreated:
        """Create a brand-new vote.

        Args:
            topic_id: The UUID of the topic being voted on.
            fingerprint_id: Voter identifier string.
            direction: The vote direction (+1 or -1).

        Returns:
            VoteCreated with the new vote and its score delta.
        """
        vote = Vote.create(
            topic_id=topic_id,
            fingerprint_id=fingerprint_id,
            value=direction,
        )
        return VoteCreated(vote=vote, score_delta=direction)

    def _cancel_vote(
        self,
        existing_vote: Vote,
    ) -> VoteCancelled:
        """Cancel an existing vote (same direction clicked again).

        Args:
            existing_vote: The vote to cancel.

        Returns:
            VoteCancelled with the vote id and reversed score
            delta.
        """
        return VoteCancelled(
            vote_id=existing_vote.id,
            score_delta=-existing_vote.value,
        )

    def _toggle_vote(
        self,
        existing_vote: Vote,
    ) -> VoteToggled:
        """Toggle an existing vote to the opposite direction.

        Args:
            existing_vote: The vote to toggle.

        Returns:
            VoteToggled with the toggled vote and the score
            delta (new_value - old_value).
        """
        old_value = existing_vote.value
        existing_vote.toggle()
        score_delta = existing_vote.value - old_value
        return VoteToggled(
            vote=existing_vote,
            score_delta=score_delta,
        )


def is_censured(score: int) -> bool:
    """Check whether a topic score is at or below the censure threshold.

    A topic is considered censured when its score drops to
    CENSURE_THRESHOLD (-5) or lower, indicating strong community
    disapproval.

    Args:
        score: The current score of a topic.

    Returns:
        True if the score is at or below the censure threshold.
    """
    return score <= CENSURE_THRESHOLD
