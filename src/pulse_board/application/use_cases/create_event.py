"""Create event use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.ports.event_repository_port import EventRepository
from pulse_board.domain.services.join_code_generator import (
    JoinCodeGenerator,
)


@dataclass(frozen=True)
class CreateEventResult:
    """Result of creating an event."""

    id: uuid.UUID
    title: str
    code: str
    description: str | None
    start_date: datetime | None
    end_date: datetime | None
    status: EventStatus
    created_at: datetime
    creator_fingerprint: str | None
    creator_token: str | None


class CreateEventUseCase:
    """Use case for creating a new event session."""

    def __init__(
        self,
        event_repository: EventRepository,
        code_generator: JoinCodeGenerator,
    ) -> None:
        self._event_repo = event_repository
        self._code_generator = code_generator

    def execute(
        self,
        title: str,
        *,
        description: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        creator_fingerprint: str | None = None,
    ) -> CreateEventResult:
        """Create a new event with a generated join code.

        Args:
            title: The event title (max 200 characters).
            description: Optional event description.
            start_date: Optional scheduled start time.
            end_date: Optional scheduled end time.
            creator_fingerprint: Optional browser fingerprint
                of the event creator for admin identification.

        Returns:
            CreateEventResult with the created event details.

        Raises:
            ValidationError: If title fails domain validation.
            CodeGenerationError: If a unique code cannot be
                generated.
        """
        code = self._code_generator.generate(self._event_repo.is_code_unique)
        event = Event.create(
            title=title,
            code=code,
            description=description,
            start_date=start_date,
            end_date=end_date,
            creator_fingerprint=creator_fingerprint,
        )
        saved = self._event_repo.create(event)
        return CreateEventResult(
            id=saved.id,
            title=saved.title,
            code=saved.code,
            description=saved.description,
            start_date=saved.start_date,
            end_date=saved.end_date,
            status=saved.status,
            created_at=saved.created_at,
            creator_fingerprint=saved.creator_fingerprint,
            creator_token=saved.creator_token,
        )
