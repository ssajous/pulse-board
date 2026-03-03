"""Integration tests for the GET /api/events/{event_id}/present-state endpoint."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from pulse_board.application.use_cases.get_present_state import GetPresentStateUseCase
from pulse_board.domain.entities.event import Event
from pulse_board.infrastructure.database.base import Base
from pulse_board.infrastructure.repositories.event_repository import (
    SQLAlchemyEventRepository,
)
from pulse_board.infrastructure.repositories.poll_repository import (
    SQLAlchemyPollRepository,
)
from pulse_board.infrastructure.repositories.poll_response_repository import (
    SQLAlchemyPollResponseRepository,
)
from pulse_board.infrastructure.repositories.topic_repository import (
    SQLAlchemyTopicRepository,
)
from pulse_board.presentation.api.app import create_app
from pulse_board.presentation.api.dependencies import (
    get_get_present_state_use_case,
)
from tests.unit.pulse_board.fakes import FakeParticipantCounter

_DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://pulse:pulse_dev_password@localhost:5433/pulse_board"
)


@pytest.fixture(scope="module")
def db_engine() -> Engine:
    """Create a test database engine for this module."""
    url = os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="module")
def session_factory(db_engine: Engine) -> sessionmaker:  # type: ignore[type-arg]
    """Provide a session factory bound to the test engine."""
    return sessionmaker(bind=db_engine)


@pytest.fixture
def cleanup_present_state(session_factory: sessionmaker) -> None:  # type: ignore[type-arg]
    """Delete all test data in FK-safe order after each test."""
    yield
    with session_factory() as session:
        session.execute(text("DELETE FROM poll_responses"))
        session.execute(text("DELETE FROM polls"))
        session.execute(text("DELETE FROM topics"))
        session.execute(text("DELETE FROM events"))
        session.commit()


@pytest.fixture
def test_client(
    session_factory: sessionmaker,  # type: ignore[type-arg]
    cleanup_present_state: None,
) -> TestClient:
    """Return a TestClient with the dependency overridden to use test DB."""
    app = create_app()
    participant_counter = FakeParticipantCounter()

    def _override_use_case() -> GetPresentStateUseCase:
        return GetPresentStateUseCase(
            event_repository=SQLAlchemyEventRepository(session_factory=session_factory),
            poll_repository=SQLAlchemyPollRepository(session_factory=session_factory),
            poll_response_repository=SQLAlchemyPollResponseRepository(
                session_factory=session_factory
            ),
            topic_repository=SQLAlchemyTopicRepository(session_factory=session_factory),
            participant_counter=participant_counter,
        )

    app.dependency_overrides[get_get_present_state_use_case] = _override_use_case
    return TestClient(app)


@pytest.fixture
def event_repo(
    session_factory: sessionmaker,  # type: ignore[type-arg]
) -> SQLAlchemyEventRepository:
    """Provide an event repository using the test session factory."""
    return SQLAlchemyEventRepository(session_factory=session_factory)


class TestGetPresentStateEndpoint:
    """Integration tests for GET /api/events/{event_id}/present-state."""

    def test_get_present_state_event_not_found(self, test_client: TestClient) -> None:
        """Should return 404 when the event does not exist."""
        random_id = uuid.uuid4()

        response = test_client.get(f"/api/events/{random_id}/present-state")

        assert response.status_code == 404

    def test_get_present_state_returns_200(
        self,
        test_client: TestClient,
        event_repo: SQLAlchemyEventRepository,
    ) -> None:
        """Should return 200 with valid event metadata for an existing event."""
        event = Event.create(title="Integration Test Event", code="INT001")
        event_repo.create(event)

        response = test_client.get(f"/api/events/{event.id}/present-state")

        assert response.status_code == 200

    def test_get_present_state_response_shape(
        self,
        test_client: TestClient,
        event_repo: SQLAlchemyEventRepository,
    ) -> None:
        """Response JSON should contain all required top-level fields."""
        event = Event.create(title="Shape Test Event", code="SHP002")
        event_repo.create(event)

        response = test_client.get(f"/api/events/{event.id}/present-state")
        body = response.json()

        assert body["event_id"] == str(event.id)
        assert body["event_title"] == "Shape Test Event"
        assert body["event_code"] == "SHP002"
        assert body["active_poll"] is None
        assert body["top_topics"] == []
        assert body["participant_count"] == 0

    def test_get_present_state_invalid_uuid(self, test_client: TestClient) -> None:
        """Should return 422 when the event_id path parameter is not a UUID."""
        response = test_client.get("/api/events/not-a-uuid/present-state")

        assert response.status_code == 422
