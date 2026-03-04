"""Tests for submitting word cloud poll responses via SubmitPollResponseUseCase."""

import uuid

import pytest

from pulse_board.application.use_cases.submit_poll_response import (
    SubmitPollResponseResult,
    SubmitPollResponseUseCase,
)
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.exceptions import (
    DuplicateResponseError,
    PollNotActiveError,
    ValidationError,
)
from tests.unit.pulse_board.fakes import (
    FakePollRepository,
    FakePollResponseRepository,
)

FINGERPRINT = "test-fingerprint-wc"


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


def _create_active_word_cloud_poll(
    poll_repo: FakePollRepository,
) -> Poll:
    """Create and persist an active word cloud poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="What one word describes today?",
        option_texts=[],
        poll_type="word_cloud",
    )
    saved = poll_repo.create(poll)
    poll_repo.update_active_status(saved.id, True)
    return poll_repo.get_by_id(saved.id)  # type: ignore[return-value]


def _create_inactive_word_cloud_poll(
    poll_repo: FakePollRepository,
) -> Poll:
    """Create and persist an inactive word cloud poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question="Inactive word cloud?",
        option_texts=[],
        poll_type="word_cloud",
    )
    return poll_repo.create(poll)


class TestSubmitWordCloudPollResponse:
    """Tests for submitting word cloud responses through SubmitPollResponseUseCase."""

    def test_successful_word_cloud_response_submission(self) -> None:
        """Should submit a word cloud response and return a result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value="python")

        # Assert
        assert isinstance(result, SubmitPollResponseResult)
        assert result.poll_id == poll.id
        assert result.poll_type == "word_cloud"
        assert result.option_id is None

    def test_word_cloud_response_persisted_to_repository(self) -> None:
        """Should persist the word cloud response in the repository."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        use_case.execute(poll.id, FINGERPRINT, response_value="python")

        # Assert
        found = response_repo.find_by_poll_and_fingerprint(poll.id, FINGERPRINT)
        assert found is not None
        assert found.response_data.get("text") == "python"

    def test_response_value_is_required(self) -> None:
        """Should raise ValidationError when response_value is None."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError, match="response_value is required"):
            use_case.execute(poll.id, FINGERPRINT, response_value=None)

    def test_duplicate_response_is_rejected(self) -> None:
        """Should raise DuplicateResponseError on second response from same fp."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)
        use_case.execute(poll.id, FINGERPRINT, response_value="first")

        # Act / Assert
        with pytest.raises(DuplicateResponseError, match="already responded"):
            use_case.execute(poll.id, FINGERPRINT, response_value="second")

    def test_inactive_poll_raises_poll_not_active_error(self) -> None:
        """Should raise PollNotActiveError when poll is inactive."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_inactive_word_cloud_poll(poll_repo)

        # Act / Assert
        with pytest.raises(PollNotActiveError, match="inactive"):
            use_case.execute(poll.id, FINGERPRINT, response_value="hello")

    def test_text_is_normalized_through_word_cloud_validation(self) -> None:
        """Should normalize the submitted text (lowercase, whitespace collapse)."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        use_case.execute(poll.id, FINGERPRINT, response_value="  MACHINE   Learning  ")

        # Assert — stored text should be normalized
        found = response_repo.find_by_poll_and_fingerprint(poll.id, FINGERPRINT)
        assert found is not None
        assert found.response_data.get("text") == "machine learning"

    def test_empty_text_raises_validation_error(self) -> None:
        """Should raise ValidationError for empty text submission."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value="")

    def test_whitespace_only_text_raises_validation_error(self) -> None:
        """Should raise ValidationError for whitespace-only text submission."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value="   ")

    def test_text_exceeding_thirty_chars_raises_validation_error(self) -> None:
        """Should raise ValidationError for text exceeding 30 characters."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)
        long_text = "a" * 31

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value=long_text)

    def test_more_than_three_words_raises_validation_error(self) -> None:
        """Should raise ValidationError for more than 3 words."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act / Assert
        with pytest.raises(ValidationError):
            use_case.execute(poll.id, FINGERPRINT, response_value="one two three four")

    def test_result_includes_event_id(self) -> None:
        """Should include the event_id in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value="great")

        # Assert
        assert result.event_id == poll.event_id

    def test_result_includes_created_at(self) -> None:
        """Should include a non-None created_at timestamp."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id, FINGERPRINT, response_value="great")

        # Assert
        assert result.created_at is not None

    def test_different_fingerprints_can_both_submit(self) -> None:
        """Different participants should be able to submit separate responses."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        r1 = use_case.execute(poll.id, "fp-user-1", response_value="python")
        r2 = use_case.execute(poll.id, "fp-user-2", response_value="java")

        # Assert
        assert r1.id != r2.id

    def test_two_word_submission_succeeds(self) -> None:
        """Should accept a two-word submission."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_active_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(
            poll.id, FINGERPRINT, response_value="machine learning"
        )

        # Assert
        assert isinstance(result, SubmitPollResponseResult)
        found = response_repo.find_by_poll_and_fingerprint(poll.id, FINGERPRINT)
        assert found is not None
        assert found.response_data.get("text") == "machine learning"
