"""Tests for the WebSocket endpoint route."""

from fastapi.testclient import TestClient

from pulse_board.presentation.api.app import create_app


class TestWebSocketEndpoint:
    """Tests for the /ws WebSocket endpoint."""

    def test_websocket_connect_and_disconnect(self) -> None:
        """Should connect to /ws and disconnect without errors."""
        app = create_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as ws:
            # Connection established; close cleanly
            ws.close()

    def test_websocket_receives_broadcast(self) -> None:
        """Client should receive messages broadcast via the manager."""
        app = create_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as ws:
            # Access the manager from app state and broadcast
            manager = app.state.connection_manager
            # The TestClient runs sync, so we need to use
            # the broadcast through the manager directly.
            # In the TestClient context, the event loop is
            # managed internally.
            import asyncio

            asyncio.get_event_loop().run_until_complete(
                manager.broadcast({"type": "test", "payload": "hello"})
            )

            data = ws.receive_json()
            assert data == {"type": "test", "payload": "hello"}
