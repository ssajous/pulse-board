"""Join event use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.event import EventStatus
from pulse_board.domain.exceptions import (
    EventNotActiveError,
    EventNotFoundError,
)
from pulse_board.domain.ports.event_repository_port import EventRepository


@dataclass(frozen=True)
class JoinEventResult:
    """Result of joining an event."""

    id: uuid.UUID
    title: str
    code: str
    description: str | None
    status: EventStatus
    created_at: datetime


class JoinEventUseCase:
    """Use case for joining an event via join code."""

    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repo = event_repository

    def execute(self, code: str) -> JoinEventResult:
        """Look up an active event by its join code.

        Args:
            code: The join code string to look up.

        Returns:
            JoinEventResult with the matched event details.

        Raises:
            EventNotFoundError: If no event matches the code.
            EventNotActiveError: If the matched event is not
                active.
        """
        event = self._event_repo.get_by_code(code)
        if event is None:
            raise EventNotFoundError(f"No event found with code '{code}'")
        if event.status != EventStatus.ACTIVE:
            raise EventNotActiveError(f"Event '{event.title}' is no longer active")
        return JoinEventResult(
            id=event.id,
            title=event.title,
            code=event.code,
            description=event.description,
            status=event.status,
            created_at=event.created_at,
        )
