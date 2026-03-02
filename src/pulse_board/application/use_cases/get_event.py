"""Get event use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.event import EventStatus
from pulse_board.domain.exceptions import EventNotFoundError
from pulse_board.domain.ports.event_repository_port import EventRepository


@dataclass(frozen=True)
class GetEventResult:
    """Result of getting an event."""

    id: uuid.UUID
    title: str
    code: str
    description: str | None
    start_date: datetime | None
    end_date: datetime | None
    status: EventStatus
    created_at: datetime


class GetEventUseCase:
    """Use case for retrieving a single event by ID."""

    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repo = event_repository

    def execute(self, event_id: uuid.UUID) -> GetEventResult:
        """Retrieve an event by ID.

        Args:
            event_id: The UUID of the event to retrieve.

        Returns:
            GetEventResult with the event details.

        Raises:
            EventNotFoundError: If no event matches the ID.
        """
        event = self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event with id '{event_id}' not found")
        return GetEventResult(
            id=event.id,
            title=event.title,
            code=event.code,
            description=event.description,
            start_date=event.start_date,
            end_date=event.end_date,
            status=event.status,
            created_at=event.created_at,
        )
