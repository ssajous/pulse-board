"""Get present state use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.application.use_cases.get_poll_results import (
    GetPollResultsUseCase,
    PollOptionResult,
)
from pulse_board.domain.exceptions import EventNotFoundError
from pulse_board.domain.ports.event_repository_port import EventRepository
from pulse_board.domain.ports.participant_counter_port import ParticipantCounter
from pulse_board.domain.ports.poll_repository_port import PollRepository
from pulse_board.domain.ports.poll_response_repository_port import (
    PollResponseRepository,
)
from pulse_board.domain.ports.topic_repository_port import TopicRepository


@dataclass(frozen=True)
class PresentActivePoll:
    """Active poll summary for the present view."""

    poll_id: uuid.UUID
    question: str
    total_votes: int
    options: list[PollOptionResult]


@dataclass(frozen=True)
class PresentTopicSummary:
    """Topic summary for the present view."""

    id: uuid.UUID
    content: str
    score: int
    created_at: datetime


@dataclass(frozen=True)
class PresentStateResult:
    """Full present mode state for an event."""

    event_id: uuid.UUID
    event_title: str
    event_code: str
    active_poll: PresentActivePoll | None
    top_topics: list[PresentTopicSummary]
    participant_count: int


class GetPresentStateUseCase:
    """Retrieve projection-ready state for an event."""

    TOP_TOPICS_LIMIT = 10

    def __init__(
        self,
        event_repository: EventRepository,
        poll_repository: PollRepository,
        poll_response_repository: PollResponseRepository,
        topic_repository: TopicRepository,
        participant_counter: ParticipantCounter,
    ) -> None:
        self._event_repo = event_repository
        self._poll_repo = poll_repository
        self._poll_response_repo = poll_response_repository
        self._topic_repo = topic_repository
        self._participant_counter = participant_counter

    def execute(self, event_id: uuid.UUID) -> PresentStateResult:
        """Get the present mode state for an event.

        Args:
            event_id: The UUID of the event.

        Returns:
            PresentStateResult with current poll, top topics, and participant count.

        Raises:
            EventNotFoundError: If the event does not exist.
        """
        event = self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event with id '{event_id}' not found")

        # Active poll with results
        active_poll: PresentActivePoll | None = None
        active_poll_entity = self._poll_repo.find_active_by_event(event_id)
        if active_poll_entity is not None:
            results = GetPollResultsUseCase(
                poll_repository=self._poll_repo,
                poll_response_repository=self._poll_response_repo,
            ).execute(active_poll_entity.id)
            active_poll = PresentActivePoll(
                poll_id=results.poll_id,
                question=results.question,
                total_votes=results.total_votes,
                options=results.options,
            )

        # Top topics
        all_topics = self._topic_repo.list_by_event(event_id)
        sorted_topics = sorted(all_topics, key=lambda t: t.score, reverse=True)
        top_topics = [
            PresentTopicSummary(
                id=t.id,
                content=t.content,
                score=t.score,
                created_at=t.created_at,
            )
            for t in sorted_topics[: self.TOP_TOPICS_LIMIT]
        ]

        channel = f"event:{event.code}"
        participant_count = self._participant_counter.get_channel_count(channel)

        return PresentStateResult(
            event_id=event.id,
            event_title=event.title,
            event_code=event.code,
            active_poll=active_poll,
            top_topics=top_topics,
            participant_count=participant_count,
        )
