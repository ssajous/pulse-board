"""Tests for the PollResponse domain entity."""

import uuid
from datetime import UTC, datetime

from pulse_board.domain.entities.poll_response import PollResponse


class TestPollResponseCreate:
    """Tests for PollResponse.create factory method."""

    def test_create_returns_response_with_generated_id(self) -> None:
        """Should generate a UUID id on creation."""
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-abc123",
        )

        assert isinstance(response.id, uuid.UUID)

    def test_create_sets_poll_id(self) -> None:
        """Should store the parent poll_id."""
        poll_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id="fp-abc123",
        )

        assert response.poll_id == poll_id

    def test_create_sets_fingerprint_id(self) -> None:
        """Should store the respondent fingerprint."""
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="device-xyz",
        )

        assert response.fingerprint_id == "device-xyz"

    def test_create_defaults_response_data_to_empty_dict(self) -> None:
        """Should default response_data to an empty dict when None."""
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
        )

        assert response.response_data == {}

    def test_create_preserves_provided_response_data(self) -> None:
        """Should use the provided response_data dict."""
        data = {"choice": "option_a", "comment": "Great!"}
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            response_data=data,
        )

        assert response.response_data == data

    def test_create_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
        )
        after = datetime.now(UTC)

        assert before <= response.created_at <= after

    def test_create_generates_unique_ids(self) -> None:
        """Each call to create should produce a different id."""
        poll_id = uuid.uuid4()
        r1 = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id="fp-1",
        )
        r2 = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id="fp-1",
        )

        assert r1.id != r2.id


class TestPollResponseDirectConstruction:
    """Tests for direct dataclass construction (repository reconstitution)."""

    def test_direct_construction_preserves_all_fields(self) -> None:
        """Should allow direct construction without validation."""
        response_id = uuid.uuid4()
        poll_id = uuid.uuid4()
        created_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        data = {"answer": "42"}

        response = PollResponse(
            id=response_id,
            poll_id=poll_id,
            fingerprint_id="fp-recon",
            response_data=data,
            created_at=created_at,
        )

        assert response.id == response_id
        assert response.poll_id == poll_id
        assert response.fingerprint_id == "fp-recon"
        assert response.response_data == data
        assert response.created_at == created_at
