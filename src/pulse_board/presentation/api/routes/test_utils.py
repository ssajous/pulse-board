"""Test utility routes for E2E testing."""

import logging
from typing import Any

from fastapi import APIRouter, status
from sqlalchemy import text

from pulse_board.infrastructure.database.connection import (
    get_session_factory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test", tags=["test"])


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
)
def reset_database() -> dict[str, Any]:
    """Reset the database by clearing all votes and topics.

    Deletes votes before topics to respect foreign key
    constraints. This endpoint is only available when
    PULSE_BOARD_TEST_MODE is enabled.
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        session.execute(text("DELETE FROM votes"))
        session.execute(text("DELETE FROM topics"))
        session.commit()
        logger.info("Test reset: cleared all votes and topics")
        return {"status": "ok"}
    except Exception:
        session.rollback()
        logger.exception("Test reset failed")
        raise
    finally:
        session.close()
