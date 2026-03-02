"""Activate/deactivate poll use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.exceptions import EntityNotFoundError
from pulse_board.domain.ports.poll_repository_port import PollRepository


@dataclass(frozen=True)
class ActivatePollResult:
    """Result of activating or deactivating a poll.

    Attributes:
        id: The UUID of the poll.
        event_id: The UUID of the parent event.
        question: The poll question text.
        is_active: Whether the poll is now active.
        options: List of option dicts with id and text.
        created_at: When the poll was created.
    """

    id: uuid.UUID
    event_id: uuid.UUID
    question: str
    is_active: bool
    options: list[dict[str, str]]
    created_at: datetime


class ActivatePollUseCase:
    """Use case for activating or deactivating a poll.

    When activating a poll, any currently active poll for
    the same event is deactivated first to ensure only one
    poll is active at a time per event.
    """

    def __init__(
        self,
        poll_repository: PollRepository,
    ) -> None:
        self._poll_repo = poll_repository

    def execute(
        self,
        poll_id: uuid.UUID,
        *,
        activate: bool = True,
    ) -> ActivatePollResult:
        """Activate or deactivate a poll.

        Args:
            poll_id: The UUID of the poll to update.
            activate: True to activate, False to deactivate.

        Returns:
            ActivatePollResult with the updated poll state.

        Raises:
            EntityNotFoundError: If the poll does not exist.
        """
        poll = self._poll_repo.get_by_id(poll_id)
        if poll is None:
            raise EntityNotFoundError(f"Poll with id '{poll_id}' not found")

        if activate:
            current_active = self._poll_repo.find_active_by_event(
                poll.event_id,
            )
            if current_active and current_active.id != poll_id:
                self._poll_repo.update_active_status(
                    current_active.id,
                    False,
                )

        updated = self._poll_repo.update_active_status(
            poll_id,
            activate,
        )
        if updated is None:
            raise EntityNotFoundError(f"Poll with id '{poll_id}' not found")

        return ActivatePollResult(
            id=updated.id,
            event_id=updated.event_id,
            question=updated.question,
            is_active=updated.is_active,
            options=[{"id": str(opt.id), "text": opt.text} for opt in updated.options],
            created_at=updated.created_at,
        )
