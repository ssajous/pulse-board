"""Submit poll response use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.domain.exceptions import (
    DuplicateResponseError,
    EntityNotFoundError,
    InvalidPollOptionError,
    PollNotActiveError,
    ValidationError,
)
from pulse_board.domain.ports.poll_repository_port import PollRepository
from pulse_board.domain.ports.poll_response_repository_port import (
    PollResponseRepository,
)


@dataclass(frozen=True)
class SubmitPollResponseResult:
    """Result of submitting a poll response.

    Attributes:
        id: The UUID of the created response.
        poll_id: The UUID of the poll.
        event_id: The UUID of the poll's parent event.
        option_id: The UUID of the selected option, or None for
            rating/open-text responses.
        poll_type: The type of the poll that was responded to.
        created_at: When the response was submitted.
    """

    id: uuid.UUID
    poll_id: uuid.UUID
    event_id: uuid.UUID
    option_id: uuid.UUID | None
    poll_type: str
    created_at: datetime


class SubmitPollResponseUseCase:
    """Use case for submitting a response to a poll.

    Validates the poll is active, the response value is appropriate
    for the poll type, and the participant has not already responded
    before persisting the response.
    """

    def __init__(
        self,
        poll_repository: PollRepository,
        poll_response_repository: PollResponseRepository,
    ) -> None:
        self._poll_repo = poll_repository
        self._poll_response_repo = poll_response_repository

    def execute(
        self,
        poll_id: uuid.UUID,
        fingerprint_id: str,
        option_id: uuid.UUID | None = None,
        response_value: int | str | None = None,
    ) -> SubmitPollResponseResult:
        """Submit a response to a poll.

        Dispatches to the appropriate PollResponse factory based on the
        poll type:
        - ``rating``: uses ``response_value`` as an integer rating (1-5)
        - ``open_text``: uses ``response_value`` as a free-form string
        - ``multiple_choice``: uses ``option_id`` to select an option

        Args:
            poll_id: The UUID of the poll to respond to.
            fingerprint_id: Identifier for the respondent.
            option_id: UUID of the selected option (multiple_choice only).
            response_value: Rating (int) or text (str) for rating/open_text
                polls respectively.

        Returns:
            SubmitPollResponseResult with the response details.

        Raises:
            EntityNotFoundError: If the poll does not exist.
            PollNotActiveError: If the poll is not active.
            InvalidPollOptionError: If the option does not belong to the
                poll (multiple_choice only).
            ValidationError: If response_value fails domain validation.
            DuplicateResponseError: If the participant has already
                responded to this poll.
        """
        poll = self._poll_repo.get_by_id(poll_id)
        if poll is None:
            raise EntityNotFoundError(f"Poll with id '{poll_id}' not found")

        if not poll.is_active:
            raise PollNotActiveError("Cannot respond to an inactive poll")

        existing = self._poll_response_repo.find_by_poll_and_fingerprint(
            poll_id,
            fingerprint_id,
        )
        if existing is not None:
            raise DuplicateResponseError("You have already responded to this poll")

        if poll.poll_type == "rating":
            if response_value is None:
                raise ValidationError("response_value is required for rating polls")
            response = PollResponse.create_rating(
                poll_id=poll_id,
                fingerprint_id=fingerprint_id,
                rating=int(response_value),
            )
        elif poll.poll_type == "open_text":
            if response_value is None:
                raise ValidationError("response_value is required for open text polls")
            response = PollResponse.create_open_text(
                poll_id=poll_id,
                fingerprint_id=fingerprint_id,
                text=str(response_value),
            )
        else:
            if option_id is None:
                raise ValidationError("option_id is required for multiple choice polls")
            valid_option_ids = {opt.id for opt in poll.options}
            if option_id not in valid_option_ids:
                raise InvalidPollOptionError(
                    f"Option '{option_id}' does not belong to poll '{poll_id}'"
                )
            response = PollResponse.create(
                poll_id=poll_id,
                fingerprint_id=fingerprint_id,
                option_id=option_id,
            )

        saved = self._poll_response_repo.create(response)

        return SubmitPollResponseResult(
            id=saved.id,
            poll_id=saved.poll_id,
            event_id=poll.event_id,
            option_id=saved.option_id,
            poll_type=poll.poll_type,
            created_at=saved.created_at,
        )
