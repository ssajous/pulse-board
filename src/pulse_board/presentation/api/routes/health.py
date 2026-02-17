"""Health check route."""

from fastapi import APIRouter, Depends, Response

from pulse_board.application.use_cases.health_check import HealthCheckUseCase
from pulse_board.presentation.api.dependencies import get_health_check_use_case
from pulse_board.presentation.api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(
    use_case: HealthCheckUseCase = Depends(get_health_check_use_case),
    response: Response = Response(),
) -> HealthResponse:
    """Check application health status."""
    result = use_case.execute()
    if result.status == "degraded":
        response.status_code = 503
    return HealthResponse(status=result.status, database=result.database)
