"""Create topic use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.ports.topic_repository_port import TopicRepository


@dataclass(frozen=True)
class CreateTopicResult:
    """Result of creating a topic."""

    id: uuid.UUID
    content: str
    score: int
    created_at: datetime


class CreateTopicUseCase:
    """Use case for creating a new topic."""

    def __init__(self, repository: TopicRepository) -> None:
        self._repository = repository

    def execute(self, content: str) -> CreateTopicResult:
        """Create a new topic.

        Args:
            content: The topic content text.

        Returns:
            CreateTopicResult with the created topic details.

        Raises:
            ValidationError: If content fails domain validation.
        """
        topic = Topic.create(content)
        saved = self._repository.create(topic)
        return CreateTopicResult(
            id=saved.id,
            content=saved.content,
            score=saved.score,
            created_at=saved.created_at,
        )
