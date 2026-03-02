"""Get poll results use case."""

import uuid
from dataclasses import dataclass

from pulse_board.domain.exceptions import EntityNotFoundError
from pulse_board.domain.ports.poll_repository_port import PollRepository
from pulse_board.domain.ports.poll_response_repository_port import (
    PollResponseRepository,
)


@dataclass(frozen=True)
class PollOptionResult:
    """Vote count and percentage for a single poll option.

    Attributes:
        option_id: The UUID of the option.
        text: Display text of the option.
        count: Number of votes for this option.
        percentage: Percentage of total votes (0.0-100.0).
    """

    option_id: uuid.UUID
    text: str
    count: int
    percentage: float


@dataclass(frozen=True)
class PollResultsResult:
    """Aggregated results for a poll.

    Attributes:
        poll_id: The UUID of the poll.
        question: The poll question text.
        total_votes: Total number of responses.
        options: Per-option results in original order.
    """

    poll_id: uuid.UUID
    question: str
    total_votes: int
    options: list[PollOptionResult]


class GetPollResultsUseCase:
    """Use case for retrieving aggregated poll results."""

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
    ) -> PollResultsResult:
        """Get aggregated results for a poll.

        Args:
            poll_id: The UUID of the poll.

        Returns:
            PollResultsResult with per-option counts and
            percentages.

        Raises:
            EntityNotFoundError: If the poll does not exist.
        """
        poll = self._poll_repo.get_by_id(poll_id)
        if poll is None:
            raise EntityNotFoundError(f"Poll with id '{poll_id}' not found")

        counts = self._poll_response_repo.count_all_by_poll(poll_id)
        total_votes = sum(counts.values())

        option_results = []
        for opt in poll.options:
            count = counts.get(opt.id, 0)
            percentage = (
                round(count / total_votes * 100, 1)
                if total_votes > 0
                else 0.0
            )
            option_results.append(
                PollOptionResult(
                    option_id=opt.id,
                    text=opt.text,
                    count=count,
                    percentage=percentage,
                )
            )

        return PollResultsResult(
            poll_id=poll.id,
            question=poll.question,
            total_votes=total_votes,
            options=option_results,
        )
