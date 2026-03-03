"""Close event use case."""

import uuid
from dataclasses import dataclass

from pulse_board.domain.entities.event import EventStatus
from pulse_board.domain.exceptions import EventNotFoundError
from pulse_board.domain.ports.event_repository_port import EventRepository


@dataclass(frozen=True)
class CloseEventResult:
    """Result of closing a live event session."""

    event_id: uuid.UUID
    status: str


class CloseEventUseCase:
    """Use case for closing an active event session."""

    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repo = event_repository

    def execute(self, event_id: uuid.UUID) -> CloseEventResult:
        """Close a live event session.

        Idempotent — if the event is already closed the result is
        returned without performing an additional update.

        Args:
            event_id: The unique identifier of the event to close.

        Returns:
            CloseEventResult with the event id and final status.

        Raises:
            EventNotFoundError: If no event exists with the given id.
        """
        event = self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")
        if event.status == EventStatus.CLOSED:
            return CloseEventResult(
                event_id=event_id,
                status=EventStatus.CLOSED.value,
            )
        self._event_repo.update_status(event_id, EventStatus.CLOSED)
        return CloseEventResult(
            event_id=event_id,
            status=EventStatus.CLOSED.value,
        )
