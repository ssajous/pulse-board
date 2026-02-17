# Phase 1: Project Foundation & Infrastructure

## Overview

Set up the complete development environment, project scaffolding, and folder structure following onion architecture. This phase produces a running (but empty) application with health checks.

## Dependencies

None -- this is the first phase.

## Functional Requirements

### FR-1.1: Python Backend Scaffolding

**Description**: Initialize the Python backend project with pyproject.toml, uv package manager, and FastAPI as the web framework.

**Acceptance Criteria**:

- Given a fresh clone, When I run `uv sync`, Then all dependencies install without errors
- Given the project structure, When I inspect pyproject.toml, Then it lists fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary as dependencies
- Given the project, When I check the Python version, Then it requires Python 3.13+

### FR-1.2: React Frontend Scaffolding

**Description**: Initialize the React frontend with Vite, TypeScript, Tailwind CSS, MobX, and react-use-websocket.

**Acceptance Criteria**:

- Given a fresh clone, When I run `cd frontend && npm install`, Then all dependencies install without errors
- Given the frontend, When I run `npm run dev`, Then Vite starts with HMR on port 5173
- Given the frontend, When I inspect package.json, Then it includes react, react-dom, typescript, mobx, mobx-react-lite, react-use-websocket, tailwindcss, lucide-react

### FR-1.3: Docker Compose Infrastructure

**Description**: Create docker-compose.yml with PostgreSQL service for local development.

**Acceptance Criteria**:

- Given docker-compose.yml, When I run `docker compose up -d`, Then PostgreSQL starts on port 5432
- Given the PostgreSQL container, When I connect with credentials from .env.example, Then the connection succeeds
- Given the infrastructure, When I run `make infra-up`, Then Docker Compose services start
- Given running infrastructure, When I run `make infra-down`, Then all services stop cleanly

### FR-1.4: Makefile with Required Targets

**Description**: Create a Makefile with all targets specified in CLAUDE.md (dev, dev-backend, dev-frontend, test, test-unit, test-integration, test-all, test-e2e, infra-up, infra-down, docker-build, docker-run, clean, version, version-patch, version-minor, version-major, help).

**Acceptance Criteria**:

- Given the Makefile, When I run `make help`, Then all targets are listed with descriptions
- Given the Makefile, When I run `make dev`, Then both backend and frontend start (infrastructure starts automatically)
- Given the Makefile, When I run `make dev-backend`, Then only the FastAPI backend starts with hot reload
- Given the Makefile, When I run `make dev-frontend`, Then only the Vite frontend starts with HMR

### FR-1.5: Onion Architecture Folder Structure

**Description**: Create the complete folder structure for both backend and frontend following onion architecture patterns.

**Acceptance Criteria**:

- Given the backend, When I inspect src/, Then I see domain/ (entities/, value_objects/, services/, ports/), application/ (use_cases/, dtos/), infrastructure/ (repositories/, external/), presentation/ (api/routes/, api/schemas/)
- Given the frontend, When I inspect frontend/src/, Then I see domain/ (entities/, ports/), application/ (use-cases/), infrastructure/ (api/), presentation/ (components/, hooks/)
- Given the domain layer, When I inspect imports, Then there are NO framework imports (no FastAPI, no SQLAlchemy, no Pydantic)

### FR-1.6: FastAPI Health Endpoint

**Description**: Create a minimal FastAPI application with a health check endpoint that verifies database connectivity.

**Acceptance Criteria**:

- Given the running backend, When I GET /health, Then I receive {"status": "healthy", "database": "connected"}
- Given the backend with no database, When I GET /health, Then I receive {"status": "degraded", "database": "disconnected"} with HTTP 503
- Given the running backend, When I GET /docs, Then I see the Swagger UI

### FR-1.7: Alembic Migration Setup

**Description**: Configure Alembic for database migrations with SQLAlchemy.

**Acceptance Criteria**:

- Given the project, When I run `uv run alembic upgrade head`, Then migrations apply to the database
- Given the project, When I inspect alembic.ini, Then the database URL is loaded from environment variables
- Given the project, When I inspect the migrations directory, Then an initial migration exists (even if empty)

### FR-1.8: Environment Configuration

**Description**: Create .env.example with all required configuration variables.

**Acceptance Criteria**:

- Given .env.example, When I inspect it, Then it contains DATABASE_URL, CORS_ORIGINS, API_HOST, API_PORT, LOG_LEVEL
- Given .env.example, When I copy it to .env, Then the application starts with default values
- Given the application, When environment variables are set, Then configuration loads from environment (12-factor)

## Technical Notes

- Use `uv` exclusively for Python package management (never pip)
- Frontend uses nvm with Node.js v22 LTS
- All infrastructure runs in Docker, never installed on host
- Backend runs on port 8000, frontend on port 5173
