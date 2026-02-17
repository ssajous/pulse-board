"""Cast vote use case."""

import uuid
from dataclasses import dataclass

from pulse_board.domain.events import DomainEvent, TopicCensuredEvent
from pulse_board.domain.exceptions import EntityNotFoundError
from pulse_board.domain.ports.topic_repository_port import TopicRepository
from pulse_board.domain.ports.vote_repository_port import VoteRepository
from pulse_board.domain.services.voting_service import (
    VoteCancelled,
    VoteCreated,
    VoteToggled,
    VotingService,
    is_censured,
)


@dataclass(frozen=True)
class CastVoteResult:
    """Result of casting a vote.

    Attributes:
        topic_id: The UUID of the topic that was voted on.
        new_score: The topic's score after the vote action.
        vote_status: One of "created", "toggled", or "cancelled".
        vote_direction: The final vote direction (1 or -1),
            or None if the vote was cancelled.
        censured: Whether the topic is now censured.
        event: A TopicCensuredEvent if the topic became censured,
            otherwise None.
    """

    topic_id: uuid.UUID
    new_score: int
    vote_status: str
    vote_direction: int | None
    censured: bool
    event: DomainEvent | None


class CastVoteUseCase:
    """Use case for casting a vote on a topic.

    Orchestrates the voting flow: validates the topic exists,
    delegates business logic to the VotingService, persists
    the result, and checks for censure.
    """

    def __init__(
        self,
        vote_repo: VoteRepository,
        topic_repo: TopicRepository,
        voting_service: VotingService,
    ) -> None:
        self._vote_repo = vote_repo
        self._topic_repo = topic_repo
        self._voting_service = voting_service

    def execute(
        self,
        topic_id: uuid.UUID,
        fingerprint_id: str,
        direction: int,
    ) -> CastVoteResult:
        """Cast a vote on a topic.

        Args:
            topic_id: The UUID of the topic to vote on.
            fingerprint_id: A non-empty string identifying
                the voter (browser fingerprint).
            direction: The vote direction, +1 (upvote) or
                -1 (downvote).

        Returns:
            CastVoteResult describing the outcome of the vote.

        Raises:
            EntityNotFoundError: If the topic does not exist.
            ValidationError: If the direction or fingerprint
                is invalid.
        """
        topic = self._topic_repo.get_by_id(topic_id)
        if topic is None:
            raise EntityNotFoundError("Topic not found")

        existing_vote = self._vote_repo.find_by_topic_and_fingerprint(
            topic_id, fingerprint_id
        )

        action = self._voting_service.process_vote(
            existing_vote=existing_vote,
            topic_id=topic_id,
            fingerprint_id=fingerprint_id,
            direction=direction,
        )

        vote_status, vote_direction = self._persist_action(action)

        updated_topic = self._topic_repo.update_score(topic_id, action.score_delta)
        new_score = updated_topic.score if updated_topic is not None else 0

        censured = is_censured(new_score)
        event: DomainEvent | None = None
        if censured:
            event = TopicCensuredEvent(
                topic_id=topic_id,
                final_score=new_score,
            )

        return CastVoteResult(
            topic_id=topic_id,
            new_score=new_score,
            vote_status=vote_status,
            vote_direction=vote_direction,
            censured=censured,
            event=event,
        )

    def _persist_action(
        self,
        action: VoteCreated | VoteToggled | VoteCancelled,
    ) -> tuple[str, int | None]:
        """Persist the vote action and return status metadata.

        Args:
            action: The VoteAction from the VotingService.

        Returns:
            A tuple of (vote_status, vote_direction).
        """
        if isinstance(action, VoteCreated):
            self._vote_repo.save(action.vote)
            return "created", action.vote.value

        if isinstance(action, VoteToggled):
            self._vote_repo.save(action.vote)
            return "toggled", action.vote.value

        self._vote_repo.delete(action.vote_id)
        return "cancelled", None
