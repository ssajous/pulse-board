"""List topics use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.ports.topic_repository_port import (
    TopicRepository,
)


@dataclass(frozen=True)
class TopicSummary:
    """Summary of a single topic for listing."""

    id: uuid.UUID
    content: str
    score: int
    created_at: datetime
    status: str = "active"


class ListTopicsUseCase:
    """Use case for listing active topics."""

    def __init__(self, repository: TopicRepository) -> None:
        self._repository = repository

    def execute(self) -> list[TopicSummary]:
        """List active topics sorted by popularity.

        Returns:
            List of TopicSummary sorted by score desc,
            then created_at desc.
        """
        topics = self._repository.list_active()
        sorted_topics = sorted(
            topics,
            key=lambda t: (t.score, t.created_at),
            reverse=True,
        )
        return [
            TopicSummary(
                id=t.id,
                content=t.content,
                score=t.score,
                created_at=t.created_at,
            )
            for t in sorted_topics
        ]
