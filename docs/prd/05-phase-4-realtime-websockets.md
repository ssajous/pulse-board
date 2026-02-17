# Phase 4: Real-Time WebSocket Updates

## Overview

Implement WebSocket-based real-time updates so all connected clients see score changes and topic removals instantly without page refresh. Topics re-rank in real-time as scores change.

## Dependencies

- Phase 3 (Voting System) must be complete

## Functional Requirements

### FR-4.1: WebSocket Endpoint

**Description**: Create a WebSocket endpoint on the FastAPI backend that clients can connect to for real-time updates.

**Acceptance Criteria**:

- Given the backend is running, When a client connects to ws://localhost:8000/ws, Then the WebSocket connection is established
- Given a connected client, When the server has no updates, Then the connection remains open (keep-alive)
- Given a connected client, When the client disconnects, Then the server cleans up the connection without errors

### FR-4.2: Connection Manager

**Description**: Implement a ConnectionManager class that tracks active WebSocket connections and broadcasts messages to all connected clients.

**Acceptance Criteria**:

- Given the ConnectionManager, When a new client connects, Then it is added to the active connections list
- Given the ConnectionManager, When a client disconnects, Then it is removed from the active connections list
- Given the ConnectionManager, When broadcast(message) is called, Then all connected clients receive the message
- Given a client that has disconnected unexpectedly, When broadcasting, Then the stale connection is removed without crashing

### FR-4.3: Vote Score Broadcasting

**Description**: When a vote is cast, broadcast the updated topic score to all connected WebSocket clients.

**Acceptance Criteria**:

- Given a vote is cast on topic X, When the vote is processed, Then a message {"type": "score_update", "topic_id": "X", "score": N} is broadcast to all clients
- Given multiple clients are connected, When a vote is cast, Then ALL clients receive the score update
- Given the voter's own client, When the vote response returns, Then the HTTP response score and WebSocket broadcast score are consistent

### FR-4.4: Topic Censure Broadcasting

**Description**: When a topic is censured (score <= -5), broadcast the removal to all connected clients.

**Acceptance Criteria**:

- Given a topic is censured, When censure occurs, Then a message {"type": "topic_censured", "topic_id": "X"} is broadcast to all clients
- Given a connected client receives a censure message, When processing it, Then the topic is removed from the display with a toast notification

### FR-4.5: New Topic Broadcasting

**Description**: When a new topic is created, broadcast it to all connected clients.

**Acceptance Criteria**:

- Given a new topic is created via POST /api/topics, When the topic is persisted, Then a message {"type": "new_topic", "topic": {...}} is broadcast to all clients
- Given a connected client receives a new_topic message, When processing it, Then the topic appears in the list at the correct sorted position

### FR-4.6: Frontend Real-Time Re-Ranking

**Description**: When scores update in real-time, topics visually re-sort to their new positions.

**Acceptance Criteria**:

- Given topic A (score 5) and topic B (score 4), When topic B receives an upvote (score 5), Then topics re-sort by created_at as tiebreaker
- Given topic A (score 5) and topic B (score 3), When topic B receives 3 upvotes (score 6), Then topic B moves above topic A
- Given re-ranking occurs, When the animation completes, Then the transition is smooth (CSS transition on position)

### FR-4.7: WebSocket Client Integration with MobX

**Description**: Integrate react-use-websocket with the MobX ViewModel to handle real-time updates.

**Acceptance Criteria**:

- Given the ViewModel, When it initializes, Then a WebSocket connection is established to ws://localhost:8000/ws
- Given a score_update message, When received, Then the ViewModel updates the topic's score observable
- Given a topic_censured message, When received, Then the ViewModel removes the topic from the topics array
- Given a new_topic message, When received, Then the ViewModel adds the topic to the topics array
- Given a WebSocket disconnection, When it occurs, Then react-use-websocket automatically reconnects
- Given a reconnection, When it succeeds, Then the ViewModel fetches the full topic list to sync state

### FR-4.8: Optimistic Update Reconciliation

**Description**: Handle the case where a user's optimistic vote update conflicts with the WebSocket broadcast.

**Acceptance Criteria**:

- Given a user casts a vote (optimistic score = 6), When the WebSocket broadcasts score = 6, Then no visual flicker occurs (scores match)
- Given a user casts a vote (optimistic score = 6), When the WebSocket broadcasts score = 7 (another user also voted), Then the score smoothly updates to 7

## Technical Notes

- Use FastAPI's built-in WebSocket support (Starlette)
- ConnectionManager should handle concurrent access safely (asyncio)
- WebSocket messages are JSON-encoded
- react-use-websocket provides shouldReconnect, reconnectInterval, and reconnectAttempts options
- The WebSocket is for push notifications only -- initial state is loaded via REST API
- NFR: WebSocket message delivery < 100ms from vote to all connected clients
- NFR: Support 50 concurrent WebSocket connections per instance
- NFR: Graceful reconnection within 5s of disconnection
