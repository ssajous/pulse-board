"""List event topics use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.ports.topic_repository_port import TopicRepository


@dataclass(frozen=True)
class EventTopicSummary:
    """Summary of a topic within an event."""

    id: uuid.UUID
    content: str
    score: int
    created_at: datetime


class ListEventTopicsUseCase:
    """Use case for listing topics belonging to an event."""

    def __init__(self, repository: TopicRepository) -> None:
        self._repository = repository

    def execute(self, event_id: uuid.UUID) -> list[EventTopicSummary]:
        """List topics for a specific event, sorted by popularity.

        Args:
            event_id: The UUID of the event whose topics to list.

        Returns:
            List of EventTopicSummary sorted by score desc,
            then created_at desc.
        """
        topics = self._repository.list_by_event(event_id)
        sorted_topics = sorted(
            topics,
            key=lambda t: (t.score, t.created_at),
            reverse=True,
        )
        return [
            EventTopicSummary(
                id=t.id,
                content=t.content,
                score=t.score,
                created_at=t.created_at,
            )
            for t in sorted_topics
        ]
