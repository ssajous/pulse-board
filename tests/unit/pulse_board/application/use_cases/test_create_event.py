"""Tests for the create event use case."""

import uuid
from datetime import UTC, datetime

import pytest

from pulse_board.application.use_cases.create_event import (
    CreateEventResult,
    CreateEventUseCase,
)
from pulse_board.domain.entities.event import EventStatus
from pulse_board.domain.exceptions import (
    CodeGenerationError,
    ValidationError,
)
from pulse_board.domain.services.join_code_generator import (
    JoinCodeGenerator,
)
from tests.unit.pulse_board.fakes import FakeEventRepository


class TestCreateEventUseCase:
    """Tests for CreateEventUseCase.execute."""

    def test_creates_event_successfully(self) -> None:
        """Should create an event and return a result with all fields."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )

        result = use_case.execute("My Event")

        assert isinstance(result, CreateEventResult)
        assert result.title == "My Event"
        assert result.status == EventStatus.ACTIVE
        assert result.id is not None
        assert result.code is not None
        assert len(result.code) == 6
        assert result.created_at is not None

    def test_creates_event_with_description(self) -> None:
        """Should store optional description."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )

        result = use_case.execute(
            "Event with Desc",
            description="A description",
        )

        assert result.description == "A description"

    def test_creates_event_with_dates(self) -> None:
        """Should store optional start and end dates."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )
        start = datetime(2026, 6, 1, 9, 0, 0, tzinfo=UTC)
        end = datetime(2026, 6, 1, 17, 0, 0, tzinfo=UTC)

        result = use_case.execute(
            "Dated Event",
            start_date=start,
            end_date=end,
        )

        assert result.start_date == start
        assert result.end_date == end

    def test_persists_event_to_repository(self) -> None:
        """Should persist the event in the repository."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )

        result = use_case.execute("Persisted Event")

        saved = repo.get_by_id(result.id)
        assert saved is not None
        assert saved.title == "Persisted Event"

    def test_empty_title_raises_validation_error(self) -> None:
        """Should propagate ValidationError for empty title."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )

        with pytest.raises(ValidationError):
            use_case.execute("")

    def test_result_is_frozen(self) -> None:
        """CreateEventResult should be immutable."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )
        result = use_case.execute("Frozen Event")

        with pytest.raises(AttributeError):
            result.title = "changed"  # type: ignore[misc]

    def test_description_defaults_to_none(self) -> None:
        """Should default description to None when not provided."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )

        result = use_case.execute("No Desc")

        assert result.description is None

    def test_dates_default_to_none(self) -> None:
        """Should default dates to None when not provided."""
        repo = FakeEventRepository()
        generator = JoinCodeGenerator()
        use_case = CreateEventUseCase(
            event_repository=repo,
            code_generator=generator,
        )

        result = use_case.execute("No Dates")

        assert result.start_date is None
        assert result.end_date is None
