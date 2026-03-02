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
        option_id: The UUID of the selected option.
        created_at: When the response was submitted.
    """

    id: uuid.UUID
    poll_id: uuid.UUID
    option_id: uuid.UUID
    created_at: datetime


class SubmitPollResponseUseCase:
    """Use case for submitting a response to a poll.

    Validates the poll is active, the option exists, and
    the participant has not already responded before
    persisting the response.
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
        option_id: uuid.UUID,
    ) -> SubmitPollResponseResult:
        """Submit a response to a poll.

        Args:
            poll_id: The UUID of the poll to respond to.
            fingerprint_id: Identifier for the respondent.
            option_id: The UUID of the selected option.

        Returns:
            SubmitPollResponseResult with the response details.

        Raises:
            EntityNotFoundError: If the poll does not exist.
            PollNotActiveError: If the poll is not active.
            InvalidPollOptionError: If the option does not
                belong to the poll.
            DuplicateResponseError: If the participant has
                already responded to this poll.
        """
        poll = self._poll_repo.get_by_id(poll_id)
        if poll is None:
            raise EntityNotFoundError(f"Poll with id '{poll_id}' not found")

        if not poll.is_active:
            raise PollNotActiveError("Cannot respond to an inactive poll")

        valid_option_ids = {opt.id for opt in poll.options}
        if option_id not in valid_option_ids:
            raise InvalidPollOptionError(
                f"Option '{option_id}' does not belong to poll '{poll_id}'"
            )

        existing = self._poll_response_repo.find_by_poll_and_fingerprint(
            poll_id,
            fingerprint_id,
        )
        if existing is not None:
            raise DuplicateResponseError("You have already responded to this poll")

        response = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id=fingerprint_id,
            option_id=option_id,
        )
        saved = self._poll_response_repo.create(response)

        return SubmitPollResponseResult(
            id=saved.id,
            poll_id=saved.poll_id,
            option_id=saved.option_id,
            created_at=saved.created_at,
        )
