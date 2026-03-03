"""Tests for the events API routes."""

import dataclasses
import uuid

from fastapi.testclient import TestClient

from pulse_board.domain.entities.event import EventStatus
from tests.unit.pulse_board.fakes import (
    FakeEventPublisher,
    FakeEventRepository,
)


class TestCreateEventRoute:
    """Tests for POST /api/events."""

    def test_create_event_returns_201(self, client: TestClient) -> None:
        """Should return 201 for valid event creation."""
        response = client.post(
            "/api/events",
            json={"title": "My Event"},
        )

        assert response.status_code == 201

    def test_create_event_response_body(
        self,
        client: TestClient,
    ) -> None:
        """Response should include all event fields."""
        response = client.post(
            "/api/events",
            json={"title": "Full Event", "description": "A desc"},
        )
        body = response.json()

        assert body["title"] == "Full Event"
        assert body["description"] == "A desc"
        assert body["status"] == "active"
        assert "id" in body
        assert "code" in body
        assert len(body["code"]) == 6
        assert "created_at" in body

    def test_create_event_with_dates(self, client: TestClient) -> None:
        """Should accept optional start_date and end_date."""
        response = client.post(
            "/api/events",
            json={
                "title": "Dated Event",
                "start_date": "2026-06-01T09:00:00Z",
                "end_date": "2026-06-01T17:00:00Z",
            },
        )
        body = response.json()

        assert response.status_code == 201
        assert body["start_date"] is not None
        assert body["end_date"] is not None

    def test_create_event_with_creator_fingerprint(
        self,
        client: TestClient,
    ) -> None:
        """Should accept and persist creator_fingerprint field."""
        response = client.post(
            "/api/events",
            json={
                "title": "My Event",
                "creator_fingerprint": "fp123",
            },
        )

        assert response.status_code == 201

    def test_create_event_returns_creator_token(
        self,
        client: TestClient,
    ) -> None:
        """Response should include a non-null creator_token."""
        response = client.post(
            "/api/events",
            json={"title": "Token Event"},
        )
        body = response.json()

        assert response.status_code == 201
        assert "creator_token" in body
        assert body["creator_token"] is not None
        assert len(body["creator_token"]) > 0

    def test_create_event_empty_title_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for empty title."""
        response = client.post(
            "/api/events",
            json={"title": ""},
        )

        assert response.status_code == 422


class TestJoinEventRoute:
    """Tests for GET /api/events/join/{code}."""

    def test_join_active_event(
        self,
        client: TestClient,
    ) -> None:
        """Should return event details for valid join code."""
        # Create an event first
        create_resp = client.post(
            "/api/events",
            json={"title": "Joinable Event"},
        )
        code = create_resp.json()["code"]

        response = client.get(f"/api/events/join/{code}")

        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Joinable Event"
        assert body["code"] == code

    def test_join_nonexistent_code_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for unknown join code."""
        response = client.get("/api/events/join/000000")

        assert response.status_code == 404

    def test_join_closed_event_returns_409(
        self,
        client: TestClient,
        fake_event_repo: FakeEventRepository,
    ) -> None:
        """Should return 409 for closed events."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Closed Event"},
        )
        event_id = uuid.UUID(create_resp.json()["id"])
        code = create_resp.json()["code"]

        # Close the event
        event = fake_event_repo.get_by_id(event_id)
        assert event is not None
        closed = dataclasses.replace(event, status=EventStatus.CLOSED)
        fake_event_repo._events[event_id] = closed

        response = client.get(f"/api/events/join/{code}")

        assert response.status_code == 409


class TestGetEventRoute:
    """Tests for GET /api/events/{event_id}."""

    def test_get_existing_event(self, client: TestClient) -> None:
        """Should return event details for valid event_id."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Retrievable Event"},
        )
        event_id = create_resp.json()["id"]

        response = client.get(f"/api/events/{event_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Retrievable Event"
        assert body["id"] == event_id

    def test_get_nonexistent_event_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for unknown event_id."""
        missing_id = uuid.uuid4()
        response = client.get(f"/api/events/{missing_id}")

        assert response.status_code == 404


class TestListEventTopicsRoute:
    """Tests for GET /api/events/{event_id}/topics."""

    def test_list_empty_returns_200(
        self,
        client: TestClient,
    ) -> None:
        """Should return 200 with empty topics list."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Empty Event"},
        )
        event_id = create_resp.json()["id"]

        response = client.get(f"/api/events/{event_id}/topics")

        assert response.status_code == 200
        assert response.json()["topics"] == []

    def test_list_returns_event_topics(
        self,
        client: TestClient,
    ) -> None:
        """Should return topics created for the event."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Topic Event"},
        )
        event_id = create_resp.json()["id"]

        client.post(
            f"/api/events/{event_id}/topics",
            json={"content": "Event Topic 1"},
        )
        client.post(
            f"/api/events/{event_id}/topics",
            json={"content": "Event Topic 2"},
        )

        response = client.get(f"/api/events/{event_id}/topics")
        topics = response.json()["topics"]

        assert len(topics) == 2


class TestCreateEventTopicRoute:
    """Tests for POST /api/events/{event_id}/topics."""

    def test_create_event_topic_returns_201(
        self,
        client: TestClient,
    ) -> None:
        """Should return 201 for valid topic creation in event."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Topic Event"},
        )
        event_id = create_resp.json()["id"]

        response = client.post(
            f"/api/events/{event_id}/topics",
            json={"content": "Event topic content"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["content"] == "Event topic content"
        assert body["score"] == 0

    def test_create_topic_for_nonexistent_event_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for unknown event_id."""
        missing_id = uuid.uuid4()
        response = client.post(
            f"/api/events/{missing_id}/topics",
            json={"content": "Orphan topic"},
        )

        assert response.status_code == 404

    def test_create_topic_for_closed_event_returns_409(
        self,
        client: TestClient,
        fake_event_repo: FakeEventRepository,
    ) -> None:
        """Should return 409 for closed events."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Will Close"},
        )
        event_id = uuid.UUID(create_resp.json()["id"])

        # Close the event
        event = fake_event_repo.get_by_id(event_id)
        assert event is not None
        closed = dataclasses.replace(event, status=EventStatus.CLOSED)
        fake_event_repo._events[event_id] = closed

        response = client.post(
            f"/api/events/{event_id}/topics",
            json={"content": "Late topic"},
        )

        assert response.status_code == 409

    def test_create_event_topic_broadcasts(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """Creating an event topic should broadcast via channel."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Broadcast Event"},
        )
        event_id = create_resp.json()["id"]

        client.post(
            f"/api/events/{event_id}/topics",
            json={"content": "Broadcast topic"},
        )

        assert len(fake_publisher.channel_new_topic_events) == 1
        published = fake_publisher.channel_new_topic_events[0]
        assert published["content"] == "Broadcast topic"

    def test_create_empty_content_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for empty content."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Validation Event"},
        )
        event_id = create_resp.json()["id"]

        response = client.post(
            f"/api/events/{event_id}/topics",
            json={"content": ""},
        )

        assert response.status_code == 422


class TestCheckCreatorRoute:
    """Tests for GET /api/events/{event_id}/check-creator."""

    def test_check_creator_matching_fingerprint(
        self,
        client: TestClient,
    ) -> None:
        """Should return is_creator=True when creator_token matches."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Creator Event"},
        )
        body = create_resp.json()
        event_id = body["id"]
        creator_token = body["creator_token"]

        response = client.get(
            f"/api/events/{event_id}/check-creator",
            params={"creator_token": creator_token},
        )

        assert response.status_code == 200
        assert response.json()["is_creator"] is True

    def test_check_creator_mismatched_fingerprint(
        self,
        client: TestClient,
    ) -> None:
        """Should return is_creator=False when creator_token does not match."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Creator Event"},
        )
        event_id = create_resp.json()["id"]

        response = client.get(
            f"/api/events/{event_id}/check-creator",
            params={"creator_token": "wrong-token"},
        )

        assert response.status_code == 200
        assert response.json()["is_creator"] is False

    def test_check_creator_wrong_token_returns_false(
        self,
        client: TestClient,
    ) -> None:
        """Should return is_creator=False when a wrong token is supplied."""
        create_resp = client.post(
            "/api/events",
            json={"title": "Token Event"},
        )
        event_id = create_resp.json()["id"]

        response = client.get(
            f"/api/events/{event_id}/check-creator",
            params={"creator_token": "definitely-wrong-token"},
        )

        assert response.status_code == 200
        assert response.json()["is_creator"] is False

    def test_check_creator_nonexistent_event_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for nonexistent event."""
        missing_id = uuid.uuid4()

        response = client.get(
            f"/api/events/{missing_id}/check-creator",
            params={"creator_token": "some-token"},
        )

        assert response.status_code == 404
