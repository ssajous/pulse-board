"""Health check use case."""

from dataclasses import dataclass

from pulse_board.domain.ports.database_port import DatabasePort


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a health check operation."""

    status: str
    database: str


class HealthCheckUseCase:
    """Use case for checking application health."""

    def __init__(self, database: DatabasePort) -> None:
        self._database = database

    def execute(self) -> HealthCheckResult:
        """Execute the health check."""
        db_connected = self._database.is_connected()
        return HealthCheckResult(
            status="healthy" if db_connected else "degraded",
            database="connected" if db_connected else "disconnected",
        )
