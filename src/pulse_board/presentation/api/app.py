"""FastAPI application factory."""

import logging
import os
from pathlib import Path

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
        openapi_tags=[
            {
                "name": "health",
                "description": "Application health monitoring",
            },
            {
                "name": "topics",
                "description": "Topic creation and listing",
            },
            {
                "name": "votes",
                "description": "Voting on topics",
            },
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    app.state.connection_manager = ConnectionManager(
        max_connections=settings.ws_max_connections,
        max_connections_per_ip=settings.ws_max_connections_per_ip,
    )

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

    # Serve static frontend assets in production Docker builds
    static_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "static"
    if static_dir.is_dir():
        from fastapi.staticfiles import StaticFiles
        from starlette.responses import FileResponse

        app.mount(
            "/assets",
            StaticFiles(directory=str(static_dir / "assets")),
            name="static-assets",
        )

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str) -> FileResponse:
            """Serve index.html for SPA client-side routing."""
            return FileResponse(str(static_dir / "index.html"))

    return app
