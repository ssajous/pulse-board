"""Check event creator use case."""

import uuid
from dataclasses import dataclass

from pulse_board.domain.exceptions import EventNotFoundError
from pulse_board.domain.ports.event_repository_port import (
    EventRepository,
)


@dataclass(frozen=True)
class CheckEventCreatorResult:
    """Result of checking whether a token matches the event creator."""

    is_creator: bool


class CheckEventCreatorUseCase:
    """Use case for verifying if a participant is the event creator."""

    def __init__(
        self,
        event_repository: EventRepository,
    ) -> None:
        self._event_repo = event_repository

    def execute(
        self,
        event_id: uuid.UUID,
        creator_token: str,
    ) -> CheckEventCreatorResult:
        """Check if the given token matches the event creator token.

        Args:
            event_id: The unique identifier of the event.
            creator_token: The server-issued creator token to check.

        Returns:
            CheckEventCreatorResult indicating whether the token
            belongs to the event creator.

        Raises:
            EventNotFoundError: If no event exists with the
                given id.
        """
        event = self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")

        is_creator = (
            event.creator_token is not None
            and event.creator_token == creator_token
        )
        return CheckEventCreatorResult(is_creator=is_creator)
