"""Test fixtures for route tests."""

import pytest
from fastapi.testclient import TestClient

from pulse_board.application.use_cases.cast_vote import CastVoteUseCase
from pulse_board.application.use_cases.create_event import (
    CreateEventUseCase,
)
from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.get_event import GetEventUseCase
from pulse_board.application.use_cases.join_event import JoinEventUseCase
from pulse_board.application.use_cases.list_event_topics import (
    ListEventTopicsUseCase,
)
from pulse_board.application.use_cases.list_topics import ListTopicsUseCase
from pulse_board.domain.services.join_code_generator import (
    JoinCodeGenerator,
)
from pulse_board.domain.services.voting_service import VotingService
from pulse_board.presentation.api.app import create_app
from pulse_board.presentation.api.dependencies import (
    get_cast_vote_use_case,
    get_create_event_use_case,
    get_create_topic_use_case,
    get_event_publisher,
    get_get_event_use_case,
    get_join_event_use_case,
    get_list_event_topics_use_case,
    get_list_topics_use_case,
)
from tests.unit.pulse_board.fakes import (
    FakeEventPublisher,
    FakeEventRepository,
    FakeTopicRepository,
    FakeVoteRepository,
)


@pytest.fixture
def fake_repo() -> FakeTopicRepository:
    """Provide a fresh in-memory topic repository."""
    return FakeTopicRepository()


@pytest.fixture
def fake_vote_repo() -> FakeVoteRepository:
    """Provide a fresh in-memory vote repository."""
    return FakeVoteRepository()


@pytest.fixture
def fake_publisher() -> FakeEventPublisher:
    """Provide a fresh in-memory event publisher."""
    return FakeEventPublisher()


@pytest.fixture
def fake_event_repo() -> FakeEventRepository:
    """Provide a fresh in-memory event repository."""
    return FakeEventRepository()


@pytest.fixture
def client(
    fake_repo: FakeTopicRepository,
    fake_vote_repo: FakeVoteRepository,
    fake_publisher: FakeEventPublisher,
    fake_event_repo: FakeEventRepository,
) -> TestClient:
    """Provide a test client wired to fake repositories and publisher."""
    app = create_app()
    overrides = app.dependency_overrides
    overrides[get_create_topic_use_case] = lambda: CreateTopicUseCase(
        repository=fake_repo,
        event_repository=fake_event_repo,
    )
    overrides[get_list_topics_use_case] = lambda: ListTopicsUseCase(
        repository=fake_repo
    )
    overrides[get_cast_vote_use_case] = lambda: CastVoteUseCase(
        vote_repo=fake_vote_repo,
        topic_repo=fake_repo,
        voting_service=VotingService(),
    )
    overrides[get_event_publisher] = lambda: fake_publisher
    overrides[get_create_event_use_case] = lambda: CreateEventUseCase(
        event_repository=fake_event_repo,
        code_generator=JoinCodeGenerator(),
    )
    overrides[get_join_event_use_case] = lambda: JoinEventUseCase(
        event_repository=fake_event_repo,
    )
    overrides[get_get_event_use_case] = lambda: GetEventUseCase(
        event_repository=fake_event_repo,
    )
    overrides[get_list_event_topics_use_case] = lambda: ListEventTopicsUseCase(
        repository=fake_repo,
    )
    return TestClient(app)
