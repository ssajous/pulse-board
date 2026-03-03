"""Tests for the PollResponse domain entity."""

import uuid
from datetime import UTC, datetime

import pytest

from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.domain.exceptions import ValidationError


class TestPollResponseCreate:
    """Tests for PollResponse.create factory method (multiple choice)."""

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


class TestPollResponseCreateRating:
    """Tests for PollResponse.create_rating factory method."""

    def test_create_rating_returns_response_with_generated_id(self) -> None:
        """Should generate a UUID id."""
        response = PollResponse.create_rating(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            rating=3,
        )

        assert isinstance(response.id, uuid.UUID)

    def test_create_rating_sets_option_id_to_none(self) -> None:
        """Rating responses should have option_id=None."""
        response = PollResponse.create_rating(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            rating=4,
        )

        assert response.option_id is None

    def test_create_rating_stores_rating_in_response_data(self) -> None:
        """Should store rating in response_data."""
        response = PollResponse.create_rating(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            rating=5,
        )

        assert response.response_data == {"rating": 5}

    def test_create_rating_accepts_all_valid_ratings(self) -> None:
        """Should accept ratings 1 through 5."""
        for rating in range(1, 6):
            response = PollResponse.create_rating(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                rating=rating,
            )
            assert response.response_data["rating"] == rating

    def test_create_rating_zero_raises_validation_error(self) -> None:
        """Should raise ValidationError for rating of 0."""
        with pytest.raises(ValidationError, match="between 1 and 5"):
            PollResponse.create_rating(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                rating=0,
            )

    def test_create_rating_six_raises_validation_error(self) -> None:
        """Should raise ValidationError for rating of 6."""
        with pytest.raises(ValidationError, match="between 1 and 5"):
            PollResponse.create_rating(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                rating=6,
            )

    def test_create_rating_negative_raises_validation_error(self) -> None:
        """Should raise ValidationError for negative rating."""
        with pytest.raises(ValidationError, match="between 1 and 5"):
            PollResponse.create_rating(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                rating=-1,
            )

    def test_create_rating_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        response = PollResponse.create_rating(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            rating=3,
        )
        after = datetime.now(UTC)

        assert before <= response.created_at <= after

    def test_create_rating_selected_option_id_is_none(self) -> None:
        """selected_option_id property should return None for rating responses."""
        response = PollResponse.create_rating(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            rating=3,
        )

        assert response.selected_option_id is None


class TestPollResponseCreateOpenText:
    """Tests for PollResponse.create_open_text factory method."""

    def test_create_open_text_returns_response_with_generated_id(self) -> None:
        """Should generate a UUID id."""
        response = PollResponse.create_open_text(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            text="Great session!",
        )

        assert isinstance(response.id, uuid.UUID)

    def test_create_open_text_sets_option_id_to_none(self) -> None:
        """Open-text responses should have option_id=None."""
        response = PollResponse.create_open_text(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            text="Some feedback",
        )

        assert response.option_id is None

    def test_create_open_text_stores_stripped_text_in_response_data(self) -> None:
        """Should strip and store text in response_data."""
        response = PollResponse.create_open_text(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            text="  hello world  ",
        )

        assert response.response_data == {"text": "hello world"}

    def test_create_open_text_empty_string_raises_validation_error(self) -> None:
        """Should raise ValidationError for empty text."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            PollResponse.create_open_text(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                text="",
            )

    def test_create_open_text_whitespace_only_raises_validation_error(self) -> None:
        """Should raise ValidationError for whitespace-only text."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            PollResponse.create_open_text(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                text="   ",
            )

    def test_create_open_text_too_long_raises_validation_error(self) -> None:
        """Should raise ValidationError for text exceeding 500 characters."""
        long_text = "a" * 501
        with pytest.raises(ValidationError, match="500 characters or fewer"):
            PollResponse.create_open_text(
                poll_id=uuid.uuid4(),
                fingerprint_id="fp-1",
                text=long_text,
            )

    def test_create_open_text_at_max_length_succeeds(self) -> None:
        """Should accept text of exactly 500 characters."""
        max_text = "a" * 500
        response = PollResponse.create_open_text(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            text=max_text,
        )

        assert response.response_data["text"] == max_text

    def test_create_open_text_sets_created_at_to_utc_now(self) -> None:
        """Should set created_at to approximately the current UTC time."""
        before = datetime.now(UTC)
        response = PollResponse.create_open_text(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            text="Good feedback",
        )
        after = datetime.now(UTC)

        assert before <= response.created_at <= after

    def test_create_open_text_selected_option_id_is_none(self) -> None:
        """selected_option_id property should return None for open-text responses."""
        response = PollResponse.create_open_text(
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-1",
            text="Some text",
        )

        assert response.selected_option_id is None


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

    def test_selected_option_id_returns_none_when_not_in_response_data(self) -> None:
        """Should return None when response_data has no option_id key."""
        response = PollResponse(
            id=uuid.uuid4(),
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-recon",
            option_id=None,
            response_data={"rating": 4},
            created_at=datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC),
        )

        assert response.selected_option_id is None


class TestPollResponseDirectConstruction:
    """Tests for direct dataclass construction (repository reconstitution)."""

    def test_direct_construction_preserves_all_fields(self) -> None:
        """Should allow direct construction without validation."""
        response_id = uuid.uuid4()
        poll_id = uuid.uuid4()
        option_id = uuid.uuid4()
        created_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        data: dict[str, object] = {"option_id": str(option_id)}

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

    def test_direct_construction_with_none_option_id(self) -> None:
        """Should allow None option_id for rating/open-text reconstitution."""
        response = PollResponse(
            id=uuid.uuid4(),
            poll_id=uuid.uuid4(),
            fingerprint_id="fp-recon",
            option_id=None,
            response_data={"text": "My feedback"},
            created_at=datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC),
        )

        assert response.option_id is None
        assert response.response_data == {"text": "My feedback"}
