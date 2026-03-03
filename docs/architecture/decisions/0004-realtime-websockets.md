# ADR 004: Real-Time Updates -- Starlette Native WebSockets

## Status

Accepted

## Date

2024-12-01

## Context and Problem Statement

The Community Pulse Board must deliver real-time updates to connected clients when topic scores change, new topics are created, or topics are censured by the community. Multiple users viewing the board simultaneously need to see vote results reflected immediately without manual page refreshes. The real-time transport must integrate cleanly with the existing FastAPI backend and support broadcasting events from server to all connected clients.

## Decision Drivers

- **No external dependencies**: Avoid introducing additional infrastructure services (message brokers, Redis Pub/Sub) for a single-server deployment
- **Framework integration**: The solution must work natively within FastAPI without requiring a separate ASGI application or process
- **Simplicity**: Minimize operational complexity -- fewer moving parts reduce deployment and debugging overhead
- **Bidirectional capability**: While the current use case is primarily server-to-client, the transport should support future client-to-server messaging if needed
- **Performance**: The solution must efficiently broadcast events to hundreds of concurrent connections without blocking the main event loop
- **Connection management**: The solution must handle connection lifecycle (connect, disconnect, dead connection cleanup) reliably

## Considered Options

1. Starlette native WebSockets (built into FastAPI)
2. Socket.IO (via `python-socketio`)
3. Server-Sent Events (SSE)
4. HTTP polling (short or long polling)
5. Redis Pub/Sub with an external message broker

## Decision Outcome

We chose **Option 1: Starlette native WebSockets** because they are built directly into FastAPI's ASGI layer, requiring zero additional dependencies or infrastructure services. The implementation consists of a `ConnectionManager` class (see `infrastructure/websocket/connection_manager.py`) that implements the `EventPublisher` domain port, and a single WebSocket route at `/ws` (see `presentation/api/routes/websocket.py`). This design keeps real-time event publishing within the onion architecture -- use cases call the abstract `EventPublisher` port, and the `ConnectionManager` infrastructure adapter handles the actual WebSocket broadcasting.

### Consequences

- **Good**: Zero additional dependencies -- WebSocket support comes from Starlette, which is already a transitive dependency of FastAPI.
- **Good**: The `ConnectionManager` implements the `EventPublisher` port (ABC), maintaining clean separation between domain events and transport mechanism.
- **Good**: Async `broadcast()` sends messages to all connected clients concurrently on the same event loop that handles HTTP requests.
- **Good**: Built-in connection limits (configurable `max_connections` and `max_connections_per_ip`) prevent resource exhaustion from connection flooding.
- **Good**: Origin validation in the WebSocket route rejects connections from unauthorized origins (close code 1008), providing basic security.
- **Good**: Dead connections are automatically detected and removed during broadcast, preventing memory leaks from abandoned connections.
- **Bad**: Single-server architecture -- the in-memory `ConnectionManager` does not synchronize state across multiple server instances, limiting horizontal scaling.
- **Bad**: No automatic reconnection or message buffering on the server side -- if a client disconnects and reconnects, it misses events that occurred during the gap (mitigated by client-side reconnect handler that re-fetches all topics).
- **Bad**: Connection management (the `asyncio.Lock`, connection set, dead connection cleanup) is application code that must be maintained and tested.
- **Neutral**: The WebSocket channel is primarily server-to-client; inbound messages from clients are received but intentionally ignored (the receive loop exists only to detect disconnection).

## Pros and Cons of the Options

### Option 1: Starlette Native WebSockets

- **Good**: No additional packages, services, or infrastructure -- uses only what FastAPI provides.
- **Good**: Full async/await integration with FastAPI's event loop.
- **Good**: WebSocket routes are defined with standard FastAPI decorators (`@router.websocket("/ws")`), maintaining consistency with REST routes.
- **Good**: Bidirectional protocol supports future extensions (e.g., client-initiated subscriptions to specific topics).
- **Good**: The `ConnectionManager` pattern is straightforward to understand, test, and extend.
- **Bad**: No built-in rooms, namespaces, or message acknowledgment -- these must be implemented manually if needed.
- **Bad**: Scaling beyond a single server requires adding an external Pub/Sub layer (e.g., Redis) to synchronize connection managers.
- **Neutral**: WebSocket connections are persistent, consuming a file descriptor and memory per connection (bounded by `max_connections=1000` default).

### Option 2: Socket.IO (via `python-socketio`)

- **Good**: Built-in room support, automatic reconnection, and message acknowledgment.
- **Good**: Fallback transports (long polling) for environments that block WebSocket connections.
- **Good**: Cross-language client support (JavaScript, Python, Java, etc.).
- **Bad**: Adds `python-socketio` and `python-engineio` as dependencies, plus the Socket.IO client library on the frontend.
- **Bad**: Socket.IO uses a custom protocol on top of WebSocket, which adds message framing overhead and complicates debugging with standard WebSocket tools.
- **Bad**: Integrating Socket.IO with FastAPI requires mounting a separate ASGI application, breaking the unified route definition pattern.
- **Neutral**: The room and namespace abstractions are powerful but unnecessary for a single-topic-list broadcast use case.

### Option 3: Server-Sent Events (SSE)

- **Good**: Simple HTTP-based protocol -- works through proxies and firewalls that may block WebSocket connections.
- **Good**: Built-in automatic reconnection with `Last-Event-ID` for resuming missed events.
- **Good**: No special client library required -- the browser's native `EventSource` API handles connection management.
- **Bad**: Unidirectional (server-to-client only) -- future client-to-server messaging would require a separate mechanism.
- **Bad**: Each SSE connection holds an HTTP connection open, which counts against browser per-domain connection limits (typically 6 for HTTP/1.1).
- **Bad**: SSE is not natively supported in FastAPI's routing -- requires `StreamingResponse` with manual event formatting.
- **Neutral**: Adequate for the current server-to-client broadcast pattern but limits future extensibility.

### Option 4: HTTP Polling

- **Good**: Simplest implementation -- standard REST endpoints with periodic client-side `fetch()` calls.
- **Good**: Works universally across all browsers, proxies, and firewalls.
- **Good**: Stateless on the server -- no connection management required.
- **Bad**: Polling intervals create a trade-off between latency and server load -- short intervals waste bandwidth, long intervals feel sluggish.
- **Bad**: Does not meet the "real-time" requirement -- users would see delayed score updates proportional to the polling interval.
- **Bad**: Generates significant unnecessary traffic when no data has changed, especially with many concurrent clients.
- **Bad**: Poor user experience for a community engagement tool where immediate feedback drives participation.

### Option 5: Redis Pub/Sub with External Broker

- **Good**: Enables horizontal scaling -- multiple server instances subscribe to the same Redis channel and broadcast to their local connections.
- **Good**: Redis is battle-tested infrastructure for message passing.
- **Good**: Decouples event production from event delivery -- any service can publish to the Redis channel.
- **Bad**: Introduces Redis as an additional infrastructure dependency that must be deployed, monitored, and maintained.
- **Bad**: Adds latency from the network hop between the application server and Redis.
- **Bad**: Over-engineered for a single-server deployment -- adds operational complexity without immediate benefit.
- **Neutral**: A natural evolution path if the application needs to scale horizontally in the future. The `EventPublisher` port abstraction makes this migration straightforward.

## More Information

- [Starlette WebSocket documentation](https://www.starlette.io/websockets/)
- [FastAPI WebSocket documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- Event publisher port (domain interface): `src/pulse_board/domain/ports/event_publisher_port.py`
- Connection manager (infrastructure): `src/pulse_board/infrastructure/websocket/connection_manager.py`
- WebSocket route (presentation): `src/pulse_board/presentation/api/routes/websocket.py`
- Frontend WebSocket port: `frontend/src/domain/ports/WebSocketPort.ts`
- Frontend WebSocket client: `frontend/src/infrastructure/websocket/webSocketClient.ts`
- ViewModel WebSocket handling: `frontend/src/presentation/view-models/TopicsViewModel.ts` (see `handleWebSocketMessage`, `handleReconnect`)
