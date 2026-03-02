"""Centralized domain exception-to-HTTP response mapping."""

import logging

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from pulse_board.domain.exceptions import (
    CodeGenerationError,
    DomainError,
    DuplicateVoteError,
    EntityNotFoundError,
    EventNotActiveError,
    EventNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

DOMAIN_EXCEPTION_STATUS_MAP: dict[type[DomainError], int] = {
    ValidationError: 422,
    EntityNotFoundError: 404,
    EventNotFoundError: 404,
    EventNotActiveError: 409,
    DuplicateVoteError: 409,
    CodeGenerationError: 500,
}


async def _domain_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Convert a domain exception to an appropriate HTTP response."""
    assert isinstance(exc, DomainError)
    status_code = DOMAIN_EXCEPTION_STATUS_MAP.get(type(exc), 500)
    if status_code >= 500:
        logger.error(
            "Domain error: %s",
            exc.message,
            exc_info=True,
        )
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized handlers for all domain exceptions."""
    for exc_type in DOMAIN_EXCEPTION_STATUS_MAP:
        app.add_exception_handler(exc_type, _domain_error_handler)
    app.add_exception_handler(DomainError, _domain_error_handler)
