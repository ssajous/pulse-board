"""Shared fake implementations for testing."""

import dataclasses
import uuid
from collections import Counter
from datetime import datetime
from typing import Any

from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.entities.vote import Vote
from pulse_board.domain.ports.event_publisher_port import EventPublisher
from pulse_board.domain.ports.event_repository_port import EventRepository
from pulse_board.domain.ports.participant_counter_port import ParticipantCounter
from pulse_board.domain.ports.poll_repository_port import PollRepository
from pulse_board.domain.ports.poll_response_repository_port import (
    PollResponseRepository,
)
from pulse_board.domain.ports.topic_repository_port import TopicRepository
from pulse_board.domain.ports.vote_repository_port import VoteRepository


class FakeEventRepository(EventRepository):
    """In-memory event repository for unit tests."""

    def __init__(self) -> None:
        self._events: dict[uuid.UUID, Event] = {}

    def create(self, event: Event) -> Event:
        """Persist a new event."""
        self._events[event.id] = event
        return event

    def get_by_id(self, id: uuid.UUID) -> Event | None:
        """Look up an event by ID."""
        return self._events.get(id)

    def get_by_code(self, code: str) -> Event | None:
        """Look up an event by join code."""
        for event in self._events.values():
            if event.code == code:
                return event
        return None

    def list_active(self) -> list[Event]:
        """Return all active events."""
        return [e for e in self._events.values() if e.status == EventStatus.ACTIVE]

    def update_status(
        self,
        id: uuid.UUID,
        status: EventStatus,
    ) -> Event | None:
        """Update the status of an event."""
        event = self._events.get(id)
        if event is None:
            return None
        updated = dataclasses.replace(event, status=status)
        self._events[id] = updated
        return updated

    def is_code_unique(self, code: str) -> bool:
        """Check whether a join code is not yet in use."""
        return all(e.code != code for e in self._events.values())


class FakeTopicRepository(TopicRepository):
    """In-memory topic repository for unit tests."""

    def __init__(self) -> None:
        self._topics: dict[uuid.UUID, Topic] = {}

    def create(self, topic: Topic) -> Topic:
        self._topics[topic.id] = topic
        return topic

    def list_active(self) -> list[Topic]:
        # Intentionally returns UNSORTED to verify use case sorting
        return list(self._topics.values())

    def get_by_id(self, id: uuid.UUID) -> Topic | None:
        return self._topics.get(id)

    def delete(self, id: uuid.UUID) -> None:
        self._topics.pop(id, None)

    def list_by_event(self, event_id: uuid.UUID) -> list[Topic]:
        return [t for t in self._topics.values() if t.event_id == event_id]

    def update_score(self, id: uuid.UUID, delta: int) -> Topic | None:
        topic = self._topics.get(id)
        if topic is None:
            return None
        updated = dataclasses.replace(topic, score=topic.score + delta)
        self._topics[id] = updated
        return updated


class FakeVoteRepository(VoteRepository):
    """In-memory vote repository for unit tests."""

    def __init__(self) -> None:
        self._votes: dict[uuid.UUID, Vote] = {}

    def save(self, vote: Vote) -> Vote:
        self._votes[vote.id] = vote
        return vote

    def find_by_topic_and_fingerprint(
        self,
        topic_id: uuid.UUID,
        fingerprint_id: str,
    ) -> Vote | None:
        for vote in self._votes.values():
            if vote.topic_id == topic_id and vote.fingerprint_id == fingerprint_id:
                return vote
        return None

    def delete(self, vote_id: uuid.UUID) -> None:
        self._votes.pop(vote_id, None)

    def count_by_topic(self, topic_id: uuid.UUID) -> int:
        return sum(1 for v in self._votes.values() if v.topic_id == topic_id)


class FakePollRepository(PollRepository):
    """In-memory poll repository for unit tests."""

    def __init__(self) -> None:
        self._polls: dict[uuid.UUID, Poll] = {}

    def create(self, poll: Poll) -> Poll:
        """Persist a new poll."""
        self._polls[poll.id] = poll
        return poll

    def save(self, poll: Poll) -> Poll:
        """Persist a new or updated poll."""
        self._polls[poll.id] = poll
        return poll

    def get_by_id(self, id: uuid.UUID) -> Poll | None:
        """Look up a poll by ID."""
        return self._polls.get(id)

    def list_by_event(self, event_id: uuid.UUID) -> list[Poll]:
        """Return all polls belonging to a given event."""
        return [p for p in self._polls.values() if p.event_id == event_id]

    def update_active_status(
        self,
        id: uuid.UUID,
        is_active: bool,
    ) -> Poll | None:
        """Update the active status of a poll."""
        poll = self._polls.get(id)
        if poll is None:
            return None
        updated = dataclasses.replace(poll, is_active=is_active)
        self._polls[id] = updated
        return updated

    def find_active_by_event(
        self,
        event_id: uuid.UUID,
    ) -> Poll | None:
        """Find the currently active poll for an event."""
        for poll in self._polls.values():
            if poll.event_id == event_id and poll.is_active:
                return poll
        return None


class FakePollResponseRepository(PollResponseRepository):
    """In-memory poll response repository for unit tests."""

    def __init__(self) -> None:
        self._responses: dict[uuid.UUID, PollResponse] = {}

    def create(self, poll_response: PollResponse) -> PollResponse:
        """Persist a new poll response."""
        self._responses[poll_response.id] = poll_response
        return poll_response

    def list_by_poll(self, poll_id: uuid.UUID) -> list[PollResponse]:
        """Return all responses for a given poll."""
        return [r for r in self._responses.values() if r.poll_id == poll_id]

    def find_by_poll_and_fingerprint(
        self,
        poll_id: uuid.UUID,
        fingerprint_id: str,
    ) -> PollResponse | None:
        """Look up a response by poll and fingerprint."""
        for response in self._responses.values():
            if (
                response.poll_id == poll_id
                and response.fingerprint_id == fingerprint_id
            ):
                return response
        return None

    def count_by_option(
        self,
        poll_id: uuid.UUID,
        option_id: uuid.UUID,
    ) -> int:
        """Count responses for a specific option."""
        return sum(
            1
            for r in self._responses.values()
            if r.poll_id == poll_id and r.option_id == option_id
        )

    def count_all_by_poll(
        self,
        poll_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        """Count responses grouped by option for a poll."""
        counter: Counter[uuid.UUID] = Counter()
        for response in self._responses.values():
            if response.poll_id == poll_id:
                counter[response.option_id] += 1
        return dict(counter)


class FakeEventPublisher(EventPublisher):
    """In-memory event publisher that records published events for assertions."""

    def __init__(self) -> None:
        self.score_updates: list[dict[str, Any]] = []
        self.censured_events: list[dict[str, Any]] = []
        self.new_topic_events: list[dict[str, Any]] = []
        self.channel_score_updates: list[dict[str, Any]] = []
        self.channel_censured_events: list[dict[str, Any]] = []
        self.channel_new_topic_events: list[dict[str, Any]] = []
        self.channel_poll_activated: list[dict[str, Any]] = []
        self.channel_poll_deactivated: list[dict[str, Any]] = []
        self.channel_poll_results_updated: list[dict[str, Any]] = []

    async def publish_score_update(
        self,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        self.score_updates.append({"topic_id": topic_id, "score": score})

    async def publish_topic_censured(
        self,
        topic_id: uuid.UUID,
    ) -> None:
        self.censured_events.append({"topic_id": topic_id})

    async def publish_new_topic(
        self,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        self.new_topic_events.append(
            {
                "topic_id": topic_id,
                "content": content,
                "score": score,
                "created_at": created_at,
            }
        )

    async def publish_score_update_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        self.channel_score_updates.append(
            {
                "channel": channel,
                "topic_id": topic_id,
                "score": score,
            }
        )

    async def publish_topic_censured_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
    ) -> None:
        self.channel_censured_events.append({"channel": channel, "topic_id": topic_id})

    async def publish_new_topic_to_channel(
        self,
        channel: str,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        self.channel_new_topic_events.append(
            {
                "channel": channel,
                "topic_id": topic_id,
                "content": content,
                "score": score,
                "created_at": created_at,
            }
        )

    async def publish_poll_activated_to_channel(
        self,
        channel: str,
        poll_id: uuid.UUID,
        question: str,
        options: list[dict[str, str]],
    ) -> None:
        self.channel_poll_activated.append(
            {
                "channel": channel,
                "poll_id": poll_id,
                "question": question,
                "options": options,
            }
        )

    async def publish_poll_deactivated_to_channel(
        self,
        channel: str,
        poll_id: uuid.UUID,
    ) -> None:
        self.channel_poll_deactivated.append({"channel": channel, "poll_id": poll_id})

    async def publish_poll_results_updated_to_channel(
        self,
        channel: str,
        poll_id: uuid.UUID,
        results: list[dict[str, object]],
    ) -> None:
        self.channel_poll_results_updated.append(
            {
                "channel": channel,
                "poll_id": poll_id,
                "results": results,
            }
        )


class FakeParticipantCounter(ParticipantCounter):
    """In-memory participant counter for unit tests."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def set_count(self, channel: str, count: int) -> None:
        """Configure the count for a given channel."""
        self._counts[channel] = count

    def get_channel_count(self, channel: str) -> int:
        """Return the configured count, defaulting to 0."""
        return self._counts.get(channel, 0)
