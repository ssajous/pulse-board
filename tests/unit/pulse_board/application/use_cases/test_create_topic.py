"""Tests for the create topic use case."""

import pytest

from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.domain.exceptions import ValidationError
from tests.unit.pulse_board.fakes import FakeTopicRepository


class TestCreateTopicUseCase:
    """Tests for CreateTopicUseCase."""

    def test_create_topic_success(self) -> None:
        """Should create a topic and return a result with all fields."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        result = use_case.execute("My new topic")

        assert result.content == "My new topic"
        assert result.score == 0
        assert result.id is not None
        assert result.created_at is not None

    def test_create_topic_result_is_frozen(self) -> None:
        """CreateTopicResult should be immutable."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)
        result = use_case.execute("test")

        with pytest.raises(AttributeError):
            result.content = "changed"  # type: ignore[misc]

    def test_create_topic_persists_to_repo(self) -> None:
        """Should persist the topic in the repository."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        result = use_case.execute("Persisted topic")

        saved = repo.get_by_id(result.id)
        assert saved is not None
        assert saved.content == "Persisted topic"

    def test_create_topic_strips_content(self) -> None:
        """Should strip whitespace from content before persisting."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        result = use_case.execute("  spaced out  ")

        assert result.content == "spaced out"

    def test_create_empty_content_raises_validation_error(self) -> None:
        """Should propagate ValidationError for empty content."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        with pytest.raises(ValidationError):
            use_case.execute("")

    def test_repo_not_touched_on_validation_error(self) -> None:
        """Repository should remain empty when validation fails."""
        repo = FakeTopicRepository()
        use_case = CreateTopicUseCase(repository=repo)

        with pytest.raises(ValidationError):
            use_case.execute("")

        assert repo.list_active() == []
