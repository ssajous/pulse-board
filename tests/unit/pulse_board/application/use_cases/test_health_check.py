"""Tests for the health check use case."""

import pytest

from pulse_board.application.use_cases.health_check import (
    HealthCheckResult,
    HealthCheckUseCase,
)
from pulse_board.domain.ports.database_port import DatabasePort


class FakeDatabaseConnected(DatabasePort):
    """Fake database that reports as connected."""

    def is_connected(self) -> bool:
        return True


class FakeDatabaseDisconnected(DatabasePort):
    """Fake database that reports as disconnected."""

    def is_connected(self) -> bool:
        return False


class TestHealthCheckUseCase:
    """Tests for HealthCheckUseCase."""

    def test_healthy_when_database_connected(self) -> None:
        """Should return healthy status when database is connected."""
        use_case = HealthCheckUseCase(database=FakeDatabaseConnected())
        result = use_case.execute()
        assert result == HealthCheckResult(status="healthy", database="connected")

    def test_degraded_when_database_disconnected(self) -> None:
        """Should return degraded status when database is disconnected."""
        use_case = HealthCheckUseCase(database=FakeDatabaseDisconnected())
        result = use_case.execute()
        assert result == HealthCheckResult(status="degraded", database="disconnected")

    def test_result_is_frozen(self) -> None:
        """Health check result should be immutable."""
        result = HealthCheckResult(status="healthy", database="connected")
        with pytest.raises(AttributeError):
            result.status = "changed"  # type: ignore[misc]
