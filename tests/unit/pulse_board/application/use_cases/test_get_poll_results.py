"""Tests for the get poll results use case."""

import uuid

import pytest

from pulse_board.application.use_cases.get_poll_results import (
    GetPollResultsUseCase,
    OpenTextPollResultsResult,
    PollOptionResult,
    PollResultsResult,
    RatingPollResultsResult,
)
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.domain.exceptions import EntityNotFoundError
from tests.unit.pulse_board.fakes import (
    FakePollRepository,
    FakePollResponseRepository,
)


def _setup() -> tuple[
    GetPollResultsUseCase,
    FakePollRepository,
    FakePollResponseRepository,
]:
    """Create a GetPollResultsUseCase with fresh fake repos."""
    poll_repo = FakePollRepository()
    response_repo = FakePollResponseRepository()
    use_case = GetPollResultsUseCase(
        poll_repository=poll_repo,
        poll_response_repository=response_repo,
    )
    return use_case, poll_repo, response_repo


def _create_poll(
    poll_repo: FakePollRepository,
    option_texts: list[str] | None = None,
) -> Poll:
    """Create and persist a poll."""
    texts = option_texts or ["Red", "Blue", "Green"]
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="Favorite color?",
        option_texts=texts,
    )
    return poll_repo.create(poll)


def _submit_response(
    response_repo: FakePollResponseRepository,
    poll_id: uuid.UUID,
    option_id: uuid.UUID,
    fingerprint: str,
) -> PollResponse:
    """Create and persist a poll response."""
    response = PollResponse.create(
        poll_id=poll_id,
        fingerprint_id=fingerprint,
        option_id=option_id,
    )
    return response_repo.create(response)


class TestGetPollResultsUseCase:
    """Tests for GetPollResultsUseCase.execute."""

    def test_results_with_votes(self) -> None:
        """Should return correct counts and percentages."""
        use_case, poll_repo, response_repo = _setup()
        poll = _create_poll(poll_repo)
        red_id = poll.options[0].id
        blue_id = poll.options[1].id

        # 3 votes for Red, 1 for Blue, 0 for Green
        _submit_response(response_repo, poll.id, red_id, "fp-1")
        _submit_response(response_repo, poll.id, red_id, "fp-2")
        _submit_response(response_repo, poll.id, red_id, "fp-3")
        _submit_response(response_repo, poll.id, blue_id, "fp-4")

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        assert result.poll_id == poll.id
        assert result.question == "Favorite color?"
        assert result.total_votes == 4

        # Check per-option results
        red_result = result.options[0]
        assert red_result.count == 3
        assert red_result.percentage == 75.0

        blue_result = result.options[1]
        assert blue_result.count == 1
        assert blue_result.percentage == 25.0

        green_result = result.options[2]
        assert green_result.count == 0
        assert green_result.percentage == 0.0

    def test_results_with_zero_votes(self) -> None:
        """Should return 0 counts and 0.0 percentages when no votes."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        assert result.total_votes == 0
        for opt in result.options:
            assert opt.count == 0
            assert opt.percentage == 0.0

    def test_poll_not_found_raises_error(self) -> None:
        """Should raise EntityNotFoundError for nonexistent poll."""
        use_case, _poll_repo, _response_repo = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundError, match="Poll"):
            use_case.execute(missing_id)

    def test_options_in_original_order(self) -> None:
        """Options should be returned in the same order as the poll."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(
            poll_repo,
            option_texts=["First", "Second", "Third"],
        )

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        texts = [opt.text for opt in result.options]
        assert texts == ["First", "Second", "Third"]

    def test_percentage_calculation_rounding(self) -> None:
        """Percentages should be rounded to 1 decimal place."""
        use_case, poll_repo, response_repo = _setup()
        poll = _create_poll(
            poll_repo,
            option_texts=["A", "B", "C"],
        )
        a_id = poll.options[0].id
        b_id = poll.options[1].id
        c_id = poll.options[2].id

        # 1/3 each => 33.3%
        _submit_response(response_repo, poll.id, a_id, "fp-1")
        _submit_response(response_repo, poll.id, b_id, "fp-2")
        _submit_response(response_repo, poll.id, c_id, "fp-3")

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        for opt in result.options:
            assert opt.percentage == 33.3

    def test_all_votes_for_one_option(self) -> None:
        """Single option getting all votes should show 100%."""
        use_case, poll_repo, response_repo = _setup()
        poll = _create_poll(poll_repo, option_texts=["Yes", "No"])
        yes_id = poll.options[0].id

        _submit_response(response_repo, poll.id, yes_id, "fp-1")
        _submit_response(response_repo, poll.id, yes_id, "fp-2")

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        yes_result = result.options[0]
        assert yes_result.count == 2
        assert yes_result.percentage == 100.0

        no_result = result.options[1]
        assert no_result.count == 0
        assert no_result.percentage == 0.0

    def test_result_is_frozen(self) -> None:
        """PollResultsResult should be immutable."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        with pytest.raises(AttributeError):
            result.total_votes = 99  # type: ignore[misc]

    def test_option_result_is_frozen(self) -> None:
        """PollOptionResult should be immutable."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        with pytest.raises(AttributeError):
            result.options[0].count = 99  # type: ignore[misc]

    def test_result_includes_question(self) -> None:
        """Result should include the poll question text."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id)

        assert result.question == "Favorite color?"

    def test_option_result_includes_text_and_option_id(self) -> None:
        """Each option result should have text and option_id."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id)

        assert isinstance(result, PollResultsResult)
        for i, opt in enumerate(result.options):
            assert isinstance(opt, PollOptionResult)
            assert opt.option_id == poll.options[i].id
            assert opt.text == poll.options[i].text


def _create_rating_poll(
    poll_repo: FakePollRepository,
    question: str = "How would you rate this?",
) -> Poll:
    """Create and persist a rating poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question=question,
        option_texts=[],
        poll_type="rating",
    )
    return poll_repo.create(poll)


def _create_open_text_poll(
    poll_repo: FakePollRepository,
    question: str = "What do you think?",
) -> Poll:
    """Create and persist an open text poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question=question,
        option_texts=[],
        poll_type="open_text",
    )
    return poll_repo.create(poll)


def _submit_rating_response(
    response_repo: FakePollResponseRepository,
    poll_id: uuid.UUID,
    fingerprint: str,
    rating: int,
) -> PollResponse:
    """Create and persist a rating poll response."""
    response = PollResponse.create_rating(
        poll_id=poll_id,
        fingerprint_id=fingerprint,
        rating=rating,
    )
    return response_repo.create(response)


def _submit_open_text_response(
    response_repo: FakePollResponseRepository,
    poll_id: uuid.UUID,
    fingerprint: str,
    text: str,
) -> PollResponse:
    """Create and persist an open text poll response."""
    response = PollResponse.create_open_text(
        poll_id=poll_id,
        fingerprint_id=fingerprint,
        text=text,
    )
    return response_repo.create(response)


class TestGetRatingPollResults:
    """Tests for rating poll result aggregation."""

    def test_rating_poll_returns_rating_results_type(self) -> None:
        """Should return RatingPollResultsResult for rating polls."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_rating_poll(poll_repo)
        _submit_rating_response(response_repo, poll.id, "fp-1", 3)
        _submit_rating_response(response_repo, poll.id, "fp-2", 5)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, RatingPollResultsResult)

    def test_rating_poll_no_responses_returns_none_average(self) -> None:
        """Should return None average when no responses."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_rating_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, RatingPollResultsResult)
        assert result.average_rating is None
        assert result.distribution == {}
        assert result.total_votes == 0

    def test_rating_poll_single_response_average(self) -> None:
        """Should return correct average for single response."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_rating_poll(poll_repo)
        _submit_rating_response(response_repo, poll.id, "fp-1", 4)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, RatingPollResultsResult)
        assert result.average_rating == 4.0
        assert result.distribution == {"4": 1}
        assert result.total_votes == 1

    def test_rating_poll_multiple_responses_average(self) -> None:
        """Should return correct average and distribution for multiple responses."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_rating_poll(poll_repo)
        _submit_rating_response(response_repo, poll.id, "fp-1", 5)
        _submit_rating_response(response_repo, poll.id, "fp-2", 5)
        _submit_rating_response(response_repo, poll.id, "fp-3", 3)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        # Average = (5 + 5 + 3) / 3 = 13/3 = 4.33
        assert isinstance(result, RatingPollResultsResult)
        assert result.average_rating == 4.33
        assert result.distribution == {"5": 2, "3": 1}
        assert result.total_votes == 3

    def test_rating_poll_returns_correct_question(self) -> None:
        """Should return the poll question in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_rating_poll(poll_repo, question="Rate the session!")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, RatingPollResultsResult)
        assert result.question == "Rate the session!"

    def test_rating_poll_returns_correct_poll_id(self) -> None:
        """Should return the poll ID in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_rating_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, RatingPollResultsResult)
        assert result.poll_id == poll.id

    def test_rating_poll_all_same_rating(self) -> None:
        """Should compute average correctly when all ratings are identical."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_rating_poll(poll_repo)
        for i in range(4):
            _submit_rating_response(response_repo, poll.id, f"fp-{i}", 2)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, RatingPollResultsResult)
        assert result.average_rating == 2.0
        assert result.distribution == {"2": 4}
        assert result.total_votes == 4


class TestGetOpenTextPollResults:
    """Tests for open text poll result pagination."""

    def test_open_text_poll_returns_open_text_results_type(self) -> None:
        """Should return OpenTextPollResultsResult for open_text polls."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_open_text_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, OpenTextPollResultsResult)

    def test_open_text_poll_no_responses(self) -> None:
        """Should return empty responses list with total_responses=0."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_open_text_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, OpenTextPollResultsResult)
        assert result.total_responses == 0
        assert result.responses == []
        assert result.total_pages == 0

    def test_open_text_poll_pagination_page_1(self) -> None:
        """Should return first page of responses ordered newest first."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_open_text_poll(poll_repo)
        _submit_open_text_response(response_repo, poll.id, "fp-1", "First response")
        _submit_open_text_response(response_repo, poll.id, "fp-2", "Second response")
        _submit_open_text_response(response_repo, poll.id, "fp-3", "Third response")

        # Act
        result = use_case.execute(poll.id, page=1, page_size=2)

        # Assert
        assert isinstance(result, OpenTextPollResultsResult)
        assert len(result.responses) == 2
        assert result.total_responses == 3

    def test_open_text_poll_total_pages_calculated_correctly(self) -> None:
        """Should calculate total_pages based on total_responses and page_size."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_open_text_poll(poll_repo)
        for i in range(5):
            _submit_open_text_response(
                response_repo, poll.id, f"fp-{i}", f"Response {i}"
            )

        # Act — 5 responses, page_size=2 => 3 pages
        result_five = use_case.execute(poll.id, page=1, page_size=2)

        # Create second poll with 4 responses, page_size=2 => 2 pages
        poll2 = _create_open_text_poll(poll_repo)
        for i in range(4):
            _submit_open_text_response(
                response_repo, poll2.id, f"fp-{i}", f"Response {i}"
            )
        result_four = use_case.execute(poll2.id, page=1, page_size=2)

        # Assert
        assert isinstance(result_five, OpenTextPollResultsResult)
        assert isinstance(result_four, OpenTextPollResultsResult)
        assert result_five.total_pages == 3
        assert result_four.total_pages == 2

    def test_open_text_poll_responses_have_text(self) -> None:
        """Each response DTO should have the submitted text."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_open_text_poll(poll_repo)
        _submit_open_text_response(response_repo, poll.id, "fp-1", "Hello world")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, OpenTextPollResultsResult)
        assert len(result.responses) == 1
        assert result.responses[0].text == "Hello world"

    def test_open_text_poll_returns_correct_question(self) -> None:
        """Should return the poll question in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_open_text_poll(poll_repo, question="What is your feedback?")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, OpenTextPollResultsResult)
        assert result.question == "What is your feedback?"

    def test_open_text_poll_page_2_returns_remaining_responses(self) -> None:
        """Should return second page with remaining responses."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_open_text_poll(poll_repo)
        for i in range(3):
            _submit_open_text_response(
                response_repo, poll.id, f"fp-{i}", f"Response {i}"
            )

        # Act
        result = use_case.execute(poll.id, page=2, page_size=2)

        # Assert
        assert isinstance(result, OpenTextPollResultsResult)
        assert len(result.responses) == 1
        assert result.total_responses == 3
        assert result.page == 2
