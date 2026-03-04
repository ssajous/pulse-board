"""Integration tests for get_word_cloud_frequencies on PollResponseRepository."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from pulse_board.domain.entities.event import Event
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.infrastructure.repositories.event_repository import (
    SQLAlchemyEventRepository,
)
from pulse_board.infrastructure.repositories.poll_repository import (
    SQLAlchemyPollRepository,
)
from pulse_board.infrastructure.repositories.poll_response_repository import (
    SQLAlchemyPollResponseRepository,
)


@pytest.fixture
def event_repo(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
) -> SQLAlchemyEventRepository:
    """Create event repository using the integration session factory."""
    return SQLAlchemyEventRepository(session_factory=integration_session_factory)


@pytest.fixture
def poll_repo(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
) -> SQLAlchemyPollRepository:
    """Create poll repository using the integration session factory."""
    return SQLAlchemyPollRepository(session_factory=integration_session_factory)


@pytest.fixture
def response_repo(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
) -> SQLAlchemyPollResponseRepository:
    """Create poll response repository using the integration session factory."""
    return SQLAlchemyPollResponseRepository(session_factory=integration_session_factory)


@pytest.fixture
def cleanup_word_cloud(
    integration_session_factory: sessionmaker,  # type: ignore[type-arg]
) -> None:
    """Delete all word-cloud-related data after each test in FK-safe order."""
    yield
    with integration_session_factory() as session:
        session.execute(text("DELETE FROM poll_responses"))
        session.execute(text("DELETE FROM polls"))
        session.execute(text("DELETE FROM events"))
        session.commit()


@pytest.fixture
def word_cloud_poll(
    event_repo: SQLAlchemyEventRepository,
    poll_repo: SQLAlchemyPollRepository,
    cleanup_word_cloud: None,
) -> Poll:
    """Create and persist a word_cloud poll ready to accept responses."""
    event = Event.create(title="Word Cloud Test Event", code="WCT001")
    event_repo.create(event)

    poll = Poll.create(
        event_id=event.id,
        question="What one word describes the session?",
        option_texts=[],
        poll_type="word_cloud",
    )
    poll = poll.activate()
    poll_repo.save(poll)
    return poll


def _make_word_cloud_response(
    poll_id: uuid.UUID,
    text: str,
    fingerprint_id: str,
) -> PollResponse:
    """Build a PollResponse with word_cloud response_data."""
    return PollResponse(
        id=uuid.uuid4(),
        poll_id=poll_id,
        fingerprint_id=fingerprint_id,
        option_id=None,
        response_data={"text": text, "fingerprint": fingerprint_id},
        created_at=datetime.now(UTC),
    )


class TestGetWordCloudFrequenciesEmpty:
    """Tests for the empty-data case."""

    def test_returns_empty_list_when_no_responses(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Should return an empty list when the poll has no responses."""
        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        assert result == []

    def test_returns_empty_list_for_unknown_poll_id(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Should return an empty list for a poll with no matching rows."""
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "great", "fp-1")
        )

        result = response_repo.get_word_cloud_frequencies(uuid.uuid4())

        assert result == []


class TestGetWordCloudFrequenciesGrouping:
    """Tests for grouping and counting identical texts."""

    def test_groups_identical_texts_and_counts_correctly(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Identical texts should be grouped into a single (text, count) pair."""
        for i in range(3):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "great", f"fp-{i}")
            )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        assert len(result) == 1
        assert result[0] == ("great", 3)

    def test_distinct_texts_each_appear_once(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Each unique text should appear as its own entry with count 1."""
        words = ["alpha", "beta", "gamma"]
        for idx, word in enumerate(words):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, word, f"fp-{idx}")
            )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        assert len(result) == 3
        texts = {text for text, _ in result}
        assert texts == {"alpha", "beta", "gamma"}
        for _, count in result:
            assert count == 1

    def test_mixed_counts_are_grouped_correctly(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Multiple words submitted different numbers of times should all be grouped."""
        # "fun" appears twice, "hard" appears once
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "fun", "fp-a")
        )
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "fun", "fp-b")
        )
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "hard", "fp-c")
        )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        counts = dict(result)
        assert counts["fun"] == 2
        assert counts["hard"] == 1


class TestGetWordCloudFrequenciesSorting:
    """Tests for the sort order guarantee (count desc, text asc)."""

    def test_sorted_by_count_descending(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Higher-count words must appear before lower-count words."""
        # "popular" 3 times, "rare" 1 time
        for i in range(3):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "popular", f"fp-p-{i}")
            )
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "rare", "fp-r-0")
        )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        assert result[0] == ("popular", 3)
        assert result[1] == ("rare", 1)

    def test_tie_broken_by_text_ascending(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """When two words have the same count, they should be sorted alphabetically."""
        # "zebra" and "apple" each appear once
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "zebra", "fp-z")
        )
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "apple", "fp-a")
        )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        assert len(result) == 2
        assert result[0][0] == "apple"
        assert result[1][0] == "zebra"

    def test_complex_sort_order(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Mixed counts with ties should maintain (count desc, text asc) ordering."""
        # "best" × 3, "cool" × 2, "amazing" × 2, "wow" × 1
        for i in range(3):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "best", f"fp-b{i}")
            )
        for i in range(2):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "cool", f"fp-c{i}")
            )
        for i in range(2):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "amazing", f"fp-a{i}")
            )
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "wow", "fp-w0")
        )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id)

        assert result[0] == ("best", 3)
        # "amazing" < "cool" alphabetically at count 2
        assert result[1] == ("amazing", 2)
        assert result[2] == ("cool", 2)
        assert result[3] == ("wow", 1)


class TestGetWordCloudFrequenciesLimit:
    """Tests for the limit parameter."""

    def test_limit_restricts_number_of_results(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """Limit should cap the number of distinct words returned."""
        words = ["alpha", "beta", "gamma", "delta", "epsilon"]
        for idx, word in enumerate(words):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, word, f"fp-{idx}")
            )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id, limit=3)

        assert len(result) == 3

    def test_limit_returns_top_n_by_count(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """With a limit of 2, the two most frequent words should be returned."""
        # "top" × 5, "second" × 3, "third" × 1
        for i in range(5):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "top", f"fp-t{i}")
            )
        for i in range(3):
            response_repo.create(
                _make_word_cloud_response(word_cloud_poll.id, "second", f"fp-s{i}")
            )
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "third", "fp-th0")
        )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id, limit=2)

        assert len(result) == 2
        assert result[0] == ("top", 5)
        assert result[1] == ("second", 3)

    def test_limit_larger_than_result_set_returns_all(
        self,
        response_repo: SQLAlchemyPollResponseRepository,
        word_cloud_poll: Poll,
    ) -> None:
        """A limit larger than the number of distinct words should return all rows."""
        response_repo.create(
            _make_word_cloud_response(word_cloud_poll.id, "only", "fp-only")
        )

        result = response_repo.get_word_cloud_frequencies(word_cloud_poll.id, limit=100)

        assert len(result) == 1
        assert result[0] == ("only", 1)
