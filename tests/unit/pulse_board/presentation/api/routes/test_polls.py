"""Tests for the polls API routes."""

import uuid

from fastapi.testclient import TestClient

from tests.unit.pulse_board.fakes import (
    FakeEventPublisher,
    FakePollRepository,
)


def _create_event(client: TestClient) -> dict:
    """Create an event and return its response body."""
    response = client.post(
        "/api/events",
        json={"title": "Poll Event"},
    )
    return response.json()


def _create_poll(
    client: TestClient,
    event_id: str,
    question: str = "Favorite color?",
    options: list[str] | None = None,
) -> dict:
    """Create a poll and return its response body."""
    opts = options or ["Red", "Blue", "Green"]
    response = client.post(
        f"/api/events/{event_id}/polls",
        json={"question": question, "options": opts},
    )
    return response.json()


class TestCreatePollRoute:
    """Tests for POST /api/events/{event_id}/polls."""

    def test_create_poll_returns_201(self, client: TestClient) -> None:
        """Should return 201 for valid poll creation."""
        event = _create_event(client)

        response = client.post(
            f"/api/events/{event['id']}/polls",
            json={
                "question": "What is best?",
                "options": ["A", "B"],
            },
        )

        assert response.status_code == 201

    def test_create_poll_response_body(self, client: TestClient) -> None:
        """Response should include all poll fields."""
        event = _create_event(client)

        response = client.post(
            f"/api/events/{event['id']}/polls",
            json={
                "question": "Pick one",
                "options": ["Alpha", "Bravo", "Charlie"],
            },
        )
        body = response.json()

        assert body["question"] == "Pick one"
        assert body["event_id"] == event["id"]
        assert body["poll_type"] == "multiple_choice"
        assert body["is_active"] is False
        assert "id" in body
        assert "created_at" in body
        assert len(body["options"]) == 3
        assert body["options"][0]["text"] == "Alpha"

    def test_create_poll_event_not_found_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for unknown event_id."""
        missing_id = str(uuid.uuid4())

        response = client.post(
            f"/api/events/{missing_id}/polls",
            json={
                "question": "Orphan?",
                "options": ["A", "B"],
            },
        )

        assert response.status_code == 404

    def test_create_poll_empty_question_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for empty question."""
        event = _create_event(client)

        response = client.post(
            f"/api/events/{event['id']}/polls",
            json={"question": "", "options": ["A", "B"]},
        )

        assert response.status_code == 422

    def test_create_poll_too_few_options_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for fewer than 2 options."""
        event = _create_event(client)

        response = client.post(
            f"/api/events/{event['id']}/polls",
            json={"question": "Only one?", "options": ["Single"]},
        )

        assert response.status_code == 422

    def test_create_poll_too_many_options_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for more than 10 options."""
        event = _create_event(client)
        options = [f"Option {i}" for i in range(11)]

        response = client.post(
            f"/api/events/{event['id']}/polls",
            json={"question": "Too many?", "options": options},
        )

        assert response.status_code == 422


class TestListPollsRoute:
    """Tests for GET /api/events/{event_id}/polls."""

    def test_list_empty_returns_200(self, client: TestClient) -> None:
        """Should return 200 with empty polls list."""
        event = _create_event(client)

        response = client.get(f"/api/events/{event['id']}/polls")

        assert response.status_code == 200
        assert response.json()["polls"] == []

    def test_list_returns_created_polls(self, client: TestClient) -> None:
        """Should return all polls created for the event."""
        event = _create_event(client)
        _create_poll(client, event["id"], "Poll 1", ["A", "B"])
        _create_poll(client, event["id"], "Poll 2", ["X", "Y"])

        response = client.get(f"/api/events/{event['id']}/polls")
        polls = response.json()["polls"]

        assert len(polls) == 2
        questions = {p["question"] for p in polls}
        assert "Poll 1" in questions
        assert "Poll 2" in questions

    def test_list_does_not_include_other_event_polls(
        self,
        client: TestClient,
    ) -> None:
        """Should only return polls for the requested event."""
        event1 = _create_event(client)
        event2_resp = client.post(
            "/api/events",
            json={"title": "Other Event"},
        )
        event2 = event2_resp.json()
        _create_poll(client, event1["id"], "Event 1 Poll", ["A", "B"])
        _create_poll(client, event2["id"], "Event 2 Poll", ["X", "Y"])

        response = client.get(f"/api/events/{event1['id']}/polls")
        polls = response.json()["polls"]

        assert len(polls) == 1
        assert polls[0]["question"] == "Event 1 Poll"


class TestGetActivePollRoute:
    """Tests for GET /api/events/{event_id}/polls/active."""

    def test_no_active_poll_returns_204(self, client: TestClient) -> None:
        """Should return 204 when no poll is active."""
        event = _create_event(client)

        response = client.get(
            f"/api/events/{event['id']}/polls/active",
        )

        assert response.status_code == 204

    def test_active_poll_returns_200(
        self,
        client: TestClient,
    ) -> None:
        """Should return 200 with the active poll."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        # Activate the poll
        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )

        response = client.get(
            f"/api/events/{event['id']}/polls/active",
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == poll["id"]
        assert body["is_active"] is True

    def test_deactivated_poll_returns_204(
        self,
        client: TestClient,
    ) -> None:
        """Should return 204 after deactivating the only active poll."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )
        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": False},
        )

        response = client.get(
            f"/api/events/{event['id']}/polls/active",
        )

        assert response.status_code == 204


class TestActivatePollRoute:
    """Tests for PATCH /api/polls/{poll_id}/activate."""

    def test_activate_returns_200(self, client: TestClient) -> None:
        """Should return 200 on successful activation."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        response = client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_deactivate_returns_200(self, client: TestClient) -> None:
        """Should return 200 on successful deactivation."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )
        response = client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_activate_not_found_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for nonexistent poll."""
        missing_id = str(uuid.uuid4())

        response = client.patch(
            f"/api/polls/{missing_id}/activate",
            json={"activate": True},
        )

        assert response.status_code == 404

    def test_activate_broadcasts_poll_activated(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """Activating should broadcast a poll_activated event."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )

        assert len(fake_publisher.channel_poll_activated) == 1
        published = fake_publisher.channel_poll_activated[0]
        assert str(published["poll_id"]) == poll["id"]
        assert published["question"] == poll["question"]

    def test_deactivate_broadcasts_poll_deactivated(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """Deactivating should broadcast a poll_deactivated event."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )
        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": False},
        )

        assert len(fake_publisher.channel_poll_deactivated) == 1
        published = fake_publisher.channel_poll_deactivated[0]
        assert str(published["poll_id"]) == poll["id"]

    def test_activate_switches_active_poll(
        self,
        client: TestClient,
        fake_poll_repo: FakePollRepository,
    ) -> None:
        """Activating a new poll should deactivate the old one."""
        event = _create_event(client)
        poll1 = _create_poll(client, event["id"], "Poll 1", ["A", "B"])
        poll2 = _create_poll(client, event["id"], "Poll 2", ["X", "Y"])

        client.patch(
            f"/api/polls/{poll1['id']}/activate",
            json={"activate": True},
        )
        client.patch(
            f"/api/polls/{poll2['id']}/activate",
            json={"activate": True},
        )

        # Check poll1 is now inactive
        old = fake_poll_repo.get_by_id(uuid.UUID(poll1["id"]))
        assert old is not None
        assert old.is_active is False

        # Check poll2 is active
        new = fake_poll_repo.get_by_id(uuid.UUID(poll2["id"]))
        assert new is not None
        assert new.is_active is True


class TestSubmitPollResponseRoute:
    """Tests for POST /api/polls/{poll_id}/respond."""

    def _setup_active_poll(self, client: TestClient) -> dict:
        """Create an event with an active poll and return the poll body."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])
        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )
        return poll

    def test_submit_response_returns_201(
        self,
        client: TestClient,
    ) -> None:
        """Should return 201 for valid response submission."""
        poll = self._setup_active_poll(client)
        option_id = poll["options"][0]["id"]

        response = client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": option_id,
            },
        )

        assert response.status_code == 201

    def test_submit_response_body(self, client: TestClient) -> None:
        """Response should include all expected fields."""
        poll = self._setup_active_poll(client)
        option_id = poll["options"][0]["id"]

        response = client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": option_id,
            },
        )
        body = response.json()

        assert body["poll_id"] == poll["id"]
        assert body["option_id"] == option_id
        assert "id" in body
        assert "created_at" in body

    def test_poll_not_found_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for nonexistent poll."""
        missing_id = str(uuid.uuid4())
        option_id = str(uuid.uuid4())

        response = client.post(
            f"/api/polls/{missing_id}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": option_id,
            },
        )

        assert response.status_code == 404

    def test_poll_not_active_returns_409(
        self,
        client: TestClient,
    ) -> None:
        """Should return 409 for inactive poll."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])
        option_id = poll["options"][0]["id"]

        response = client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": option_id,
            },
        )

        assert response.status_code == 409

    def test_duplicate_response_returns_409(
        self,
        client: TestClient,
    ) -> None:
        """Should return 409 for duplicate fingerprint."""
        poll = self._setup_active_poll(client)
        option_id = poll["options"][0]["id"]

        client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": option_id,
            },
        )
        response = client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": poll["options"][1]["id"],
            },
        )

        assert response.status_code == 409

    def test_invalid_option_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for option not belonging to poll."""
        poll = self._setup_active_poll(client)
        bogus_option = str(uuid.uuid4())

        response = client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": bogus_option,
            },
        )

        assert response.status_code == 422

    def test_empty_fingerprint_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Should return 422 for empty fingerprint_id."""
        poll = self._setup_active_poll(client)
        option_id = poll["options"][0]["id"]

        response = client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "",
                "option_id": option_id,
            },
        )

        assert response.status_code == 422

    def test_submit_broadcasts_results_update(
        self,
        client: TestClient,
        fake_publisher: FakeEventPublisher,
    ) -> None:
        """Submitting a response should broadcast updated results."""
        poll = self._setup_active_poll(client)
        option_id = poll["options"][0]["id"]

        client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-abc",
                "option_id": option_id,
            },
        )

        assert len(fake_publisher.channel_poll_results_updated) == 1
        published = fake_publisher.channel_poll_results_updated[0]
        assert str(published["poll_id"]) == poll["id"]


class TestGetPollResultsRoute:
    """Tests for GET /api/polls/{poll_id}/results."""

    def test_results_returns_200(self, client: TestClient) -> None:
        """Should return 200 with results."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        response = client.get(f"/api/polls/{poll['id']}/results")

        assert response.status_code == 200

    def test_results_body_structure(self, client: TestClient) -> None:
        """Response should include all expected result fields."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        response = client.get(f"/api/polls/{poll['id']}/results")
        body = response.json()

        assert body["poll_id"] == poll["id"]
        assert body["question"] == "Favorite color?"
        assert body["total_votes"] == 0
        assert len(body["options"]) == 3
        for opt in body["options"]:
            assert "option_id" in opt
            assert "text" in opt
            assert "count" in opt
            assert "percentage" in opt

    def test_results_with_votes(self, client: TestClient) -> None:
        """Should return correct vote counts after submissions."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])
        option_id = poll["options"][0]["id"]

        # Activate and submit a response
        client.patch(
            f"/api/polls/{poll['id']}/activate",
            json={"activate": True},
        )
        client.post(
            f"/api/polls/{poll['id']}/respond",
            json={
                "fingerprint_id": "fp-1",
                "option_id": option_id,
            },
        )

        response = client.get(f"/api/polls/{poll['id']}/results")
        body = response.json()

        assert body["total_votes"] == 1

    def test_results_not_found_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for nonexistent poll."""
        missing_id = str(uuid.uuid4())

        response = client.get(f"/api/polls/{missing_id}/results")

        assert response.status_code == 404

    def test_results_zero_votes_percentages(
        self,
        client: TestClient,
    ) -> None:
        """All percentages should be 0.0 when no votes cast."""
        event = _create_event(client)
        poll = _create_poll(client, event["id"])

        response = client.get(f"/api/polls/{poll['id']}/results")
        body = response.json()

        for opt in body["options"]:
            assert opt["count"] == 0
            assert opt["percentage"] == 0.0
