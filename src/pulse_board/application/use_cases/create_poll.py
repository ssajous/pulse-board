"""Create poll use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.exceptions import EventNotFoundError
from pulse_board.domain.ports.event_repository_port import (
    EventRepository,
)
from pulse_board.domain.ports.poll_repository_port import PollRepository


@dataclass(frozen=True)
class CreatePollResult:
    """Result of creating a poll.

    Attributes:
        id: The UUID of the created poll.
        event_id: The UUID of the parent event.
        question: The poll question text.
        poll_type: The type of poll.
        options: List of option dicts with id and text.
        is_active: Whether the poll is currently active.
        created_at: When the poll was created.
    """

    id: uuid.UUID
    event_id: uuid.UUID
    question: str
    poll_type: str
    options: list[dict[str, str]]
    is_active: bool
    created_at: datetime


class CreatePollUseCase:
    """Use case for creating a new poll within an event."""

    def __init__(
        self,
        poll_repository: PollRepository,
        event_repository: EventRepository,
    ) -> None:
        self._poll_repo = poll_repository
        self._event_repo = event_repository

    def execute(
        self,
        event_id: uuid.UUID,
        question: str,
        option_texts: list[str],
        poll_type: str = "multiple_choice",
    ) -> CreatePollResult:
        """Create a new poll for an event.

        Args:
            event_id: The UUID of the parent event.
            question: The poll question text (1-500 chars).
            option_texts: List of option display texts (2-10 for
                multiple_choice; ignored for rating and open_text).
            poll_type: The type of poll. Defaults to
                ``multiple_choice``.

        Returns:
            CreatePollResult with the created poll details.

        Raises:
            EventNotFoundError: If the event does not exist.
            ValidationError: If question or options fail
                domain validation.
        """
        event = self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event with id '{event_id}' not found")

        poll = Poll.create(
            event_id=event_id,
            question=question,
            option_texts=option_texts,
            poll_type=poll_type,
        )
        saved = self._poll_repo.create(poll)

        return CreatePollResult(
            id=saved.id,
            event_id=saved.event_id,
            question=saved.question,
            poll_type=saved.poll_type,
            options=[opt.to_dict() for opt in saved.options],
            is_active=saved.is_active,
            created_at=saved.created_at,
        )
