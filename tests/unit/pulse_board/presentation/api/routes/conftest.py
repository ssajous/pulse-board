"""Test fixtures for route tests."""

import pytest
from fastapi.testclient import TestClient

from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.list_topics import ListTopicsUseCase
from pulse_board.presentation.api.app import create_app
from pulse_board.presentation.api.dependencies import (
    get_create_topic_use_case,
    get_list_topics_use_case,
)
from tests.unit.pulse_board.fakes import FakeTopicRepository


@pytest.fixture
def fake_repo() -> FakeTopicRepository:
    """Provide a fresh in-memory topic repository."""
    return FakeTopicRepository()


@pytest.fixture
def client(fake_repo: FakeTopicRepository) -> TestClient:
    """Provide a test client wired to the fake repository."""
    app = create_app()
    app.dependency_overrides[get_create_topic_use_case] = lambda: CreateTopicUseCase(
        repository=fake_repo
    )
    app.dependency_overrides[get_list_topics_use_case] = lambda: ListTopicsUseCase(
        repository=fake_repo
    )
    return TestClient(app)
