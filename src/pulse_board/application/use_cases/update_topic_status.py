"""Update topic status use case."""

import uuid
from dataclasses import dataclass

from pulse_board.domain.entities.topic import TopicStatus
from pulse_board.domain.exceptions import TopicNotFoundError
from pulse_board.domain.ports.topic_repository_port import TopicRepository


@dataclass(frozen=True)
class UpdateTopicStatusResult:
    """Result of updating a topic's lifecycle status."""

    topic_id: uuid.UUID
    new_status: str


class UpdateTopicStatusUseCase:
    """Use case for changing a topic's status within an event."""

    def __init__(self, topic_repository: TopicRepository) -> None:
        self._topic_repo = topic_repository

    def execute(
        self,
        topic_id: uuid.UUID,
        new_status: TopicStatus,
        event_id: uuid.UUID,
    ) -> UpdateTopicStatusResult:
        """Change the lifecycle status of a topic.

        Args:
            topic_id: The unique identifier of the topic to update.
            new_status: The desired TopicStatus value.
            event_id: The event that must own the topic.

        Returns:
            UpdateTopicStatusResult with the topic id and new status.

        Raises:
            TopicNotFoundError: If no topic exists with the given id
                or the topic does not belong to the specified event.
        """
        topic = self._topic_repo.get_by_id(topic_id)
        if topic is None:
            raise TopicNotFoundError(f"Topic {topic_id} not found")
        if topic.event_id != event_id:
            raise TopicNotFoundError(
                f"Topic {topic_id} does not belong to event {event_id}"
            )
        self._topic_repo.update_status(topic_id, new_status)
        return UpdateTopicStatusResult(
            topic_id=topic_id,
            new_status=new_status.value,
        )
