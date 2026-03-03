"""Tests for GetEventStatsUseCase."""

import uuid

import pytest

from pulse_board.application.use_cases.get_event_stats import GetEventStatsUseCase
from pulse_board.domain.entities.event import Event
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.entities.topic import Topic, TopicStatus
from pulse_board.domain.exceptions import EventNotFoundError
from tests.unit.pulse_board.fakes import (
    FakeEventRepository,
    FakeParticipantCounter,
    FakePollRepository,
    FakePollResponseRepository,
    FakeTopicRepository,
)


@pytest.fixture
def event_repo() -> FakeEventRepository:
    """Provide a fresh in-memory event repository."""
    return FakeEventRepository()


@pytest.fixture
def topic_repo() -> FakeTopicRepository:
    """Provide a fresh in-memory topic repository."""
    return FakeTopicRepository()


@pytest.fixture
def poll_repo() -> FakePollRepository:
    """Provide a fresh in-memory poll repository."""
    return FakePollRepository()


@pytest.fixture
def poll_response_repo() -> FakePollResponseRepository:
    """Provide a fresh in-memory poll response repository."""
    return FakePollResponseRepository()


@pytest.fixture
def participant_counter() -> FakeParticipantCounter:
    """Provide a fresh in-memory participant counter."""
    return FakeParticipantCounter()


@pytest.fixture
def use_case(
    event_repo: FakeEventRepository,
    topic_repo: FakeTopicRepository,
    poll_repo: FakePollRepository,
    poll_response_repo: FakePollResponseRepository,
    participant_counter: FakeParticipantCounter,
) -> GetEventStatsUseCase:
    """Provide a GetEventStatsUseCase wired to all fake dependencies."""
    return GetEventStatsUseCase(
        event_repository=event_repo,
        topic_repository=topic_repo,
        poll_repository=poll_repo,
        poll_response_repository=poll_response_repo,
        participant_counter=participant_counter,
    )


class TestGetEventStats:
    """Tests for GetEventStatsUseCase.execute."""

    def test_all_counts(
        self,
        event_repo: FakeEventRepository,
        topic_repo: FakeTopicRepository,
        participant_counter: FakeParticipantCounter,
        use_case: GetEventStatsUseCase,
    ) -> None:
        """Should return correct counts for participants, topics, and polls."""
        event = Event.create("Test Event", "123456")
        event_repo.create(event)
        channel = f"event:{event.code}"
        participant_counter.set_count(channel, 5)

        t1 = Topic.create("Topic 1", event_id=event.id)
        t2 = Topic.create("Topic 2", event_id=event.id)
        topic_repo.create(t1)
        topic_repo.create(t2)
        topic_repo.update_status(t2.id, TopicStatus.ARCHIVED)

        result = use_case.execute(event.id)

        assert result.participant_count == 5
        assert result.topic_count == 2
        assert result.active_topic_count == 1
        assert result.poll_count == 0
        assert result.has_active_poll is False
        assert result.total_poll_responses == 0

    def test_empty_event(
        self,
        event_repo: FakeEventRepository,
        use_case: GetEventStatsUseCase,
    ) -> None:
        """Should return zero counts for an event with no data."""
        event = Event.create("Empty Event", "654321")
        event_repo.create(event)

        result = use_case.execute(event.id)

        assert result.topic_count == 0
        assert result.poll_count == 0
        assert result.participant_count == 0
        assert result.active_topic_count == 0
        assert result.has_active_poll is False
        assert result.total_poll_responses == 0

    def test_not_found_raises(self, use_case: GetEventStatsUseCase) -> None:
        """Should raise EventNotFoundError when event does not exist."""
        with pytest.raises(EventNotFoundError):
            use_case.execute(uuid.uuid4())

    def test_participant_count_from_counter(
        self,
        event_repo: FakeEventRepository,
        participant_counter: FakeParticipantCounter,
        use_case: GetEventStatsUseCase,
    ) -> None:
        """Should read participant count using the event channel key."""
        event = Event.create("Channel Event", "111222")
        event_repo.create(event)
        participant_counter.set_count(f"event:{event.code}", 42)

        result = use_case.execute(event.id)

        assert result.participant_count == 42

    def test_active_topic_count_excludes_non_active(
        self,
        event_repo: FakeEventRepository,
        topic_repo: FakeTopicRepository,
        use_case: GetEventStatsUseCase,
    ) -> None:
        """Active topic count should only count ACTIVE status topics."""
        event = Event.create("Status Event", "333444")
        event_repo.create(event)

        active_topic = Topic.create("Active", event_id=event.id)
        highlighted_topic = Topic.create("Highlighted", event_id=event.id)
        answered_topic = Topic.create("Answered", event_id=event.id)
        archived_topic = Topic.create("Archived", event_id=event.id)

        topic_repo.create(active_topic)
        topic_repo.create(highlighted_topic)
        topic_repo.create(answered_topic)
        topic_repo.create(archived_topic)

        topic_repo.update_status(highlighted_topic.id, TopicStatus.HIGHLIGHTED)
        topic_repo.update_status(answered_topic.id, TopicStatus.ANSWERED)
        topic_repo.update_status(archived_topic.id, TopicStatus.ARCHIVED)

        result = use_case.execute(event.id)

        assert result.topic_count == 4
        assert result.active_topic_count == 1

    def test_has_active_poll_when_poll_is_active(
        self,
        event_repo: FakeEventRepository,
        poll_repo: FakePollRepository,
        use_case: GetEventStatsUseCase,
    ) -> None:
        """has_active_poll should be True when any poll is active."""
        event = Event.create("Poll Event", "555666")
        event_repo.create(event)

        poll = Poll.create(
            event_id=event.id,
            question="Vote?",
            option_texts=["Yes", "No"],
        )
        poll_repo.create(poll)
        poll_repo.update_active_status(poll.id, True)

        result = use_case.execute(event.id)

        assert result.poll_count == 1
        assert result.has_active_poll is True

    def test_result_is_frozen(
        self,
        event_repo: FakeEventRepository,
        use_case: GetEventStatsUseCase,
    ) -> None:
        """EventStatsResult should be immutable."""
        event = Event.create("Frozen Event", "777888")
        event_repo.create(event)

        result = use_case.execute(event.id)

        with pytest.raises(AttributeError):
            result.topic_count = 99  # type: ignore[misc]
