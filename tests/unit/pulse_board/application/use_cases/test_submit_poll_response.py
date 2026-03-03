"""Tests for the submit poll response use case."""

import uuid

import pytest

from pulse_board.application.use_cases.submit_poll_response import (
    SubmitPollResponseResult,
    SubmitPollResponseUseCase,
)
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.exceptions import (
    DuplicateResponseError,
    EntityNotFoundError,
    InvalidPollOptionError,
    PollNotActiveError,
)
from tests.unit.pulse_board.fakes import (
    FakePollRepository,
    FakePollResponseRepository,
)

FINGERPRINT = "test-fingerprint-abc"


def _setup() -> tuple[
    SubmitPollResponseUseCase,
    FakePollRepository,
    FakePollResponseRepository,
]:
    """Create a SubmitPollResponseUseCase with fresh fake repos."""
    poll_repo = FakePollRepository()
    response_repo = FakePollResponseRepository()
    use_case = SubmitPollResponseUseCase(
        poll_repository=poll_repo,
        poll_response_repository=response_repo,
    )
    return use_case, poll_repo, response_repo


def _create_active_poll(
    poll_repo: FakePollRepository,
) -> Poll:
    """Create and persist an active poll with known options."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="Pick one?",
        option_texts=["Alpha", "Bravo", "Charlie"],
    )
    saved = poll_repo.create(poll)
    poll_repo.update_active_status(saved.id, True)
    return poll_repo.get_by_id(saved.id)  # type: ignore[return-value]


def _create_inactive_poll(
    poll_repo: FakePollRepository,
) -> Poll:
    """Create and persist an inactive poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="Inactive?",
        option_texts=["X", "Y"],
    )
    return poll_repo.create(poll)


class TestSubmitPollResponseUseCase:
    """Tests for SubmitPollResponseUseCase.execute."""

    def test_successful_submission(self) -> None:
        """Should submit a response and return a result."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_poll(poll_repo)
        option_id = poll.options[0].id

        result = use_case.execute(poll.id, FINGERPRINT, option_id)

        assert isinstance(result, SubmitPollResponseResult)
        assert result.poll_id == poll.id
        assert result.option_id == option_id
        assert result.id is not None
        assert result.created_at is not None

    def test_persists_response_to_repository(self) -> None:
        """Should persist the response in the repository."""
        use_case, poll_repo, response_repo = _setup()
        poll = _create_active_poll(poll_repo)
        option_id = poll.options[0].id

        use_case.execute(poll.id, FINGERPRINT, option_id)

        found = response_repo.find_by_poll_and_fingerprint(
            poll.id,
            FINGERPRINT,
        )
        assert found is not None
        assert found.option_id == option_id

    def test_poll_not_found_raises_error(self) -> None:
        """Should raise EntityNotFoundError for nonexistent poll."""
        use_case, _poll_repo, _response_repo = _setup()
        missing_id = uuid.uuid4()
        option_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundError, match="Poll"):
            use_case.execute(missing_id, FINGERPRINT, option_id)

    def test_poll_not_active_raises_error(self) -> None:
        """Should raise PollNotActiveError for inactive poll."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_inactive_poll(poll_repo)
        option_id = poll.options[0].id

        with pytest.raises(PollNotActiveError, match="inactive"):
            use_case.execute(poll.id, FINGERPRINT, option_id)

    def test_invalid_option_raises_error(self) -> None:
        """Should raise InvalidPollOptionError for unknown option."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_poll(poll_repo)
        bogus_option = uuid.uuid4()

        with pytest.raises(InvalidPollOptionError, match="does not belong"):
            use_case.execute(poll.id, FINGERPRINT, bogus_option)

    def test_duplicate_fingerprint_raises_error(self) -> None:
        """Should raise DuplicateResponseError on second response."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_poll(poll_repo)
        option_id = poll.options[0].id

        use_case.execute(poll.id, FINGERPRINT, option_id)

        with pytest.raises(DuplicateResponseError, match="already responded"):
            use_case.execute(poll.id, FINGERPRINT, poll.options[1].id)

    def test_different_fingerprints_succeed(self) -> None:
        """Different participants should be able to respond."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_poll(poll_repo)
        option_id = poll.options[0].id

        r1 = use_case.execute(poll.id, "fp-user-1", option_id)
        r2 = use_case.execute(poll.id, "fp-user-2", option_id)

        assert r1.id != r2.id

    def test_result_is_frozen(self) -> None:
        """SubmitPollResponseResult should be immutable."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_poll(poll_repo)
        option_id = poll.options[0].id

        result = use_case.execute(poll.id, FINGERPRINT, option_id)

        with pytest.raises(AttributeError):
            result.poll_id = uuid.uuid4()  # type: ignore[misc]

    def test_can_select_any_valid_option(self) -> None:
        """Should accept any option that belongs to the poll."""
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_poll(poll_repo)

        # Use the last option instead of the first
        last_option = poll.options[-1]
        result = use_case.execute(poll.id, FINGERPRINT, last_option.id)

        assert result.option_id == last_option.id

    def test_order_of_validation_poll_not_found_before_active_check(
        self,
    ) -> None:
        """EntityNotFoundError should be raised before PollNotActiveError."""
        use_case, _poll_repo, _response_repo = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundError):
            use_case.execute(missing_id, FINGERPRINT, uuid.uuid4())
