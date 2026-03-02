"""Test utility routes for E2E testing."""

import logging
import re
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy import text

from pulse_board.infrastructure.config.settings import get_settings
from pulse_board.infrastructure.database.connection import (
    get_session_factory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test", tags=["test"])

_PRODUCTION_DB_PATTERNS = re.compile(
    r"\.rds\.amazonaws\.com|production|prod-db",
    re.IGNORECASE,
)


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
)
def reset_database(
    x_test_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Reset the database by clearing all test data.

    Deletes in FK-safe order: poll_responses, votes, polls,
    topics, events.  This endpoint is only available when
    PULSE_BOARD_TEST_MODE is enabled.
    """
    logger.warning("Test reset endpoint called")

    settings = get_settings()

    # Guard: never run against a production database
    db_url = settings.effective_database_url
    if _PRODUCTION_DB_PATTERNS.search(db_url):
        logger.warning("Test reset blocked: production database detected")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refusing to reset a production database",
        )

    # Guard: validate test token when secret is configured
    if settings.test_mode_secret:
        if x_test_token != settings.test_mode_secret:
            logger.warning("Test reset blocked: invalid or missing test token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing X-Test-Token header",
            )

    session_factory = get_session_factory()
    session = session_factory()
    try:
        session.execute(text("DELETE FROM poll_responses"))
        session.execute(text("DELETE FROM votes"))
        session.execute(text("DELETE FROM polls"))
        session.execute(text("DELETE FROM topics"))
        session.execute(text("DELETE FROM events"))
        session.commit()
        logger.info("Test reset: cleared all data")
        return {"status": "ok"}
    except Exception:
        session.rollback()
        logger.exception("Test reset failed")
        raise
    finally:
        session.close()
