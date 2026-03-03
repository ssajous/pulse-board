"""List event topics use case."""

import uuid

from pulse_board.application.use_cases.list_topics import TopicSummary
from pulse_board.domain.ports.topic_repository_port import TopicRepository


class ListEventTopicsUseCase:
    """Use case for listing topics belonging to an event."""

    def __init__(self, repository: TopicRepository) -> None:
        self._repository = repository

    def execute(self, event_id: uuid.UUID) -> list[TopicSummary]:
        """List topics for a specific event, sorted by popularity.

        Args:
            event_id: The UUID of the event whose topics to list.

        Returns:
            List of TopicSummary sorted by score desc,
            then created_at desc.
        """
        topics = self._repository.list_by_event(event_id)
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
                status=t.status.value,
            )
            for t in sorted_topics
        ]
