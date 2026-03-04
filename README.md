# Pulse Board

**Version 0.1.0** | Real-time community engagement platform for anonymous topic submission, voting, and live polling.

Pulse Board lets participants join event sessions using short numeric codes -- no accounts, no registration. Browser fingerprinting (FingerprintJS v5) uniquely identifies each participant so votes are reliable without requiring login. Everything updates live across all connected browsers via WebSockets.

## Overview

Pulse Board is built for live events: conferences, workshops, team meetings, or any gathering where the audience should have a voice. A host creates a session and shares a join code. Participants open the app, enter the code, and immediately start submitting topics or casting votes. Every upvote, downvote, and new topic appears on all screens in real time.

The host controls the experience from a dedicated admin dashboard: activating polls, projecting results in present mode, and managing the topic list throughout the event. Participants never see behind the curtain -- they just engage.

Both the backend and frontend follow **onion architecture** (clean architecture), keeping business logic independent of frameworks, databases, and transport layers. The frontend uses the **MVVM pattern** with MobX for reactive, testable state management.

## Key Features

- **Event sessions with join codes** -- participants enter a short numeric code to join; no account required
- **Topic submission and voting** -- anyone can propose a topic; up/downvoting with real-time score updates via WebSocket
- **Multiple poll types** -- multiple choice, rating scale, open text, and word cloud
- **Present mode** -- display live poll results on-screen during events
- **Host admin dashboard** -- manage events, topics, and polls from a dedicated interface
- **Browser fingerprinting** -- FingerprintJS v5 provides anonymous identity so each browser gets one vote per topic
- **Vote censure** -- topics that drop to a score of -5 are automatically censured

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
| Infrastructure | Docker, Docker Compose |
| Package Management | uv (Python), npm (Node.js) |

## Quick Start

```bash
git clone <repo-url>
cd pulse-board
cp .env.example .env
make dev
```

`make dev` starts PostgreSQL in Docker, runs database migrations, and launches both the backend and frontend with hot reload. Once running:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.13+ | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js | 22 LTS | Install via [nvm](https://github.com/nvm-sh/nvm), then `nvm install 22` |
| uv | Latest | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Docker | Latest | [docs.docker.com/get-docker](https://docs.docker.com/get-started/get-docker/) |

## Installation

Install all dependencies before running the application for the first time:

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && nvm use 22 && npm install && cd ..

# Copy the environment configuration template
cp .env.example .env
```

Open `.env` and set the required values. The defaults work for local development with Docker-managed PostgreSQL.

## Development

All development tasks run through the Makefile. Run `make help` to see every available target with its description.

### Starting the Application

| Command | Description |
|---------|-------------|
| `make dev` | Start backend, frontend, and infrastructure together |
| `make dev-backend` | Start backend only with hot reload |
| `make dev-frontend` | Start frontend only with HMR |
| `make migrate` | Run database migrations |
| `make infra-up` | Start PostgreSQL in Docker |
| `make infra-down` | Stop infrastructure services |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run unit tests (alias for `test-unit`) |
| `make test-unit` | Run Python unit tests with coverage |
| `make test-frontend` | Run frontend unit tests (Vitest) |
| `make test-integration` | Run integration tests against PostgreSQL |
| `make test-all` | Run all tests (unit + integration + frontend) with coverage |
| `make test-coverage` | Run Python tests with full HTML coverage report |
| `make test-e2e` | Run end-to-end tests (Playwright) |

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run all linters (ruff, pyright, ESLint) |
| `make format` | Auto-format Python code (ruff) |

### Docker

| Command | Description |
|---------|-------------|
| `make docker-build` | Build the production Docker image |
| `make docker-run` | Run the application container locally |
| `make docker-prod-up` | Start the full production stack |
| `make docker-prod-down` | Stop the production stack |
| `make docker-prod-logs` | Tail production logs |

### Versioning

| Command | Description |
|---------|-------------|
| `make version` | Show current version (0.1.0) |
| `make version-patch` | Bump patch version (0.1.0 -> 0.1.1) |
| `make version-minor` | Bump minor version (0.1.0 -> 0.2.0) |
| `make version-major` | Bump major version (0.1.0 -> 1.0.0) |

### Cleanup

```bash
make clean
```

Removes all build artifacts, caches, Python bytecode, frontend build output, and Docker volumes.

## Project Structure

```
pulse-board/
├── src/pulse_board/              # Backend (Python/FastAPI)
│   ├── domain/                   # Core business rules, entities, ports
│   ├── application/              # Use cases and DTOs
│   ├── infrastructure/           # Database, WebSocket, config
│   └── presentation/             # API routes and Pydantic schemas
├── frontend/src/                 # Frontend (React/TypeScript)
│   ├── domain/                   # Entities and port interfaces
│   ├── application/              # Use cases
│   ├── infrastructure/           # API clients, WebSocket, fingerprint
│   └── presentation/             # Components, pages, ViewModels
├── tests/
│   ├── unit/                     # Unit tests (mirrors src/ structure)
│   ├── integration/              # Integration tests with PostgreSQL
│   └── e2e/                      # End-to-end tests (Playwright)
├── migrations/                   # Alembic database migrations
├── docs/                         # Project documentation
│   ├── architecture/             # System architecture and ADRs
│   ├── guides/                   # Getting started, dev setup, deployment
│   ├── testing/                  # Testing strategy and conventions
│   ├── database/                 # Migration guide
│   ├── operations/               # Docker reference
│   └── code-style/               # Style guide
├── docker-compose.yml            # Development infrastructure (PostgreSQL)
├── docker-compose.prod.yml       # Production stack
├── Dockerfile                    # Production container build
├── Makefile                      # All development commands
└── pyproject.toml                # Python project configuration
```

Both backend and frontend follow onion architecture: Domain -> Application -> Infrastructure -> Presentation. Dependencies point inward only.

## API Documentation

Interactive API documentation is available when the backend is running:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Documentation

Detailed documentation lives in the `docs/` directory:

- [Architecture Overview](docs/architecture/overview.md) -- system design, components, and data flow
- [Getting Started](docs/guides/getting-started.md) -- tutorial for first-time setup
- [Development Setup](docs/guides/development-setup.md) -- full dev environment configuration
- [Deployment Guide](docs/guides/deployment.md) -- Docker deployment for local and production
- [Testing Strategy](docs/testing/testing-strategy.md) -- testing philosophy, pyramid, and coverage goals
- [Test Conventions](docs/testing/test-conventions.md) -- naming, patterns, and step-by-step checklists
- [Code Style Guide](docs/code-style/style-guide.md) -- conventions, tools, and review checklist
- [Database Migrations](docs/database/migration-guide.md) -- Alembic migration workflow
- [Docker Reference](docs/operations/docker.md) -- Docker Compose services and troubleshooting

### Architecture Decision Records

Design decisions are documented as ADRs in `docs/architecture/decisions/`:

- [ADR 0001: Frontend Technology Stack](docs/architecture/decisions/0001-frontend-technology-stack.md)
- [ADR 0002: Backend Technology Stack](docs/architecture/decisions/0002-backend-technology-stack.md)
- [ADR 0003: Browser Fingerprinting](docs/architecture/decisions/0003-browser-fingerprinting.md)
- [ADR 0004: Real-Time WebSockets](docs/architecture/decisions/0004-realtime-websockets.md)
- [ADR 0005: State Management - MobX MVVM](docs/architecture/decisions/0005-state-management-mobx-mvvm.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch strategy, commit conventions, pull request process, and code quality requirements.

Before opening a pull request:

```bash
make test-all
make test-e2e
make lint
```

All tests must pass and all linters must report no errors. A human reviewer approves and merges every PR -- contributors do not merge their own work.

## License

MIT
