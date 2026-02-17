"""FastAPI dependency injection wiring."""

from pulse_board.application.use_cases.health_check import HealthCheckUseCase
from pulse_board.infrastructure.database.connection import get_database


def get_health_check_use_case() -> HealthCheckUseCase:
    """Provide a HealthCheckUseCase instance."""
    database = get_database()
    return HealthCheckUseCase(database=database)
