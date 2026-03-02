"""Shared fake implementations for testing."""

import dataclasses
import uuid
from datetime import datetime
from typing import Any

from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.entities.vote import Vote
from pulse_board.domain.ports.event_publisher_port import EventPublisher
from pulse_board.domain.ports.event_repository_port import EventRepository
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


class FakeEventPublisher(EventPublisher):
    """In-memory event publisher that records published events for assertions."""

    def __init__(self) -> None:
        self.score_updates: list[dict[str, Any]] = []
        self.censured_events: list[dict[str, Any]] = []
        self.new_topic_events: list[dict[str, Any]] = []
        self.channel_score_updates: list[dict[str, Any]] = []
        self.channel_censured_events: list[dict[str, Any]] = []
        self.channel_new_topic_events: list[dict[str, Any]] = []

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
