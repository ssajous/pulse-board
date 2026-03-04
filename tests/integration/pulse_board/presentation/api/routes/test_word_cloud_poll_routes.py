"""Integration tests for word cloud poll API endpoints."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from pulse_board.application.use_cases.activate_poll import ActivatePollUseCase
from pulse_board.application.use_cases.create_poll import CreatePollUseCase
from pulse_board.application.use_cases.get_event import GetEventUseCase
from pulse_board.application.use_cases.get_poll_results import GetPollResultsUseCase
from pulse_board.application.use_cases.submit_poll_response import (
    SubmitPollResponseUseCase,
)
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
from pulse_board.presentation.api.app import create_app
from pulse_board.presentation.api.dependencies import (
    get_activate_poll_use_case,
    get_create_poll_use_case,
    get_event_publisher,
    get_get_event_use_case,
    get_get_poll_results_use_case,
    get_poll_repository,
    get_submit_poll_response_use_case,
)
from tests.unit.pulse_board.fakes import FakeEventPublisher

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
def cleanup_word_cloud_routes(
    session_factory: sessionmaker,  # type: ignore[type-arg]
) -> None:
    """Delete all test data in FK-safe order after each test."""
    yield
    with session_factory() as session:
        session.execute(text("DELETE FROM poll_responses"))
        session.execute(text("DELETE FROM polls"))
        session.execute(text("DELETE FROM events"))
        session.commit()


@pytest.fixture
def test_client(
    session_factory: sessionmaker,  # type: ignore[type-arg]
    cleanup_word_cloud_routes: None,
) -> TestClient:
    """Return a TestClient with dependency overrides using the test database."""
    app = create_app()
    publisher = FakeEventPublisher()

    def _event_repo() -> SQLAlchemyEventRepository:
        return SQLAlchemyEventRepository(session_factory=session_factory)

    def _poll_repo() -> SQLAlchemyPollRepository:
        return SQLAlchemyPollRepository(session_factory=session_factory)

    def _response_repo() -> SQLAlchemyPollResponseRepository:
        return SQLAlchemyPollResponseRepository(session_factory=session_factory)

    def _override_poll_repository() -> SQLAlchemyPollRepository:
        return _poll_repo()

    def _override_create_poll() -> CreatePollUseCase:
        return CreatePollUseCase(
            poll_repository=_poll_repo(),
            event_repository=_event_repo(),
        )

    def _override_activate_poll() -> ActivatePollUseCase:
        return ActivatePollUseCase(poll_repository=_poll_repo())

    def _override_submit_response() -> SubmitPollResponseUseCase:
        return SubmitPollResponseUseCase(
            poll_repository=_poll_repo(),
            poll_response_repository=_response_repo(),
        )

    def _override_get_poll_results() -> GetPollResultsUseCase:
        return GetPollResultsUseCase(
            poll_repository=_poll_repo(),
            poll_response_repository=_response_repo(),
        )

    def _override_get_event() -> GetEventUseCase:
        return GetEventUseCase(event_repository=_event_repo())

    async def _override_publisher() -> FakeEventPublisher:
        return publisher

    app.dependency_overrides[get_poll_repository] = _override_poll_repository
    app.dependency_overrides[get_create_poll_use_case] = _override_create_poll
    app.dependency_overrides[get_activate_poll_use_case] = _override_activate_poll
    app.dependency_overrides[get_submit_poll_response_use_case] = (
        _override_submit_response
    )
    app.dependency_overrides[get_get_poll_results_use_case] = _override_get_poll_results
    app.dependency_overrides[get_get_event_use_case] = _override_get_event
    app.dependency_overrides[get_event_publisher] = _override_publisher

    return TestClient(app)


@pytest.fixture
def event_repo(
    session_factory: sessionmaker,  # type: ignore[type-arg]
) -> SQLAlchemyEventRepository:
    """Provide an event repository using the test session factory."""
    return SQLAlchemyEventRepository(session_factory=session_factory)


@pytest.fixture
def created_event(
    event_repo: SQLAlchemyEventRepository,
    cleanup_word_cloud_routes: None,
) -> Event:
    """Create and persist a test event, cleaned up after each test."""
    event = Event.create(title="Word Cloud Route Test Event", code="WCRT01")
    event_repo.create(event)
    return event


class TestCreateWordCloudPoll:
    """Tests for POST /api/events/{event_id}/polls with poll_type=word_cloud."""

    def test_create_word_cloud_poll_returns_201(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Creating a word cloud poll should return HTTP 201."""
        response = test_client.post(
            f"/api/events/{created_event.id}/polls",
            json={
                "question": "Describe the session in one word",
                "poll_type": "word_cloud",
                "options": [],
            },
        )

        assert response.status_code == 201

    def test_create_word_cloud_poll_response_shape(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Created word cloud poll should have the expected JSON structure."""
        response = test_client.post(
            f"/api/events/{created_event.id}/polls",
            json={
                "question": "One word for this talk?",
                "poll_type": "word_cloud",
                "options": [],
            },
        )

        body = response.json()
        assert body["poll_type"] == "word_cloud"
        assert body["question"] == "One word for this talk?"
        assert body["event_id"] == str(created_event.id)
        assert body["is_active"] is False
        assert body["options"] == []
        assert "id" in body

    def test_create_word_cloud_poll_for_nonexistent_event_returns_404(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Creating a poll for a missing event should return HTTP 404."""
        import uuid

        response = test_client.post(
            f"/api/events/{uuid.uuid4()}/polls",
            json={
                "question": "Orphaned poll",
                "poll_type": "word_cloud",
                "options": [],
            },
        )

        assert response.status_code == 404


class TestSubmitWordCloudResponse:
    """Tests for POST /api/polls/{poll_id}/respond on word cloud polls."""

    def _create_and_activate_poll(
        self,
        test_client: TestClient,
        event_id: str,
        question: str = "One word?",
    ) -> str:
        """Helper: create and activate a word cloud poll, return its ID."""
        create_resp = test_client.post(
            f"/api/events/{event_id}/polls",
            json={
                "question": question,
                "poll_type": "word_cloud",
                "options": [],
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        activate_resp = test_client.patch(
            f"/api/polls/{poll_id}/activate",
            json={"activate": True},
        )
        assert activate_resp.status_code == 200
        return poll_id

    def test_submit_single_word_succeeds(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Submitting a single valid word should return HTTP 201."""
        poll_id = self._create_and_activate_poll(test_client, str(created_event.id))

        response = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-single-word",
                "response_value": "great",
            },
        )

        assert response.status_code == 201

    def test_submit_two_word_phrase_succeeds(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Submitting a two-word phrase should return HTTP 201."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Describe in 1-3 words"
        )

        response = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-two-words",
                "response_value": "very interesting",
            },
        )

        assert response.status_code == 201

    def test_submit_three_word_phrase_succeeds(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Submitting exactly 3 words should return HTTP 201."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Three word limit"
        )

        response = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-three-words",
                "response_value": "really loved it",
            },
        )

        assert response.status_code == 201

    def test_submit_more_than_three_words_fails_validation(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Submitting more than 3 words should return HTTP 422."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Word limit test"
        )

        response = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-too-many",
                "response_value": "this is way too long",
            },
        )

        assert response.status_code == 422

    def test_submit_response_returns_correct_schema(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Response body should contain id, poll_id, option_id, and created_at."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Schema check"
        )

        response = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-schema-check",
                "response_value": "awesome",
            },
        )

        body = response.json()
        assert "id" in body
        assert body["poll_id"] == poll_id
        assert body["option_id"] is None
        assert "created_at" in body

    def test_duplicate_response_returns_409(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """A second response from the same fingerprint should return HTTP 409."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Duplicate check"
        )

        first = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-dup-wc",
                "response_value": "cool",
            },
        )
        assert first.status_code == 201

        second = test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-dup-wc",
                "response_value": "cool",
            },
        )
        assert second.status_code == 409


class TestGetWordCloudResults:
    """Tests for GET /api/polls/{poll_id}/results on word cloud polls."""

    def _create_and_activate_poll(
        self,
        test_client: TestClient,
        event_id: str,
        question: str = "Word cloud results?",
    ) -> str:
        """Helper: create and activate a word cloud poll, return its ID."""
        create_resp = test_client.post(
            f"/api/events/{event_id}/polls",
            json={
                "question": question,
                "poll_type": "word_cloud",
                "options": [],
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        activate_resp = test_client.patch(
            f"/api/polls/{poll_id}/activate",
            json={"activate": True},
        )
        assert activate_resp.status_code == 200
        return poll_id

    def test_get_results_returns_200(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """GET results for an existing word cloud poll should return HTTP 200."""
        poll_id = self._create_and_activate_poll(test_client, str(created_event.id))

        response = test_client.get(f"/api/polls/{poll_id}/results")

        assert response.status_code == 200

    def test_get_results_empty_poll_has_zero_responses(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """A poll with no responses should return total_responses=0 and empty words."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Empty word cloud"
        )

        response = test_client.get(f"/api/polls/{poll_id}/results")
        body = response.json()

        assert body["total_responses"] == 0
        assert body["frequencies"] == []

    def test_get_results_response_shape(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Results response should contain poll_id, question, total_responses, words."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Shape check poll"
        )

        response = test_client.get(f"/api/polls/{poll_id}/results")
        body = response.json()

        assert body["poll_id"] == poll_id
        assert body["question"] == "Shape check poll"
        assert "total_responses" in body
        assert "frequencies" in body

    def test_get_results_reflects_submitted_responses(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Results should include words from submitted responses with correct counts."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Frequency check"
        )

        # Submit "great" twice and "good" once
        for i in range(2):
            resp = test_client.post(
                f"/api/polls/{poll_id}/respond",
                json={
                    "fingerprint_id": f"fp-great-{i}",
                    "response_value": "great",
                },
            )
            assert resp.status_code == 201

        test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-good-0",
                "response_value": "good",
            },
        )

        response = test_client.get(f"/api/polls/{poll_id}/results")
        body = response.json()

        assert body["total_responses"] == 3
        words_by_text = {w["text"]: w["count"] for w in body["frequencies"]}
        assert words_by_text.get("great") == 2
        assert words_by_text.get("good") == 1

    def test_get_results_words_sorted_by_count_desc(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """Words should be returned with the most frequent word first."""
        poll_id = self._create_and_activate_poll(
            test_client, str(created_event.id), question="Sort order check"
        )

        # "top" appears 3 times, "low" appears 1 time
        for i in range(3):
            test_client.post(
                f"/api/polls/{poll_id}/respond",
                json={
                    "fingerprint_id": f"fp-top-{i}",
                    "response_value": "top",
                },
            )
        test_client.post(
            f"/api/polls/{poll_id}/respond",
            json={
                "fingerprint_id": "fp-low-0",
                "response_value": "low",
            },
        )

        response = test_client.get(f"/api/polls/{poll_id}/results")
        body = response.json()

        assert body["frequencies"][0]["text"] == "top"
        assert body["frequencies"][0]["count"] == 3

    def test_get_results_for_nonexistent_poll_returns_404(
        self,
        test_client: TestClient,
        created_event: Event,
    ) -> None:
        """GET results for an unknown poll ID should return HTTP 404."""
        import uuid

        response = test_client.get(f"/api/polls/{uuid.uuid4()}/results")

        assert response.status_code == 404
