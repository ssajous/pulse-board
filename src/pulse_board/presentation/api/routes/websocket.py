"""WebSocket route for real-time client connections."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pulse_board.infrastructure.websocket.connection_manager import (
    ConnectionManager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates.

    Accepts a WebSocket connection, registers it with the
    ConnectionManager, and keeps it alive until the client
    disconnects.  Inbound messages are ignored; the channel
    is server-to-client only.
    """
    manager: ConnectionManager = websocket.app.state.connection_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.warning("WebSocket connection error", exc_info=True)
    finally:
        await manager.disconnect(websocket)
