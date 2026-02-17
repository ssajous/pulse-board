"""Tests for the votes API routes."""

import uuid

from fastapi.testclient import TestClient


def _create_topic(client: TestClient, content: str = "Test topic") -> str:
    """Create a topic and return its id."""
    response = client.post("/api/topics", json={"content": content})
    return response.json()["id"]


class TestCastVoteRoute:
    """Tests for POST /api/topics/{topic_id}/votes."""

    def test_cast_upvote_returns_200(self, client: TestClient) -> None:
        """Should return 200 for a valid upvote."""
        topic_id = _create_topic(client)

        response = client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "user-abc", "direction": "up"},
        )

        assert response.status_code == 200

    def test_cast_downvote_returns_200(self, client: TestClient) -> None:
        """Should return 200 for a valid downvote."""
        topic_id = _create_topic(client)

        response = client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "user-xyz", "direction": "down"},
        )

        assert response.status_code == 200

    def test_cast_vote_response_body(self, client: TestClient) -> None:
        """Response should include all expected fields with correct values."""
        topic_id = _create_topic(client)

        response = client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "user-abc", "direction": "up"},
        )
        body = response.json()

        assert body["topic_id"] == topic_id
        assert body["new_score"] == 1
        assert body["vote_status"] == "created"
        assert body["user_vote"] == 1
        assert body["censured"] is False

    def test_cast_vote_not_found_returns_404(self, client: TestClient) -> None:
        """Should return 404 when the topic does not exist."""
        fake_id = str(uuid.uuid4())

        response = client.post(
            f"/api/topics/{fake_id}/votes",
            json={"fingerprint_id": "user-abc", "direction": "up"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Topic not found"

    def test_cast_vote_empty_fingerprint_returns_422(self, client: TestClient) -> None:
        """Should return 422 when fingerprint_id is empty."""
        topic_id = _create_topic(client)

        response = client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "", "direction": "up"},
        )

        assert response.status_code == 422

    def test_cast_vote_invalid_direction_returns_422(self, client: TestClient) -> None:
        """Should return 422 when direction is not 'up' or 'down'."""
        topic_id = _create_topic(client)

        response = client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "user-abc", "direction": "sideways"},
        )

        assert response.status_code == 422

    def test_cast_vote_toggle(self, client: TestClient) -> None:
        """Voting up then down should toggle the vote."""
        topic_id = _create_topic(client)
        vote_payload = {"fingerprint_id": "user-abc", "direction": "up"}
        url = f"/api/topics/{topic_id}/votes"

        # First vote: upvote
        client.post(url, json=vote_payload)

        # Second vote: downvote (toggle)
        response = client.post(
            url,
            json={"fingerprint_id": "user-abc", "direction": "down"},
        )
        body = response.json()

        assert body["vote_status"] == "toggled"
        assert body["user_vote"] == -1
        assert body["new_score"] == -1

    def test_cast_vote_cancel(self, client: TestClient) -> None:
        """Voting in the same direction twice should cancel the vote."""
        topic_id = _create_topic(client)
        vote_payload = {"fingerprint_id": "user-abc", "direction": "up"}
        url = f"/api/topics/{topic_id}/votes"

        # First vote: upvote
        client.post(url, json=vote_payload)

        # Second vote: same direction (cancel)
        response = client.post(url, json=vote_payload)
        body = response.json()

        assert body["vote_status"] == "cancelled"
        assert body["user_vote"] is None
        assert body["new_score"] == 0
