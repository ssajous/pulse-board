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
    ValidationError,
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


def _create_active_rating_poll(
    poll_repo: FakePollRepository,
) -> Poll:
    """Create and persist an active rating poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="Rate this session?",
        option_texts=[],
        poll_type="rating",
    )
    saved = poll_repo.create(poll)
    poll_repo.update_active_status(saved.id, True)
    return poll_repo.get_by_id(saved.id)  # type: ignore[return-value]


def _create_active_open_text_poll(
    poll_repo: FakePollRepository,
) -> Poll:
    """Create and persist an active open text poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="What is your feedback?",
        option_texts=[],
        poll_type="open_text",
    )
    saved = poll_repo.create(poll)
    poll_repo.update_active_status(saved.id, True)
    return poll_repo.get_by_id(saved.id)  # type: ignore[return-value]


class TestSubmitRatingPollResponse:
    """Tests for submitting rating poll responses."""

    def test_submit_rating_response_success(self) -> None:
        """Should accept rating response for rating poll."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value=4)

        # Assert
        assert isinstance(result, SubmitPollResponseResult)
        assert result.poll_id == poll.id
        assert result.option_id is None
        assert result.poll_type == "rating"

    def test_submit_rating_response_persisted(self) -> None:
        """Should persist the rating response in the repository."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act
        use_case.execute(poll.id, FINGERPRINT, response_value=3)

        # Assert
        found = response_repo.find_by_poll_and_fingerprint(poll.id, FINGERPRINT)
        assert found is not None
        assert found.response_data.get("rating") == 3

    def test_submit_rating_too_high_raises_validation_error(self) -> None:
        """Should raise ValidationError for rating above maximum (5)."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value=6)

    def test_submit_rating_too_low_raises_validation_error(self) -> None:
        """Should raise ValidationError for rating below minimum (1)."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value=0)

    def test_submit_rating_duplicate_fingerprint_raises(self) -> None:
        """Should raise DuplicateResponseError for duplicate rating submission."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)
        use_case.execute(poll.id, FINGERPRINT, response_value=5)

        # Act / Assert
        with pytest.raises(DuplicateResponseError, match="already responded"):
            use_case.execute(poll.id, FINGERPRINT, response_value=3)

    def test_submit_rating_result_has_event_id(self) -> None:
        """Should include the event_id in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value=2)

        # Assert
        assert result.event_id == poll.event_id

    def test_submit_rating_result_has_created_at(self) -> None:
        """Should include a non-None created_at timestamp in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value=1)

        # Assert
        assert result.created_at is not None

    def test_submit_rating_different_fingerprints_succeed(self) -> None:
        """Different participants should be able to submit separate ratings."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_rating_poll(poll_repo)

        # Act
        r1 = use_case.execute(poll.id, "fp-user-1", response_value=5)
        r2 = use_case.execute(poll.id, "fp-user-2", response_value=3)

        # Assert
        assert r1.id != r2.id


class TestSubmitOpenTextPollResponse:
    """Tests for submitting open text poll responses."""

    def test_submit_open_text_response_success(self) -> None:
        """Should accept text response for open_text poll."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value="Hello world")

        # Assert
        assert isinstance(result, SubmitPollResponseResult)
        assert result.poll_id == poll.id
        assert result.option_id is None
        assert result.poll_type == "open_text"

    def test_submit_open_text_response_persisted(self) -> None:
        """Should persist the text response in the repository."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)

        # Act
        use_case.execute(poll.id, FINGERPRINT, response_value="Great event!")

        # Assert
        found = response_repo.find_by_poll_and_fingerprint(poll.id, FINGERPRINT)
        assert found is not None
        assert found.response_data.get("text") == "Great event!"

    def test_submit_open_text_empty_text_raises_validation_error(self) -> None:
        """Should raise ValidationError for empty text."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value="")

    def test_submit_open_text_whitespace_only_raises_validation_error(self) -> None:
        """Should raise ValidationError for whitespace-only text."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value="   ")

    def test_submit_open_text_too_long_raises_validation_error(self) -> None:
        """Should raise ValidationError for text exceeding 500 characters."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)
        long_text = "x" * 501

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value=long_text)

    def test_submit_open_text_max_length_succeeds(self) -> None:
        """Should accept text exactly at the 500-character limit."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)
        max_text = "x" * 500

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value=max_text)

        # Assert
        assert isinstance(result, SubmitPollResponseResult)

    def test_submit_open_text_duplicate_fingerprint_raises(self) -> None:
        """Should raise DuplicateResponseError for duplicate submission."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)
        use_case.execute(poll.id, FINGERPRINT, response_value="First response")

        # Act / Assert
        with pytest.raises(DuplicateResponseError, match="already responded"):
            use_case.execute(poll.id, FINGERPRINT, response_value="Second attempt")

    def test_submit_open_text_result_has_event_id(self) -> None:
        """Should include the event_id in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value="Feedback here")

        # Assert
        assert result.event_id == poll.event_id

    def test_submit_open_text_different_fingerprints_succeed(self) -> None:
        """Different participants should be able to submit separate text responses."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_open_text_poll(poll_repo)

        # Act
        r1 = use_case.execute(poll.id, "fp-user-1", response_value="Great!")
        r2 = use_case.execute(poll.id, "fp-user-2", response_value="Good session.")

        # Assert
        assert r1.id != r2.id
