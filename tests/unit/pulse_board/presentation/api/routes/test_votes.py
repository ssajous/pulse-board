"""Tests for the votes API routes."""

import uuid

from fastapi.testclient import TestClient

from tests.unit.pulse_board.fakes import FakeEventPublisher


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


class TestCastVoteBroadcast:
    """Tests verifying that vote actions publish events."""

    def test_cast_vote_broadcasts_score_update(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """Casting a vote should publish a score_update event."""
        topic_id = _create_topic(client)

        client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "user-abc", "direction": "up"},
        )

        assert len(fake_publisher.score_updates) == 1
        event = fake_publisher.score_updates[0]
        assert str(event["topic_id"]) == topic_id
        assert event["score"] == 1

    def test_cast_vote_broadcasts_censure_on_threshold(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """Downvoting to censure threshold publishes score and censure."""
        topic_id = _create_topic(client)
        url = f"/api/topics/{topic_id}/votes"

        # Cast 5 downvotes from different users to reach -5
        for i in range(5):
            client.post(
                url,
                json={
                    "fingerprint_id": f"user-{i}",
                    "direction": "down",
                },
            )

        # Should have 5 score updates (one per vote)
        assert len(fake_publisher.score_updates) == 5

        # The last score update should show score == -5
        last_update = fake_publisher.score_updates[-1]
        assert last_update["score"] == -5

        # Censure event should be published when threshold is reached
        assert len(fake_publisher.censured_events) == 1
        assert str(fake_publisher.censured_events[0]["topic_id"]) == topic_id

    def test_cast_upvote_does_not_broadcast_censure(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """An upvote should not trigger a censure event."""
        topic_id = _create_topic(client)

        client.post(
            f"/api/topics/{topic_id}/votes",
            json={"fingerprint_id": "user-abc", "direction": "up"},
        )

        assert len(fake_publisher.censured_events) == 0
