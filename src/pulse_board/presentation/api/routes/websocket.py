"""WebSocket route for real-time client connections."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pulse_board.infrastructure.config.settings import get_settings
from pulse_board.infrastructure.websocket.connection_manager import (
    ConnectionManager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates.

    Validates the request origin against the allowed origins list
    before accepting. Rejects connections with close code 1008
    (Policy Violation) when the origin is not permitted.

    Once accepted, the connection is registered with the
    ConnectionManager and kept alive until the client disconnects.
    Inbound messages are ignored; the channel is server-to-client
    only.
    """
    settings = get_settings()
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.allowed_ws_origins:
        logger.warning(
            "WebSocket rejected: origin %s not in allowed list",
            origin,
        )
        await websocket.close(code=1008)
        return

    manager: ConnectionManager = websocket.app.state.connection_manager
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > settings.ws_max_size:
                logger.warning(
                    "Oversized WebSocket message (%d bytes), ignoring",
                    len(data),
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.warning("WebSocket connection error", exc_info=True)
    finally:
        await manager.disconnect(websocket)


@router.websocket("/ws/events/{code}")
async def event_websocket_endpoint(
    websocket: WebSocket,
    code: str,
) -> None:
    """WebSocket for event-scoped real-time updates.

    Validates the request origin, then registers the connection
    to a channel keyed by ``event:{code}``.  All topic and vote
    updates for that event are broadcast through this channel.
    """
    settings = get_settings()
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.allowed_ws_origins:
        logger.warning(
            "Event WebSocket rejected: origin %s not allowed",
            origin,
        )
        await websocket.close(code=1008)
        return

    manager: ConnectionManager = websocket.app.state.connection_manager
    channel = f"event:{code}"
    await manager.connect_to_channel(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > settings.ws_max_size:
                logger.warning(
                    "Oversized WebSocket message (%d bytes), ignoring",
                    len(data),
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.warning(
            "Event WebSocket connection error",
            exc_info=True,
        )
    finally:
        await manager.disconnect_from_channel(websocket, channel)
