"""Get poll results use case."""

import math
import uuid
from dataclasses import dataclass
from datetime import datetime

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
    """Aggregated results for a multiple-choice poll.

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


@dataclass(frozen=True)
class RatingPollResultsResult:
    """Aggregated results for a rating poll.

    Attributes:
        poll_id: The UUID of the poll.
        question: The poll question text.
        total_votes: Total number of rating responses.
        average_rating: Average rating value, or None if no votes.
        distribution: Mapping from rating string ("1"-"5") to count.
    """

    poll_id: uuid.UUID
    question: str
    total_votes: int
    average_rating: float | None
    distribution: dict[str, int]


@dataclass(frozen=True)
class OpenTextResponseDTO:
    """A single open-text response for API output.

    Attributes:
        id: The UUID of the response.
        text: The submitted text content.
        created_at: When the response was submitted.
    """

    id: uuid.UUID
    text: str
    created_at: datetime


@dataclass(frozen=True)
class OpenTextPollResultsResult:
    """Paginated results for an open-text poll.

    Attributes:
        poll_id: The UUID of the poll.
        question: The poll question text.
        total_responses: Total number of text responses.
        responses: The current page of responses (newest first).
        page: The current page number (1-based).
        page_size: Number of responses per page.
        total_pages: Total number of pages.
    """

    poll_id: uuid.UUID
    question: str
    total_responses: int
    responses: list[OpenTextResponseDTO]
    page: int
    page_size: int
    total_pages: int


@dataclass(frozen=True)
class WordFrequencyDTO:
    """A single word frequency entry.

    Attributes:
        text: The normalized word or phrase.
        count: Number of times submitted.
    """

    text: str
    count: int


@dataclass(frozen=True)
class WordCloudPollResultsResult:
    """Aggregated results for a word cloud poll.

    Attributes:
        poll_id: The UUID of the poll.
        question: The poll question text.
        total_responses: Total number of submissions.
        words: Word frequency list, sorted by count descending.
    """

    poll_id: uuid.UUID
    question: str
    total_responses: int
    words: list[WordFrequencyDTO]


class GetPollResultsUseCase:
    """Use case for retrieving aggregated poll results.

    Returns a type-specific result based on the poll's poll_type:
    - ``multiple_choice``: ``PollResultsResult``
    - ``rating``: ``RatingPollResultsResult``
    - ``open_text``: ``OpenTextPollResultsResult``
    - ``word_cloud``: ``WordCloudPollResultsResult``
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
        page: int = 1,
        page_size: int = 20,
    ) -> (
        PollResultsResult
        | RatingPollResultsResult
        | OpenTextPollResultsResult
        | WordCloudPollResultsResult
    ):
        """Get aggregated results for a poll.

        Args:
            poll_id: The UUID of the poll.
            page: 1-based page number for open-text pagination.
                Defaults to 1.
            page_size: Page size for open-text pagination.
                Defaults to 20.

        Returns:
            A result dataclass appropriate to the poll type.

        Raises:
            EntityNotFoundError: If the poll does not exist.
        """
        poll = self._poll_repo.get_by_id(poll_id)
        if poll is None:
            raise EntityNotFoundError(f"Poll with id '{poll_id}' not found")

        if poll.poll_type == "rating":
            return self._build_rating_results(poll_id, poll.question)

        if poll.poll_type == "word_cloud":
            return self._build_word_cloud_results(poll_id, poll.question)

        if poll.poll_type == "open_text":
            return self._build_open_text_results(
                poll_id, poll.question, page, page_size
            )

        return self._build_multiple_choice_results(poll_id, poll.question, poll.options)

    def _build_rating_results(
        self,
        poll_id: uuid.UUID,
        question: str,
    ) -> RatingPollResultsResult:
        """Build rating poll results from the aggregate repository method."""
        avg, distribution = self._poll_response_repo.get_rating_aggregate(poll_id)
        total = sum(distribution.values())
        return RatingPollResultsResult(
            poll_id=poll_id,
            question=question,
            total_votes=total,
            average_rating=avg,
            distribution=distribution,
        )

    def _build_word_cloud_results(
        self,
        poll_id: uuid.UUID,
        question: str,
    ) -> WordCloudPollResultsResult:
        """Build word cloud results from frequency aggregation."""
        frequencies = self._poll_response_repo.get_word_cloud_frequencies(poll_id)
        words = [
            WordFrequencyDTO(text=text, count=count) for text, count in frequencies
        ]
        total = sum(w.count for w in words)
        return WordCloudPollResultsResult(
            poll_id=poll_id,
            question=question,
            total_responses=total,
            words=words,
        )

    def _build_open_text_results(
        self,
        poll_id: uuid.UUID,
        question: str,
        page: int,
        page_size: int,
    ) -> OpenTextPollResultsResult:
        """Build paginated open-text results."""
        responses, total = self._poll_response_repo.list_open_text_by_poll(
            poll_id, page, page_size
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        dtos = [
            OpenTextResponseDTO(
                id=r.id,
                text=str(r.response_data.get("text", "")),
                created_at=r.created_at,
            )
            for r in responses
        ]
        return OpenTextPollResultsResult(
            poll_id=poll_id,
            question=question,
            total_responses=total,
            responses=dtos,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _build_multiple_choice_results(
        self,
        poll_id: uuid.UUID,
        question: str,
        options: list,
    ) -> PollResultsResult:
        """Build multiple-choice results from per-option counts."""
        counts = self._poll_response_repo.count_all_by_poll(poll_id)
        total_votes = sum(counts.values())

        option_results = []
        for opt in options:
            count = counts.get(opt.id, 0)
            percentage = round(count / total_votes * 100, 1) if total_votes > 0 else 0.0
            option_results.append(
                PollOptionResult(
                    option_id=opt.id,
                    text=opt.text,
                    count=count,
                    percentage=percentage,
                )
            )

        return PollResultsResult(
            poll_id=poll_id,
            question=question,
            total_votes=total_votes,
            options=option_results,
        )
