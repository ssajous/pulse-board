"""FastAPI application factory."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pulse_board.infrastructure.config.settings import get_settings
from pulse_board.infrastructure.websocket.connection_manager import (
    ConnectionManager,
)
from pulse_board.presentation.api.routes.health import (
    router as health_router,
)
from pulse_board.presentation.api.routes.topics import (
    router as topics_router,
)
from pulse_board.presentation.api.routes.votes import (
    router as votes_router,
)
from pulse_board.presentation.api.routes.websocket import (
    router as ws_router,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Community Pulse Board",
        description="Real-time community engagement platform",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.connection_manager = ConnectionManager()

    app.include_router(health_router)
    app.include_router(topics_router)
    app.include_router(votes_router)
    app.include_router(ws_router)

    if os.environ.get("PULSE_BOARD_TEST_MODE"):
        from pulse_board.presentation.api.routes.test_utils import (
            router as test_router,
        )

        app.include_router(test_router)
        logger = logging.getLogger(__name__)
        logger.warning("Test mode enabled: test utility endpoints active")

    return app
