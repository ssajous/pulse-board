"""Create topic use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.event import EventStatus
from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.exceptions import (
    EventNotActiveError,
    EventNotFoundError,
)
from pulse_board.domain.ports.event_repository_port import EventRepository
from pulse_board.domain.ports.topic_repository_port import TopicRepository


@dataclass(frozen=True)
class CreateTopicResult:
    """Result of creating a topic."""

    id: uuid.UUID
    content: str
    score: int
    created_at: datetime
    event_id: uuid.UUID | None = None


class CreateTopicUseCase:
    """Use case for creating a new topic."""

    def __init__(
        self,
        repository: TopicRepository,
        event_repository: EventRepository | None = None,
    ) -> None:
        self._repository = repository
        self._event_repository = event_repository

    def execute(
        self,
        content: str,
        *,
        event_id: uuid.UUID | None = None,
    ) -> CreateTopicResult:
        """Create a new topic.

        Args:
            content: The topic content text.
            event_id: Optional UUID of the parent event.
                When provided, the event must exist and be
                active.

        Returns:
            CreateTopicResult with the created topic details.

        Raises:
            ValidationError: If content fails domain validation.
            EventNotFoundError: If event_id is given but the
                event does not exist or the event repository
                is not configured.
            EventNotActiveError: If the referenced event is
                not active.
        """
        if event_id is not None:
            self._validate_event(event_id)
        topic = Topic.create(content, event_id=event_id)
        saved = self._repository.create(topic)
        return CreateTopicResult(
            id=saved.id,
            content=saved.content,
            score=saved.score,
            created_at=saved.created_at,
            event_id=saved.event_id,
        )

    def _validate_event(self, event_id: uuid.UUID) -> None:
        """Validate that the referenced event exists and is active.

        Args:
            event_id: The UUID of the event to validate.

        Raises:
            EventNotFoundError: If the event repository is not
                configured or the event does not exist.
            EventNotActiveError: If the event is not active.
        """
        if self._event_repository is None:
            raise EventNotFoundError("Event repository not configured")
        event = self._event_repository.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event '{event_id}' not found")
        if event.status != EventStatus.ACTIVE:
            raise EventNotActiveError(f"Event '{event.title}' is not active")
