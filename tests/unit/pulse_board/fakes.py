"""Shared fake implementations for testing."""

import uuid

from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.ports.topic_repository_port import TopicRepository


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
