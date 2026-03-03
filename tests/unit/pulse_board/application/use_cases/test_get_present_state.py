"""Tests for the get present state use case."""

import dataclasses
import uuid

import pytest

from pulse_board.application.use_cases.get_present_state import (
    GetPresentStateUseCase,
    PresentStateResult,
)
from pulse_board.domain.entities.event import Event
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.exceptions import EventNotFoundError
from tests.unit.pulse_board.fakes import (
    FakeEventRepository,
    FakeParticipantCounter,
    FakePollRepository,
    FakePollResponseRepository,
    FakeTopicRepository,
)


def _setup() -> tuple[
    GetPresentStateUseCase,
    FakeEventRepository,
    FakePollRepository,
    FakePollResponseRepository,
    FakeTopicRepository,
    FakeParticipantCounter,
]:
    """Create a GetPresentStateUseCase with fresh fake dependencies."""
    event_repo = FakeEventRepository()
    poll_repo = FakePollRepository()
    response_repo = FakePollResponseRepository()
    topic_repo = FakeTopicRepository()
    participant_counter = FakeParticipantCounter()
    use_case = GetPresentStateUseCase(
        event_repository=event_repo,
        poll_repository=poll_repo,
        poll_response_repository=response_repo,
        topic_repository=topic_repo,
        participant_counter=participant_counter,
    )
    return (
        use_case,
        event_repo,
        poll_repo,
        response_repo,
        topic_repo,
        participant_counter,
    )


def _create_event(
    event_repo: FakeEventRepository,
    title: str = "Test Event",
    code: str = "ABC123",
) -> Event:
    """Create and persist an event."""
    event = Event.create(title=title, code=code)
    return event_repo.create(event)


def _create_poll(
    poll_repo: FakePollRepository,
    event_id: uuid.UUID,
    question: str = "Favorite color?",
    option_texts: list[str] | None = None,
    active: bool = False,
) -> Poll:
    """Create and persist a poll, optionally activating it."""
    texts = option_texts or ["Red", "Blue", "Green"]
    poll = Poll.create(event_id=event_id, question=question, option_texts=texts)
    if active:
        poll = poll.activate()
    return poll_repo.create(poll)


def _create_topic(
    topic_repo: FakeTopicRepository,
    event_id: uuid.UUID,
    content: str = "Test topic",
    score: int = 0,
) -> Topic:
    """Create and persist a topic with a custom score."""
    topic = Topic.create(content=content, event_id=event_id)
    # Override score via dataclasses.replace since Topic.create always sets 0
    topic = dataclasses.replace(topic, score=score)
    topic_repo.create(topic)
    return topic


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


class TestGetPresentStateUseCase:
    """Tests for GetPresentStateUseCase.execute."""

    def test_returns_event_metadata(self) -> None:
        """Result should include event_id, event_title, and event_code."""
        use_case, event_repo, *_ = _setup()
        event = _create_event(event_repo, title="My Conference", code="XYZ999")

        result = use_case.execute(event.id)

        assert result.event_id == event.id
        assert result.event_title == "My Conference"
        assert result.event_code == "XYZ999"

    def test_no_active_poll_returns_none(self) -> None:
        """active_poll should be None when no poll is active for the event."""
        use_case, event_repo, poll_repo, *_ = _setup()
        event = _create_event(event_repo)
        # Create a poll but leave it inactive
        _create_poll(poll_repo, event.id, active=False)

        result = use_case.execute(event.id)

        assert result.active_poll is None

    def test_active_poll_with_results(self) -> None:
        """Result should include poll summary with votes when a poll is active."""
        use_case, event_repo, poll_repo, response_repo, topic_repo, _ = _setup()
        event = _create_event(event_repo)
        poll = _create_poll(
            poll_repo,
            event.id,
            question="Best framework?",
            option_texts=["Django", "FastAPI"],
            active=True,
        )
        django_id = poll.options[0].id
        _submit_response(response_repo, poll.id, django_id, "fp-1")
        _submit_response(response_repo, poll.id, django_id, "fp-2")

        result = use_case.execute(event.id)

        assert result.active_poll is not None
        assert result.active_poll.poll_id == poll.id
        assert result.active_poll.question == "Best framework?"
        assert result.active_poll.total_votes == 2
        assert len(result.active_poll.options) == 2

    def test_top_10_limit(self) -> None:
        """Only the top 10 topics by score should be returned."""
        use_case, event_repo, _, __, topic_repo, ___ = _setup()
        event = _create_event(event_repo)
        for i in range(15):
            _create_topic(topic_repo, event.id, content=f"Topic {i}", score=i)

        result = use_case.execute(event.id)

        assert len(result.top_topics) == 10

    def test_top_topics_sorted_by_score_desc(self) -> None:
        """Topics should be sorted with the highest score first."""
        use_case, event_repo, _, __, topic_repo, ___ = _setup()
        event = _create_event(event_repo)
        scores = [5, 1, 9, 3, 7]
        for i, score in enumerate(scores):
            _create_topic(topic_repo, event.id, content=f"Topic {i}", score=score)

        result = use_case.execute(event.id)

        returned_scores = [t.score for t in result.top_topics]
        assert returned_scores == sorted(returned_scores, reverse=True)

    def test_participant_count(self) -> None:
        """participant_count should reflect the value from the counter."""
        use_case, event_repo, _, __, ___, participant_counter = _setup()
        event = _create_event(event_repo, code="EVT001")
        participant_counter.set_count("event:EVT001", 42)

        result = use_case.execute(event.id)

        assert result.participant_count == 42

    def test_event_not_found_raises_error(self) -> None:
        """Should raise EventNotFoundError for a non-existent event_id."""
        use_case, *_ = _setup()
        missing_id = uuid.uuid4()

        with pytest.raises(EventNotFoundError):
            use_case.execute(missing_id)

    def test_result_is_frozen(self) -> None:
        """PresentStateResult should be immutable."""
        use_case, event_repo, *_ = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(event.id)

        assert isinstance(result, PresentStateResult)
        with pytest.raises((AttributeError, TypeError)):
            result.event_title = "Mutated"  # type: ignore[misc]

    def test_empty_topics_list(self) -> None:
        """top_topics should be an empty list when no topics exist for the event."""
        use_case, event_repo, *_ = _setup()
        event = _create_event(event_repo)

        result = use_case.execute(event.id)

        assert result.top_topics == []

    def test_channel_name_from_event_code(self) -> None:
        """Participant counter should be queried with 'event:{code}'."""
        use_case, event_repo, _, __, ___, participant_counter = _setup()
        event = _create_event(event_repo, code="JOIN42")
        participant_counter.set_count("event:JOIN42", 7)

        result = use_case.execute(event.id)

        assert result.participant_count == 7
        # Verify the wrong channel key returns 0 (counter was only set for correct key)
        assert participant_counter.get_channel_count("JOIN42") == 0

    def test_topics_from_other_events_excluded(self) -> None:
        """Topics belonging to other events should not appear in results."""
        use_case, event_repo, _, __, topic_repo, ___ = _setup()
        event_a = _create_event(event_repo, title="Event A", code="AAA111")
        event_b = _create_event(event_repo, title="Event B", code="BBB222")
        _create_topic(topic_repo, event_a.id, content="Topic for A", score=10)
        _create_topic(topic_repo, event_b.id, content="Topic for B", score=20)

        result = use_case.execute(event_a.id)

        assert len(result.top_topics) == 1
        assert result.top_topics[0].content == "Topic for A"

    def test_default_participant_count_zero(self) -> None:
        """participant_count should be 0 when no connections have been recorded."""
        use_case, event_repo, *_ = _setup()
        event = _create_event(event_repo, code="ZERO00")

        result = use_case.execute(event.id)

        assert result.participant_count == 0

    def test_active_poll_option_details(self) -> None:
        """Each option in active_poll.options should carry text and vote data."""
        use_case, event_repo, poll_repo, response_repo, topic_repo, _ = _setup()
        event = _create_event(event_repo)
        poll = _create_poll(
            poll_repo,
            event.id,
            option_texts=["Yes", "No"],
            active=True,
        )
        yes_id = poll.options[0].id
        _submit_response(response_repo, poll.id, yes_id, "fp-1")

        result = use_case.execute(event.id)

        assert result.active_poll is not None
        yes_opt = result.active_poll.options[0]
        assert yes_opt.text == "Yes"
        assert yes_opt.count == 1
        assert yes_opt.percentage == 100.0

        no_opt = result.active_poll.options[1]
        assert no_opt.text == "No"
        assert no_opt.count == 0
        assert no_opt.percentage == 0.0
