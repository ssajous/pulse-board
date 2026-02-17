"""Application entry point for uvicorn."""

import uvicorn

from pulse_board.infrastructure.config.settings import get_settings


def main() -> None:
    """Start the application server."""
    settings = get_settings()
    uvicorn.run(
        "pulse_board.presentation.api.app:create_app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        factory=True,
    )


if __name__ == "__main__":
    main()
