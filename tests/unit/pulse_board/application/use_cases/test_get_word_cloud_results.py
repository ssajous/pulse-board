"""Tests for GetPollResultsUseCase with word cloud polls."""

import uuid

from pulse_board.application.use_cases.get_poll_results import (
    GetPollResultsUseCase,
    WordCloudPollResultsResult,
)
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.entities.poll_response import PollResponse
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


def _create_word_cloud_poll(
    poll_repo: FakePollRepository,
    question: str = "One word for today?",
) -> Poll:
    """Create and persist a word cloud poll."""
    poll = Poll.create(
        event_id=uuid.uuid4(),
        question=question,
        option_texts=[],
        poll_type="word_cloud",
    )
    return poll_repo.create(poll)


def _submit_word_cloud_response(
    response_repo: FakePollResponseRepository,
    poll_id: uuid.UUID,
    fingerprint: str,
    text: str,
) -> PollResponse:
    """Create and persist a word cloud poll response."""
    response = PollResponse.create_word_cloud(
        poll_id=poll_id,
        fingerprint_id=fingerprint,
        text=text,
    )
    return response_repo.create(response)


class TestGetWordCloudPollResults:
    """Tests for GetPollResultsUseCase with word_cloud poll type."""

    def test_returns_word_cloud_results_type(self) -> None:
        """Should return WordCloudPollResultsResult for word_cloud polls."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        _submit_word_cloud_response(response_repo, poll.id, "fp-1", "python")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)

    def test_returns_correct_word_frequencies(self) -> None:
        """Should return correct word frequencies from submitted responses."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        _submit_word_cloud_response(response_repo, poll.id, "fp-1", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-2", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-3", "java")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        word_map = {w.text: w.count for w in result.words}
        assert word_map["python"] == 2
        assert word_map["java"] == 1

    def test_returns_empty_words_list_for_poll_with_no_responses(self) -> None:
        """Should return an empty words list when no responses exist."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert result.words == []
        assert result.total_responses == 0

    def test_total_responses_is_sum_of_all_counts(self) -> None:
        """total_responses should equal the sum of all individual word counts."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        _submit_word_cloud_response(response_repo, poll.id, "fp-1", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-2", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-3", "java")
        _submit_word_cloud_response(response_repo, poll.id, "fp-4", "rust")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert result.total_responses == 4

    def test_words_sorted_by_count_descending(self) -> None:
        """Words should be returned sorted by count descending."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        _submit_word_cloud_response(response_repo, poll.id, "fp-1", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-2", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-3", "python")
        _submit_word_cloud_response(response_repo, poll.id, "fp-4", "java")
        _submit_word_cloud_response(response_repo, poll.id, "fp-5", "java")
        _submit_word_cloud_response(response_repo, poll.id, "fp-6", "rust")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        counts = [w.count for w in result.words]
        assert counts == sorted(counts, reverse=True)

    def test_maximum_fifty_words_returned(self) -> None:
        """Should return at most 50 distinct words."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        # Submit 60 distinct single-character words using unique fingerprints
        distinct_words = [chr(ord("a") + i % 26) + str(i) for i in range(60)]
        for i, word in enumerate(distinct_words):
            # Ensure each word is at most 30 chars and 1 word
            short_word = word[:5]
            _submit_word_cloud_response(response_repo, poll.id, f"fp-{i}", short_word)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert len(result.words) <= 50

    def test_returns_correct_question(self) -> None:
        """Should include the poll question in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo, question="Tag this session!")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert result.question == "Tag this session!"

    def test_returns_correct_poll_id(self) -> None:
        """Should include the poll_id in the result."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert result.poll_id == poll.id

    def test_single_response_appears_in_words(self) -> None:
        """A single submission should appear with count of 1."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        _submit_word_cloud_response(response_repo, poll.id, "fp-1", "agile")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert len(result.words) == 1
        assert result.words[0].text == "agile"
        assert result.words[0].count == 1

    def test_total_responses_zero_for_no_submissions(self) -> None:
        """total_responses should be 0 when no responses have been submitted."""
        # Arrange
        use_case, poll_repo, _response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        assert result.total_responses == 0

    def test_multi_word_phrases_aggregated_correctly(self) -> None:
        """Multi-word phrases submitted identically should be counted together."""
        # Arrange
        use_case, poll_repo, response_repo = _setup()
        poll = _create_word_cloud_poll(poll_repo)
        _submit_word_cloud_response(response_repo, poll.id, "fp-1", "machine learning")
        _submit_word_cloud_response(response_repo, poll.id, "fp-2", "machine learning")
        _submit_word_cloud_response(response_repo, poll.id, "fp-3", "deep learning")

        # Act
        result = use_case.execute(poll.id)

        # Assert
        assert isinstance(result, WordCloudPollResultsResult)
        word_map = {w.text: w.count for w in result.words}
        assert word_map["machine learning"] == 2
        assert word_map["deep learning"] == 1
        assert result.total_responses == 3
