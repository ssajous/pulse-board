"""Tests for the list topics use case."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from pulse_board.application.use_cases.list_topics import (
    ListTopicsUseCase,
)
from pulse_board.domain.entities.topic import Topic
from tests.unit.pulse_board.fakes import FakeTopicRepository


def _make_topic(content: str, score: int, minutes_ago: int) -> Topic:
    """Create a topic with a specific score and age."""
    return Topic(
        id=uuid.uuid4(),
        content=content,
        score=score,
        created_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


class TestListTopicsUseCase:
    """Tests for ListTopicsUseCase."""

    def test_empty_list(self) -> None:
        """Should return an empty list when no topics exist."""
        repo = FakeTopicRepository()
        use_case = ListTopicsUseCase(repository=repo)

        result = use_case.execute()

        assert result == []

    def test_returns_topics(self) -> None:
        """Should return all stored topics."""
        repo = FakeTopicRepository()
        topic = Topic.create("A topic")
        repo.create(topic)
        use_case = ListTopicsUseCase(repository=repo)

        result = use_case.execute()

        assert len(result) == 1
        assert result[0].content == "A topic"

    def test_sorted_by_score_descending(self) -> None:
        """Topics with higher scores should appear first."""
        repo = FakeTopicRepository()
        low = _make_topic("low", score=1, minutes_ago=0)
        high = _make_topic("high", score=10, minutes_ago=0)
        repo.create(low)
        repo.create(high)
        use_case = ListTopicsUseCase(repository=repo)

        result = use_case.execute()

        assert result[0].content == "high"
        assert result[1].content == "low"

    def test_tiebreak_by_created_at_descending(self) -> None:
        """Same-score topics should be ordered newest first."""
        repo = FakeTopicRepository()
        older = _make_topic("older", score=5, minutes_ago=10)
        newer = _make_topic("newer", score=5, minutes_ago=1)
        repo.create(older)
        repo.create(newer)
        use_case = ListTopicsUseCase(repository=repo)

        result = use_case.execute()

        assert result[0].content == "newer"
        assert result[1].content == "older"

    def test_result_items_are_frozen(self) -> None:
        """TopicSummary instances should be immutable."""
        repo = FakeTopicRepository()
        repo.create(Topic.create("test"))
        use_case = ListTopicsUseCase(repository=repo)

        result = use_case.execute()

        with pytest.raises(AttributeError):
            result[0].content = "changed"  # type: ignore[misc]
