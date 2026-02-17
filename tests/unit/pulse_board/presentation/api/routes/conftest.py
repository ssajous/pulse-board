"""Test fixtures for route tests."""

import pytest
from fastapi.testclient import TestClient

from pulse_board.application.use_cases.cast_vote import CastVoteUseCase
from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.list_topics import ListTopicsUseCase
from pulse_board.domain.services.voting_service import VotingService
from pulse_board.presentation.api.app import create_app
from pulse_board.presentation.api.dependencies import (
    get_cast_vote_use_case,
    get_create_topic_use_case,
    get_event_publisher,
    get_list_topics_use_case,
)
from tests.unit.pulse_board.fakes import (
    FakeEventPublisher,
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
def client(
    fake_repo: FakeTopicRepository,
    fake_vote_repo: FakeVoteRepository,
    fake_publisher: FakeEventPublisher,
) -> TestClient:
    """Provide a test client wired to fake repositories and publisher."""
    app = create_app()
    overrides = app.dependency_overrides
    overrides[get_create_topic_use_case] = lambda: CreateTopicUseCase(
        repository=fake_repo
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
    return TestClient(app)
