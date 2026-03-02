"""Tests for the list event topics use case."""

import uuid
from datetime import UTC, datetime, timedelta

from pulse_board.application.use_cases.list_event_topics import (
    ListEventTopicsUseCase,
)
from pulse_board.application.use_cases.list_topics import TopicSummary
from pulse_board.domain.entities.topic import Topic
from tests.unit.pulse_board.fakes import FakeTopicRepository


class TestListEventTopicsUseCase:
    """Tests for ListEventTopicsUseCase.execute."""

    def test_returns_empty_list_when_no_topics(self) -> None:
        """Should return empty list when event has no topics."""
        repo = FakeTopicRepository()
        use_case = ListEventTopicsUseCase(repository=repo)
        event_id = uuid.uuid4()

        result = use_case.execute(event_id)

        assert result == []

    def test_returns_topics_for_event(self) -> None:
        """Should return only topics belonging to the given event."""
        repo = FakeTopicRepository()
        event_id = uuid.uuid4()
        other_event_id = uuid.uuid4()

        topic1 = Topic.create("Topic 1", event_id=event_id)
        topic2 = Topic.create("Topic 2", event_id=event_id)
        other_topic = Topic.create("Other", event_id=other_event_id)
        repo.create(topic1)
        repo.create(topic2)
        repo.create(other_topic)

        use_case = ListEventTopicsUseCase(repository=repo)
        result = use_case.execute(event_id)

        assert len(result) == 2
        contents = {r.content for r in result}
        assert contents == {"Topic 1", "Topic 2"}

    def test_returns_topic_summary_instances(self) -> None:
        """Each item should be a TopicSummary."""
        repo = FakeTopicRepository()
        event_id = uuid.uuid4()
        topic = Topic.create("Summary topic", event_id=event_id)
        repo.create(topic)

        use_case = ListEventTopicsUseCase(repository=repo)
        result = use_case.execute(event_id)

        assert len(result) == 1
        assert isinstance(result[0], TopicSummary)
        assert result[0].content == "Summary topic"
        assert result[0].score == 0
        assert result[0].id == topic.id
        assert result[0].created_at == topic.created_at

    def test_sorted_by_score_descending(self) -> None:
        """Topics should be sorted by score descending."""
        repo = FakeTopicRepository()
        event_id = uuid.uuid4()
        base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

        low = Topic.create("Low", event_id=event_id)
        mid = Topic.create("Mid", event_id=event_id)
        high = Topic.create("High", event_id=event_id)
        repo.create(low)
        repo.create(mid)
        repo.create(high)
        # Manually set scores
        repo.update_score(low.id, 1)
        repo.update_score(mid.id, 5)
        repo.update_score(high.id, 10)

        use_case = ListEventTopicsUseCase(repository=repo)
        result = use_case.execute(event_id)

        scores = [r.score for r in result]
        assert scores == [10, 5, 1]

    def test_topics_without_event_id_excluded(self) -> None:
        """Topics with no event_id should not appear in results."""
        repo = FakeTopicRepository()
        event_id = uuid.uuid4()

        global_topic = Topic.create("Global")
        event_topic = Topic.create("Event", event_id=event_id)
        repo.create(global_topic)
        repo.create(event_topic)

        use_case = ListEventTopicsUseCase(repository=repo)
        result = use_case.execute(event_id)

        assert len(result) == 1
        assert result[0].content == "Event"
