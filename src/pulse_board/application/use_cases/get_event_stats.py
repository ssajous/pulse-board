"""Get event stats use case."""

import uuid
from dataclasses import dataclass

from pulse_board.domain.entities.topic import TopicStatus
from pulse_board.domain.exceptions import EventNotFoundError
from pulse_board.domain.ports.event_repository_port import EventRepository
from pulse_board.domain.ports.participant_counter_port import ParticipantCounter
from pulse_board.domain.ports.poll_repository_port import PollRepository
from pulse_board.domain.ports.poll_response_repository_port import (
    PollResponseRepository,
)
from pulse_board.domain.ports.topic_repository_port import TopicRepository


@dataclass(frozen=True)
class EventStatsResult:
    """Aggregated statistics for a live event."""

    participant_count: int
    topic_count: int
    active_topic_count: int
    poll_count: int
    has_active_poll: bool
    total_poll_responses: int


class GetEventStatsUseCase:
    """Use case for fetching aggregated stats for a host dashboard."""

    def __init__(
        self,
        event_repository: EventRepository,
        topic_repository: TopicRepository,
        poll_repository: PollRepository,
        poll_response_repository: PollResponseRepository,
        participant_counter: ParticipantCounter,
    ) -> None:
        self._event_repo = event_repository
        self._topic_repo = topic_repository
        self._poll_repo = poll_repository
        self._poll_response_repo = poll_response_repository
        self._participant_counter = participant_counter

    def execute(self, event_id: uuid.UUID) -> EventStatsResult:
        """Compute aggregated statistics for an event.

        Args:
            event_id: The unique identifier of the event.

        Returns:
            EventStatsResult containing participant count, topic
            counts, poll counts, and total poll responses.

        Raises:
            EventNotFoundError: If no event exists with the given id.
        """
        event = self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")

        channel = f"event:{event.code}"
        participant_count = self._participant_counter.get_channel_count(channel)
        topic_count = self._topic_repo.count_by_event(event_id)
        active_topic_count = self._topic_repo.count_by_event_and_status(
            event_id, TopicStatus.ACTIVE
        )
        polls = self._poll_repo.list_by_event(event_id)
        poll_count = len(polls)
        has_active_poll = any(p.is_active for p in polls)
        total_poll_responses = sum(
            len(self._poll_response_repo.list_by_poll(p.id)) for p in polls
        )

        return EventStatsResult(
            participant_count=participant_count,
            topic_count=topic_count,
            active_topic_count=active_topic_count,
            poll_count=poll_count,
            has_active_poll=has_active_poll,
            total_poll_responses=total_poll_responses,
        )
