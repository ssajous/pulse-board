# Community Pulse Board

A real-time community engagement platform where users submit topics, vote on them, and see live score updates -- all without creating an account. Browser fingerprinting enables anonymous participation, and WebSocket connections push every score change to every connected client instantly.

## Key Features

- **Topic Submission** -- anyone can propose a topic for community discussion
- **Up/Downvoting with Toggle** -- vote once per topic; voting the same direction again cancels it, voting the opposite direction switches it
- **Real-Time Updates** -- all connected browsers receive score changes and new topics via WebSockets
- **Anonymous Fingerprinting** -- FingerprintJS identifies unique browsers so votes are one-per-person without requiring login
- **Vote Censure** -- topics that drop to a score of -5 are automatically censured

## Architecture Overview

Both the backend and frontend follow **onion architecture** (clean architecture), where dependencies only point inward. The frontend uses the **MVVM pattern** with MobX for reactive state management.

```
Backend (Python)                         Frontend (TypeScript)
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  Presentation                │        │  Presentation                │
│  API routes, schemas         │        │  Components, ViewModels      │
│  ┌────────────────────────┐  │        │  ┌────────────────────────┐  │
│  │  Infrastructure        │  │        │  │  Infrastructure        │  │
│  │  Repos, WS, config     │  │        │  │  API clients, WS, FP   │  │
│  │  ┌──────────────────┐  │  │        │  │  ┌──────────────────┐  │  │
│  │  │  Application     │  │  │        │  │  │  Application     │  │  │
│  │  │  Use cases, DTOs │  │  │        │  │  │  Use cases       │  │  │
│  │  │  ┌────────────┐  │  │  │        │  │  │  ┌────────────┐  │  │  │
│  │  │  │  Domain    │  │  │  │        │  │  │  │  Domain    │  │  │  │
│  │  │  │  Entities  │  │  │  │        │  │  │  │  Entities  │  │  │  │
│  │  │  │  Ports     │  │  │  │        │  │  │  │  Ports     │  │  │  │
│  │  │  └────────────┘  │  │  │        │  │  │  └────────────┘  │  │  │
│  │  └──────────────────┘  │  │        │  │  └──────────────────┘  │  │
│  └────────────────────────┘  │        │  └────────────────────────┘  │
└──────────────────────────────┘        └──────────────────────────────┘
```

**Backend layers** -- Domain (entities, value objects, ports) -> Application (use cases, DTOs) -> Infrastructure (repositories, WebSocket manager, config) -> Presentation (FastAPI routes, Pydantic schemas)

**Frontend layers** -- Domain (entities, port interfaces) -> Application (use cases) -> Infrastructure (API clients, fingerprint service, WebSocket client) -> Presentation (React components, MobX ViewModels)

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4 |
| State Management | MobX 6 with MVVM pattern |
| Backend | FastAPI, Python 3.13 |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| Real-time | Starlette WebSockets |
| Fingerprinting | FingerprintJS v5 |
| Testing | pytest, Vitest, Playwright |
| CI/CD | GitHub Actions |
| Package Management | uv (Python), npm (Node.js) |

## Getting Started

### Prerequisites

- **Python 3.13+**
- **Node.js 22 LTS** (use [nvm](https://github.com/nvm-sh/nvm): `nvm use 22`)
- **uv** -- Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker** -- for PostgreSQL and production builds

### Quick Start

```bash
git clone <repo-url>
cd pulse-board
cp .env.example .env
make dev
```

This single command starts PostgreSQL in Docker, the backend on `http://localhost:8000`, and the frontend on `http://localhost:5173`.

### Manual Setup

If you prefer to start services individually:

```bash
# 1. Install Python dependencies
uv sync

# 2. Install frontend dependencies
cd frontend && nvm use 22 && npm install && cd ..

# 3. Copy environment config
cp .env.example .env

# 4. Start infrastructure (PostgreSQL)
make infra-up

# 5. Run database migrations
make migrate

# 6. Start backend (in one terminal)
make dev-backend

# 7. Start frontend (in another terminal)
make dev-frontend
```

### Verify the Setup

- Frontend: open `http://localhost:5173` in your browser
- Backend health check: `curl http://localhost:8000/health`
- API docs: open `http://localhost:8000/docs` in your browser

## Development

All development tasks are accessed through the Makefile. Run `make help` to see all available targets.

### Application

| Command | Description |
|---------|-------------|
| `make dev` | Start backend, frontend, and infrastructure |
| `make dev-backend` | Start backend with hot reload |
| `make dev-frontend` | Start frontend with HMR |
| `make migrate` | Run database migrations |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run unit tests (alias for `test-unit`) |
| `make test-unit` | Run Python unit tests with coverage |
| `make test-frontend` | Run frontend unit tests (Vitest) |
| `make test-integration` | Run integration tests |
| `make test-all` | Run all tests (unit + integration + frontend) with coverage |
| `make test-coverage` | Run Python tests with full HTML coverage report |
| `make test-e2e` | Run end-to-end tests (Playwright) |

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run all linters (ruff, pyright, ESLint) |
| `make format` | Auto-format Python code (ruff) |

### Infrastructure

| Command | Description |
|---------|-------------|
| `make infra-up` | Start PostgreSQL in Docker |
| `make infra-down` | Stop infrastructure services |
| `make clean` | Remove all build artifacts, caches, and Docker volumes |

### Versioning

| Command | Description |
|---------|-------------|
| `make version` | Show current version |
| `make version-patch` | Bump patch version (0.1.0 -> 0.1.1) |
| `make version-minor` | Bump minor version (0.1.0 -> 0.2.0) |
| `make version-major` | Bump major version (0.1.0 -> 1.0.0) |

### Project Structure

```
pulse-board/
├── src/pulse_board/              # Backend source
│   ├── domain/                   # Entities, value objects, ports
│   ├── application/              # Use cases, DTOs
│   ├── infrastructure/           # Repositories, WebSocket, config
│   └── presentation/             # FastAPI routes, Pydantic schemas
├── frontend/src/                 # Frontend source
│   ├── domain/                   # Entities, port interfaces
│   ├── application/              # Use cases
│   ├── infrastructure/           # API clients, fingerprint, WebSocket
│   └── presentation/             # Components, ViewModels, hooks
├── tests/
│   ├── unit/                     # Unit tests (mirrors src/ structure)
│   └── integration/              # Integration tests
├── migrations/                   # Alembic database migrations
├── docs/adr/                     # Architecture Decision Records
├── docker-compose.yml            # Development infrastructure
├── docker-compose.prod.yml       # Production stack
├── Dockerfile                    # Production container build
├── Makefile                      # All development commands
└── pyproject.toml                # Python project configuration
```

## API Documentation

Interactive API documentation is available when the backend is running:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check with database status |
| `POST` | `/api/topics` | Create a new topic |
| `GET` | `/api/topics` | List all topics sorted by score |
| `POST` | `/api/topics/{topic_id}/votes` | Cast a vote (up/down) on a topic |
| `WS` | `/ws` | WebSocket connection for real-time updates |

### Voting Behavior

The voting endpoint supports toggling:

- **First vote** -- registers the vote (up or down) and adjusts the score
- **Same direction again** -- cancels the vote, reverting the score change
- **Opposite direction** -- switches the vote, swinging the score by 2 points

Votes are identified by a browser fingerprint, so each browser gets one vote per topic without requiring authentication.

### WebSocket Events

The `/ws` endpoint is server-to-client only. Connected clients receive JSON messages for:

- **Score updates** -- when any topic's score changes
- **New topics** -- when a topic is created
- **Censure events** -- when a topic drops to -5

## Docker Deployment

### Local Docker Build

```bash
make docker-build
make docker-run
```

This builds the application image (with frontend assets baked in) and runs it on port 8000 using `--network host` to reach the local PostgreSQL.

### Production Deployment

The production stack runs both the application and PostgreSQL in Docker with a dedicated bridge network:

```bash
cp .env.example .env
# Edit .env and set a strong POSTGRES_PASSWORD
make docker-prod-up
```

The production compose file (`docker-compose.prod.yml`) includes health checks, automatic restarts, and persistent PostgreSQL storage.

| Command | Description |
|---------|-------------|
| `make docker-prod-up` | Start production stack |
| `make docker-prod-down` | Stop production stack |
| `make docker-prod-logs` | Tail production logs |

## Documentation

Detailed documentation lives in the `docs/` directory:

- [Testing Strategy](docs/testing/testing-strategy.md) -- testing philosophy, pyramid, and coverage goals
- [Test Conventions](docs/testing/test-conventions.md) -- naming, patterns, and step-by-step checklists for adding tests

## Architecture Decision Records

Design decisions are documented as ADRs in the `docs/adr/` directory:

- [ADR 001: Frontend Technology Stack](docs/adr/001-frontend-technology-stack.md)
- [ADR 002: Backend Technology Stack](docs/adr/002-backend-technology-stack.md)
- [ADR 003: Browser Fingerprinting](docs/adr/003-browser-fingerprinting.md)
- [ADR 004: Real-Time WebSockets](docs/adr/004-realtime-websockets.md)
- [ADR 005: State Management - MobX MVVM](docs/adr/005-state-management-mobx-mvvm.md)

## License

This project is unlicensed.
