"""Tests for the get poll results use case."""

import uuid

import pytest

from pulse_board.application.use_cases.get_poll_results import (
    GetPollResultsUseCase,
    PollOptionResult,
    PollResultsResult,
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

        with pytest.raises(AttributeError):
            result.total_votes = 99  # type: ignore[misc]

    def test_option_result_is_frozen(self) -> None:
        """PollOptionResult should be immutable."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_poll(poll_repo)

        result = use_case.execute(poll.id)

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

        for i, opt in enumerate(result.options):
            assert isinstance(opt, PollOptionResult)
            assert opt.option_id == poll.options[i].id
            assert opt.text == poll.options[i].text
