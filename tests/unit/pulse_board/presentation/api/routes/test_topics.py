"""Tests for the topics API routes."""

from fastapi.testclient import TestClient

from pulse_board.domain.entities.topic import MAX_CONTENT_LENGTH
from tests.unit.pulse_board.fakes import FakeTopicRepository


class TestCreateTopicRoute:
    """Tests for POST /api/topics."""

    def test_create_topic_returns_201(self, client: TestClient) -> None:
        """Should return 201 for valid topic creation."""
        response = client.post("/api/topics", json={"content": "New topic"})

        assert response.status_code == 201

    def test_create_topic_response_body(self, client: TestClient) -> None:
        """Response should include id, content, score, and created_at."""
        response = client.post("/api/topics", json={"content": "Body check"})
        body = response.json()

        assert body["content"] == "Body check"
        assert body["score"] == 0
        assert "id" in body
        assert "created_at" in body

    def test_create_empty_content_returns_422(self, client: TestClient) -> None:
        """Should return 422 for empty content."""
        response = client.post("/api/topics", json={"content": ""})

        assert response.status_code == 422

    def test_create_whitespace_only_returns_422(self, client: TestClient) -> None:
        """Should return 422 for whitespace-only content."""
        response = client.post("/api/topics", json={"content": "   "})

        assert response.status_code == 422

    def test_create_too_long_returns_422(self, client: TestClient) -> None:
        """Should return 422 when content exceeds max length."""
        content = "a" * (MAX_CONTENT_LENGTH + 1)
        response = client.post("/api/topics", json={"content": content})

        assert response.status_code == 422


class TestListTopicsRoute:
    """Tests for GET /api/topics."""

    def test_list_empty_returns_200(self, client: TestClient) -> None:
        """Should return 200 with empty topics list."""
        response = client.get("/api/topics")

        assert response.status_code == 200
        assert response.json()["topics"] == []

    def test_list_returns_topics(self, client: TestClient) -> None:
        """Should return created topics in the list."""
        client.post("/api/topics", json={"content": "Topic A"})
        client.post("/api/topics", json={"content": "Topic B"})

        response = client.get("/api/topics")
        topics = response.json()["topics"]

        assert len(topics) == 2

    def test_list_sorted_by_score_desc(
        self,
        client: TestClient,
        fake_repo: FakeTopicRepository,
    ) -> None:
        """Topics should be sorted by score descending."""
        # Create topics and manually set different scores
        client.post("/api/topics", json={"content": "Low score"})
        client.post("/api/topics", json={"content": "High score"})

        topics = fake_repo.list_active()
        topics[0].score = 1
        topics[1].score = 10

        response = client.get("/api/topics")
        result = response.json()["topics"]

        assert result[0]["content"] == "High score"
        assert result[1]["content"] == "Low score"

    def test_list_response_format(self, client: TestClient) -> None:
        """Response should have a 'topics' key wrapping the list."""
        response = client.get("/api/topics")
        body = response.json()

        assert "topics" in body
        assert isinstance(body["topics"], list)

    def test_create_and_list_roundtrip(self, client: TestClient) -> None:
        """A created topic should appear in the list response."""
        create_resp = client.post("/api/topics", json={"content": "Roundtrip topic"})
        created_id = create_resp.json()["id"]

        list_resp = client.get("/api/topics")
        topic_ids = [t["id"] for t in list_resp.json()["topics"]]

        assert created_id in topic_ids
