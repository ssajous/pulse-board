"""Shared fake implementations for testing."""

import dataclasses
import uuid
from datetime import datetime
from typing import Any

from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.entities.vote import Vote
from pulse_board.domain.ports.event_publisher_port import EventPublisher
from pulse_board.domain.ports.topic_repository_port import TopicRepository
from pulse_board.domain.ports.vote_repository_port import VoteRepository


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

    async def publish_score_update(
        self,
        topic_id: uuid.UUID,
        score: int,
    ) -> None:
        """Record a score update event."""
        self.score_updates.append({"topic_id": topic_id, "score": score})

    async def publish_topic_censured(
        self,
        topic_id: uuid.UUID,
    ) -> None:
        """Record a topic censured event."""
        self.censured_events.append({"topic_id": topic_id})

    async def publish_new_topic(
        self,
        topic_id: uuid.UUID,
        content: str,
        score: int,
        created_at: datetime,
    ) -> None:
        """Record a new topic event."""
        self.new_topic_events.append(
            {
                "topic_id": topic_id,
                "content": content,
                "score": score,
                "created_at": created_at,
            }
        )
