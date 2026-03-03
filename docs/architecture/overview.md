# Pulse Board -- System Architecture Overview

## System Context

Pulse Board is a real-time community engagement platform that enables anonymous topic submission, voting, and live polling within event sessions. Participants join events using short numeric codes -- no user accounts or registration required. Browser fingerprinting (FingerprintJS v5) uniquely identifies each participant, preventing duplicate votes while preserving anonymity.

The system serves two primary user roles:

- **Event hosts** create events, author multiple-choice polls, and control poll activation/deactivation through an admin interface.
- **Participants** join events by code, submit discussion topics, upvote or downvote topics, and respond to live polls.

All interactions happen through a single-page application served by a FastAPI backend. The only external infrastructure dependency is a PostgreSQL 16 database. There are no third-party service integrations beyond the FingerprintJS client-side library, which runs entirely in the browser.

```
                         +------------------+
                         |   Participants   |
                         |  (Web Browsers)  |
                         +--------+---------+
                                  |
                    HTTPS REST + WebSocket (wss)
                                  |
                         +--------v---------+
                         |   FastAPI App    |
                         |  (Python 3.13)  |
                         +--------+---------+
                                  |
                       PostgreSQL wire protocol
                                  |
                         +--------v---------+
                         | PostgreSQL 16    |
                         | (Docker)         |
                         +------------------+
```

## Key Design Decisions

Architectural choices are recorded as Architecture Decision Records (ADRs) in the [`docs/architecture/decisions/`](decisions/) directory:

| ADR | Decision | Rationale |
|-----|----------|-----------|
| [0001](decisions/0001-frontend-technology-stack.md) | React 19 + TypeScript + Vite + Tailwind CSS v4 | Ecosystem breadth, type safety, sub-second HMR, utility-first CSS |
| [0002](decisions/0002-backend-technology-stack.md) | FastAPI + Python 3.13 | Async-native framework, Pydantic validation, OpenAPI generation |
| [0003](decisions/0003-browser-fingerprinting.md) | FingerprintJS v5 | Anonymous identity without accounts, client-side only |
| [0004](decisions/0004-realtime-websockets.md) | Starlette WebSockets | Server-to-client push, no polling overhead, native FastAPI support |
| [0005](decisions/0005-state-management-mobx-mvvm.md) | MobX 6 with MVVM | Reactive ViewModels, computed properties, thin components |

## Component Overview

Both the backend and frontend follow **onion architecture** (clean architecture). Dependencies point inward: outer layers depend on inner layers, never the reverse. Each layer has a single responsibility, and boundaries are enforced through abstract port interfaces.

### Backend (Python / FastAPI)

```
src/pulse_board/
+-- domain/                  # Inner layer: zero framework imports
|   +-- entities/            # Topic, Vote, Event, Poll, PollResponse
|   +-- services/            # VotingService (pure logic), JoinCodeGenerator
|   +-- ports/               # ABCs: TopicRepository, VoteRepository,
|   |                        #   EventRepository, PollRepository,
|   |                        #   PollResponseRepository, EventPublisher,
|   |                        #   DatabasePort
|   +-- events.py            # Domain events (frozen dataclasses)
|   +-- exceptions.py        # DomainError hierarchy
|   +-- value_objects/       # (reserved for future value types)
|
+-- application/             # Use case orchestration
|   +-- use_cases/           # CreateTopic, CastVote, CreateEvent,
|   |                        #   JoinEvent, ListTopics, ListEventTopics,
|   |                        #   GetEvent, CreatePoll, ActivatePoll,
|   |                        #   SubmitPollResponse, GetPollResults,
|   |                        #   HealthCheck
|   +-- dtos/                # Data transfer objects
|
+-- infrastructure/          # Outer layer: framework and I/O
|   +-- config/settings.py   # Pydantic-settings (env vars, .env file)
|   +-- database/            # SQLAlchemy 2.0 engine, session, ORM models
|   +-- repositories/        # Concrete port implementations (SQL queries)
|   +-- websocket/           # ConnectionManager (EventPublisher impl)
|   +-- external/            # (reserved for third-party adapters)
|
+-- presentation/            # HTTP boundary
    +-- api/app.py           # Application factory (create_app)
    +-- api/routes/          # FastAPI routers: health, topics, votes,
    |                        #   events, polls, websocket, test_utils
    +-- api/schemas/         # Pydantic request/response models
    +-- api/dependencies.py  # FastAPI dependency injection
    +-- api/exception_handlers.py  # Domain-to-HTTP error mapping
```

**Key design points:**

- Domain entities are plain Python dataclasses with factory classmethods (`create`) that enforce validation rules. Repositories reconstitute entities through the direct constructor, bypassing re-validation.
- The `VotingService` is a pure domain service -- it takes an optional existing vote and a direction, then returns a discriminated union (`VoteCreated | VoteToggled | VoteCancelled`) describing the action. No I/O occurs inside the service.
- Port interfaces (ABCs) are defined in `domain/ports/`. Infrastructure provides concrete implementations. Use cases depend only on abstractions.
- The `ConnectionManager` implements the `EventPublisher` port. It manages WebSocket connections, enforces per-IP and global connection limits, and broadcasts JSON messages to all clients or to channel-scoped subsets.

### Frontend (React / TypeScript)

```
frontend/src/
+-- domain/
|   +-- entities/            # Topic, Vote, Event, Poll (TypeScript types)
|   +-- ports/               # Interfaces: TopicApiPort, VoteApiPort,
|                            #   EventApiPort, PollApiPort,
|                            #   FingerprintPort, WebSocketPort
|
+-- application/
|   +-- use-cases/           # Pure functions (computeScoreDelta, etc.)
|
+-- infrastructure/
|   +-- api/                 # HTTP clients: topicApiClient, voteApiClient,
|   |                        #   eventApiClient, eventTopicApiClient,
|   |                        #   pollApiClient
|   +-- fingerprint/         # FingerprintJS v5 adapter
|   +-- websocket/           # WebSocket client
|   +-- logger.ts            # Structured logging
|
+-- presentation/
    +-- components/          # React components (thin, observer-wrapped)
    +-- pages/               # Route-level page components
    +-- view-models/         # MobX ViewModels (MVVM pattern)
    +-- hooks/               # React hooks
```

**Key design points:**

- Components are intentionally "dumb" -- they observe ViewModel state via `mobx-react-lite` and delegate all logic and side effects to ViewModels.
- ViewModels use MobX observables, computed properties, and actions. Computed properties derive display state (loading flags, sorted lists, percentages) from core state, so the UI automatically reacts to state changes.
- Port interfaces in `domain/ports/` define contracts for API calls, fingerprint generation, and WebSocket communication. Infrastructure modules implement these contracts.

## Data Architecture

### Database Schema

PostgreSQL 16 stores all persistent state across five tables. Alembic manages schema migrations.

```
+-------------------+       +-------------------+       +-------------------+
|      events       |       |      topics       |       |      votes        |
+-------------------+       +-------------------+       +-------------------+
| id (PK, UUID)     |<--+   | id (PK, UUID)     |<--+   | id (PK, UUID)     |
| title              |   |   | content            |   |   | topic_id (FK)     |
| code (UNIQUE)      |   +---| event_id (FK, NULL)|   +---| fingerprint_id    |
| description        |       | score              |       | value (+1/-1)     |
| start_date         |       | created_at         |       | created_at        |
| end_date           |       +-------------------+       | updated_at        |
| status             |                                    +-------------------+
| created_at         |
+-------------------+
        |
        |       +-------------------+       +-------------------+
        |       |      polls        |       |  poll_responses   |
        |       +-------------------+       +-------------------+
        +------>| id (PK, UUID)     |<------| id (PK, UUID)     |
                | event_id (FK)     |       | poll_id (FK)      |
                | question          |       | fingerprint_id    |
                | poll_type         |       | option_id         |
                | options (JSONB)   |       | response_data     |
                | is_active         |       | created_at        |
                | created_at        |       +-------------------+
                +-------------------+       UNIQUE(poll_id,
                                              fingerprint_id)
```

**Key constraints:**

- `events.code` has a unique index for fast join-code lookups.
- `poll_responses` enforces a unique constraint on `(poll_id, fingerprint_id)` to prevent duplicate votes per participant per poll.
- Topics optionally belong to an event (`event_id` is nullable). Standalone topics support the global board mode.
- Poll options are stored as JSONB within the `polls` table, keeping the schema simple while supporting variable option counts (2--10).

### Data Flow

1. **Topic submission**: Browser sends POST to `/api/events/{code}/topics` with content and fingerprint. The `CreateTopic` use case validates, persists, and publishes a `new_topic` WebSocket event.
2. **Voting**: Browser sends POST to `/api/votes` with topic ID, fingerprint, and direction. The `CastVote` use case delegates to `VotingService`, which returns a `VoteAction`. The use case persists the result, updates the topic score, and broadcasts `score_update`. If the score crosses the censure threshold (-5), a `topic_censured` event is broadcast.
3. **Poll lifecycle**: Host creates a poll (POST `/api/events/{id}/polls`), activates it (PATCH `/api/polls/{id}/activate`), participants respond (POST `/api/polls/{id}/responses`), and results stream via `poll_results_updated` WebSocket events. Deactivation stops accepting responses.
4. **Real-time delivery**: The `ConnectionManager` broadcasts JSON messages over WebSocket connections. Global broadcasts reach `/ws`; event-scoped broadcasts reach `/ws/events/{code}` via channel routing keyed as `event:{code}`.

## Deployment Architecture

### Local Development

Run `make dev` to start the full development stack. This starts PostgreSQL via Docker Compose, the FastAPI backend with hot reload, and the Vite frontend with HMR, all in a single command. Infrastructure stops automatically on exit.

| Component | URL | Tooling |
|-----------|-----|---------|
| Backend API | `http://localhost:8000` | uvicorn `--reload` |
| API documentation | `http://localhost:8000/docs` | Swagger UI (auto-generated) |
| Frontend | `http://localhost:5173` | Vite dev server |
| PostgreSQL | `localhost:5432` | Docker Compose |

Run `make help` for all available targets. Key commands:

```
make dev              # Start everything (infra + backend + frontend)
make dev-backend      # Backend only with hot reload
make dev-frontend     # Frontend only with HMR
make test             # Unit tests with coverage
make test-all         # Unit + integration + frontend tests
make test-e2e         # End-to-end tests (Playwright)
make lint             # Ruff + Pyright + ESLint
make migrate          # Run Alembic migrations
```

### Production

The production deployment uses a multi-stage Docker build defined in the project `Dockerfile`:

1. **Stage 1 (frontend-builder)**: `node:22-alpine` builds the React app with `npm run build`, producing static assets.
2. **Stage 2 (runtime)**: `python:3.13-slim` installs Python dependencies via `uv sync --no-dev`, copies the application code, Alembic migrations, and the built frontend assets into `/app/static/`.

The FastAPI app detects the `static/` directory at startup and mounts it directly, serving the SPA frontend and API from a single process with no separate web server.

```
docker-compose.prod.yml
+--------------------------------------------+
|  pulse-network (bridge)                    |
|                                            |
|  +----------------+    +----------------+  |
|  |      app       |    |      db        |  |
|  | python:3.13    |    | postgres:16    |  |
|  | port 8000      |--->| port 5432      |  |
|  | non-root user  |    | volume: data   |  |
|  | health: /health|    | health: ready  |  |
|  +----------------+    +----------------+  |
|                                            |
+--------------------------------------------+
```

**Production safeguards:**

- The container runs as a non-root user (`appuser`, UID 1000).
- Health checks run on both the app (HTTP `/health`) and database (`pg_isready`).
- The `app` container waits for `db` to be healthy before starting (`condition: service_healthy`).
- `POSTGRES_PASSWORD` is required in production (`${POSTGRES_PASSWORD:?}`); no default is provided.
- A dedicated bridge network (`pulse-network`) isolates service communication.

Start the production stack with `make docker-prod-up`. View logs with `make docker-prod-logs`. Shut down with `make docker-prod-down`.

## Cross-Cutting Concerns

### Identity and Authentication

Pulse Board uses **browser fingerprinting** instead of traditional authentication. FingerprintJS v5 generates a stable visitor identifier on the client side, which is sent as `fingerprint_id` in API requests. This identifier:

- Prevents duplicate votes on topics (one vote per fingerprint per topic).
- Prevents duplicate poll responses (unique constraint on `poll_id` + `fingerprint_id`).
- Requires no server-side session state, cookies, or tokens.

There is no authorization layer. All participants within an event share the same permissions. Event hosts receive an admin link at creation time that grants access to the admin interface.

### Error Handling

Domain exceptions form a typed hierarchy rooted at `DomainError`. The presentation layer maps each exception type to an HTTP status code through a centralized handler (`exception_handlers.py`):

| Exception | HTTP Status | Meaning |
|-----------|-------------|---------|
| `ValidationError` | 422 | Input fails domain rules |
| `EntityNotFoundError` | 404 | Requested resource missing |
| `EventNotFoundError` | 404 | Event does not exist |
| `EventNotActiveError` | 409 | Event is closed |
| `DuplicateVoteError` | 409 | Vote already exists |
| `DuplicateResponseError` | 409 | Poll response already submitted |
| `PollNotActiveError` | 409 | Poll is not accepting responses |
| `InvalidPollOptionError` | 422 | Option ID not in poll |
| `CodeGenerationError` | 500 | Join code generation failed |

All 5xx errors are logged with full tracebacks. Client-facing error responses use a consistent `{"detail": "..."}` JSON format.

### Configuration

All configuration loads from environment variables through `pydantic-settings` (`Settings` class). A `.env` file is supported for local development. Configuration categories:

- **Database**: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DATABASE_URL`
- **API**: `API_HOST`, `API_PORT`, `CORS_ORIGINS`, `LOG_LEVEL`
- **WebSocket**: `WS_MAX_SIZE`, `WS_MAX_CONNECTIONS`, `WS_MAX_CONNECTIONS_PER_IP`
- **Security**: `TEST_MODE_SECRET` (enables test utility endpoints)

No configuration values are hardcoded. The `Settings` instance is created once and cached via `@lru_cache`.

### Logging

The application uses Python's standard `logging` module. Each module creates its own logger via `logging.getLogger(__name__)`. Log level is configurable through the `LOG_LEVEL` environment variable (default: `INFO`). WebSocket connection events, broadcast operations, and error conditions are logged with context (connection counts, message types, client IPs).

### WebSocket Security

- **Origin validation**: Both `/ws` and `/ws/events/{code}` endpoints validate the `Origin` header against the `CORS_ORIGINS` allowlist before accepting connections. Unauthorized origins receive close code 1008 (Policy Violation).
- **Connection limits**: A global maximum (default 1000) and per-IP maximum (default 10) prevent resource exhaustion. Connections exceeding limits receive close code 1013 (Try Again Later).
- **Message size**: Inbound messages exceeding `WS_MAX_SIZE` (default 1024 bytes) are logged and ignored.
- **Dead connection cleanup**: Failed sends during broadcasts automatically remove dead connections from the active set.
