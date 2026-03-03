"""Tests for the PollResponse domain entity."""

import uuid
from datetime import UTC, datetime

from pulse_board.domain.entities.poll_response import PollResponse


class TestPollResponseCreate:
    """Tests for PollResponse.create factory method."""

    def test_create_returns_response_with_generated_id(self) -> None:
        """Should generate a UUID id on creation."""
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-abc123",
            option_id=option_id,
        )

        assert isinstance(response.id, uuid.UUID)

    def test_create_sets_poll_id(self) -> None:
        """Should store the parent poll_id."""
        poll_id = uuid.uuid4()
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id="fp-abc123",
            option_id=option_id,
        )

        assert response.poll_id == poll_id

    def test_create_sets_fingerprint_id(self) -> None:
        """Should store the respondent fingerprint."""
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="device-xyz",
            option_id=option_id,
        )

        assert response.fingerprint_id == "device-xyz"

    def test_create_sets_option_id(self) -> None:
        """Should store the selected option_id."""
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            option_id=option_id,
        )

        assert response.option_id == option_id

    def test_create_builds_response_data_from_option_id(self) -> None:
        """Should auto-build response_data with the option_id."""
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            option_id=option_id,
        )

        assert response.response_data == {"option_id": str(option_id)}

    def test_create_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            option_id=option_id,
        )
        after = datetime.now(UTC)

        assert before <= response.created_at <= after

    def test_create_generates_unique_ids(self) -> None:
        """Each call to create should produce a different id."""
        poll_id = uuid.uuid4()
        option_id = uuid.uuid4()
        r1 = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id="fp-1",
            option_id=option_id,
        )
        r2 = PollResponse.create(
            poll_id=poll_id,
            fingerprint_id="fp-1",
            option_id=option_id,
        )

        assert r1.id != r2.id


class TestPollResponseSelectedOptionId:
    """Tests for PollResponse.selected_option_id property."""

    def test_selected_option_id_returns_uuid_from_response_data(self) -> None:
        """Should extract option UUID from response_data."""
        option_id = uuid.uuid4()
        response = PollResponse.create(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            option_id=option_id,
        )

        assert response.selected_option_id == option_id

    def test_selected_option_id_for_reconstituted_entity(self) -> None:
        """Should work for directly constructed entities."""
        option_id = uuid.uuid4()
        response = PollResponse(
            id=uuid.uuid4(),
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-recon",
            option_id=option_id,
            response_data={"option_id": str(option_id)},
            created_at=datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC),
        )

        assert response.selected_option_id == option_id


class TestPollResponseDirectConstruction:
    """Tests for direct dataclass construction (repository reconstitution)."""

    def test_direct_construction_preserves_all_fields(self) -> None:
        """Should allow direct construction without validation."""
        response_id = uuid.uuid4()
        poll_id = uuid.uuid4()
        option_id = uuid.uuid4()
        created_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        data = {"option_id": str(option_id)}

        response = PollResponse(
            id=response_id,
            poll_id=poll_id,
            fingerprint_id="fp-recon",
            option_id=option_id,
            response_data=data,
            created_at=created_at,
        )

        assert response.id == response_id
        assert response.poll_id == poll_id
        assert response.fingerprint_id == "fp-recon"
        assert response.option_id == option_id
        assert response.response_data == data
        assert response.created_at == created_at
