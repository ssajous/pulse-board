# Development Setup

This guide walks you through setting up a full development environment for Pulse Board. It covers installing dependencies, configuring environment variables, running services individually, executing tests, and using code quality tools.

For a quick first run, see the [Getting Started](getting-started.md) guide instead.

## Prerequisites

| Tool | Minimum Version | Install Guide |
|------|-----------------|---------------|
| **Python** | 3.13+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 22 LTS | Install via [nvm](https://github.com/nvm-sh/nvm), then `nvm install 22` |
| **uv** | Latest | [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/) |
| **Docker** | Latest (with Compose plugin) | [docs.docker.com/get-started/get-docker](https://docs.docker.com/get-started/get-docker/) |

Verify each tool is installed:

```bash
python3 --version    # Python 3.13.x or higher
node --version       # v22.x.x
uv --version         # uv 0.x.x
docker compose version  # Docker Compose v2.x.x
```

## Environment Configuration

Copy the example environment file and review its variables:

```bash
cp .env.example .env
```

The `.env` file configures both the backend application and the PostgreSQL container. The defaults are suitable for local development -- you only need to edit them if you have a conflicting PostgreSQL instance or need to change ports.

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `pulse` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `pulse_dev_password` |
| `POSTGRES_DB` | Database name | `pulse_board` |
| `POSTGRES_HOST` | Database hostname | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `DATABASE_URL` | Full SQLAlchemy connection string | `postgresql+psycopg2://pulse:pulse_dev_password@localhost:5432/pulse_board` |
| `CORS_ORIGINS` | Comma-separated allowed origins for CORS | `http://localhost:5173,http://127.0.0.1:5173` |
| `API_HOST` | Backend bind address | `0.0.0.0` |
| `API_PORT` | Backend port | `8000` |
| `LOG_LEVEL` | Python logging level | `INFO` |

## Backend Setup

### 1. Install Python Dependencies

```bash
uv sync
```

This reads `pyproject.toml` and installs all runtime and development dependencies into a local `.venv` virtual environment.

### 2. Start PostgreSQL

```bash
make infra-up
```

This starts a PostgreSQL 16 container using Docker Compose, waits for the database to accept connections (up to 30 seconds), and prints "Infrastructure is ready." when complete.

Verify the database is running:

```bash
docker compose exec db pg_isready -U pulse -d pulse_board
```

Expected output: `/var/run/postgresql:5432 - accepting connections`

### 3. Run Database Migrations

```bash
make migrate
```

This runs all Alembic migrations against the database, creating the required tables and schema. The command starts infrastructure automatically if it is not already running.

### 4. Start the Backend

```bash
make dev-backend
```

The backend starts with hot reload on `http://localhost:8000`. Every time you save a Python file under `src/`, Uvicorn automatically reloads the application.

Verify the backend is running:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "healthy", "database": "connected"}
```

Browse the interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## Frontend Setup

### 1. Install Node.js Dependencies

```bash
cd frontend
nvm use 22
npm install
```

### 2. Start the Frontend

From within the `frontend/` directory:

```bash
npm run dev
```

Alternatively, from the project root:

```bash
make dev-frontend
```

The frontend starts with Vite's Hot Module Replacement (HMR) on `http://localhost:5173`. Changes to React components, styles, and TypeScript files are reflected in the browser instantly without a full page reload.

Verify the frontend is running by opening [http://localhost:5173](http://localhost:5173) in your browser.

## Running Both Together

To start PostgreSQL, the backend, and the frontend with a single command:

```bash
make dev
```

Press `Ctrl+C` to stop all services. The PostgreSQL container is stopped automatically on exit.

## Running Tests

All test commands are available as Makefile targets. Run `make help` to see the full list.

| Command | Description | Requires PostgreSQL |
|---------|-------------|---------------------|
| `make test` | Run Python unit tests with coverage (alias for `test-unit`) | No |
| `make test-unit` | Run Python unit tests with coverage and missing-line report | No |
| `make test-frontend` | Run frontend unit tests via Vitest | No |
| `make test-integration` | Run integration tests against a real database | Yes (started automatically) |
| `make test-all` | Run all tests (unit + integration + frontend) with HTML coverage report | Yes (started automatically) |
| `make test-coverage` | Run Python tests with full HTML coverage report | Yes (started automatically) |
| `make test-e2e` | Run Playwright end-to-end tests | Yes (started automatically) |

### Unit Tests

Unit tests run quickly with no external dependencies. They use mocked ports and never touch the database.

```bash
make test
```

This produces a coverage report in the terminal showing line-by-line coverage for the `pulse_board` package. The project enforces a minimum coverage threshold of 80%.

### Frontend Tests

Frontend tests use Vitest and run against the React components and MobX ViewModels.

```bash
make test-frontend
```

### Integration Tests

Integration tests verify that infrastructure adapters (repositories, database queries) work correctly against a real PostgreSQL instance. The command starts PostgreSQL automatically if it is not already running.

```bash
make test-integration
```

### End-to-End Tests

End-to-end tests use Playwright to simulate real user interactions in a browser. They exercise the full stack: frontend, backend, and database.

```bash
make test-e2e
```

This command starts PostgreSQL, runs database migrations, and then executes the Playwright test suite.

### Full Test Suite with Coverage Report

Run every test category and generate an HTML coverage report:

```bash
make test-all
```

Open `htmlcov/index.html` in your browser to view the detailed coverage report.

## Code Quality

### Linting

Run all linters across both backend and frontend:

```bash
make lint
```

This executes the following checks in sequence:

1. **ruff check** -- Python linting (style, imports, unused variables)
2. **ruff format --check** -- Python formatting verification
3. **pyright** -- Python static type checking
4. **ESLint** -- TypeScript/React linting (via `npm run lint` in `frontend/`)

All checks must pass before opening a pull request.

### Auto-Formatting

Automatically fix Python formatting and import ordering:

```bash
make format
```

This runs `ruff check --fix` (auto-fixable lint issues) followed by `ruff format` (code formatting). The project enforces an 88-character line length and isort-compatible import ordering.

Frontend formatting is handled by ESLint's auto-fix capabilities. Run it from the `frontend/` directory:

```bash
cd frontend && npm run lint -- --fix
```

## Available Makefile Targets

Run `make help` to see all targets with descriptions. Here is the complete reference:

| Command | Description |
|---------|-------------|
| `make help` | Show all available targets with descriptions |
| `make dev` | Start backend, frontend, and infrastructure |
| `make dev-backend` | Start backend with hot reload |
| `make dev-frontend` | Start frontend with HMR |
| `make migrate` | Run database migrations |
| `make test` | Run unit tests (alias) |
| `make test-unit` | Run Python unit tests with coverage |
| `make test-frontend` | Run frontend unit tests |
| `make test-integration` | Run integration tests |
| `make test-all` | Run all tests with coverage |
| `make test-coverage` | Run Python tests with full coverage report |
| `make test-e2e` | Run end-to-end tests |
| `make lint` | Run linters (ruff + pyright + ESLint) |
| `make format` | Auto-format Python code |
| `make infra-up` | Start PostgreSQL in Docker |
| `make infra-down` | Stop infrastructure services |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run application in Docker |
| `make docker-prod-up` | Start production stack |
| `make docker-prod-down` | Stop production stack |
| `make docker-prod-logs` | View production logs |
| `make clean` | Remove all build artifacts and infrastructure |
| `make version` | Show current version |
| `make version-patch` | Bump patch version (0.1.0 -> 0.1.1) |
| `make version-minor` | Bump minor version (0.1.0 -> 0.2.0) |
| `make version-major` | Bump major version (0.1.0 -> 1.0.0) |

## Troubleshooting

### Port 5432 is already in use

Another PostgreSQL instance (or another Docker container) is using port 5432. Either stop the conflicting service or change `POSTGRES_PORT` in your `.env` file:

```bash
# .env
POSTGRES_PORT=5433
DATABASE_URL=postgresql+psycopg2://pulse:pulse_dev_password@localhost:5433/pulse_board
```

Then restart infrastructure:

```bash
make infra-down
make infra-up
```

### Port 8000 or 5173 is already in use

Another process is occupying the backend or frontend port. Find and stop it:

```bash
lsof -i :8000   # Find process on port 8000
lsof -i :5173   # Find process on port 5173
```

Change `API_PORT` in `.env` for the backend, or edit `frontend/vite.config.ts` for the frontend.

### Database connection refused

Confirm PostgreSQL is running:

```bash
docker compose ps
```

If the `db` container is not listed or shows an unhealthy status, restart it:

```bash
make infra-down
make infra-up
```

Check the container logs for errors:

```bash
docker compose logs db
```

### `uv` command not found

Install uv following the [official guide](https://docs.astral.sh/uv/getting-started/installation/). On macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell or run `source ~/.bashrc` (or `source ~/.zshrc`).

### `nvm` or `node` command not found

Install nvm following the [official guide](https://github.com/nvm-sh/nvm#installing-and-updating), then install Node.js 22:

```bash
nvm install 22
nvm use 22
```

### Migrations fail with "relation already exists"

The database schema is out of sync. Reset it by stopping infrastructure with volume removal, then re-running migrations:

```bash
docker compose down -v
make infra-up
make migrate
```

**Warning**: This deletes all data in the local development database.

### Python type errors from pyright

Run pyright to see specific errors:

```bash
uv run pyright
```

Common fixes:

- Add explicit `None` checks for `Optional` types
- Use type narrowing (`isinstance`, `is not None`) before accessing attributes
- Add missing type annotations to function parameters and return values

## Next Steps

- **[Deployment Guide](deployment.md)** -- Build and deploy Pulse Board with Docker.
- **[Testing Strategy](../testing/testing-strategy.md)** -- Understand the testing philosophy and coverage goals.
- **[Test Conventions](../testing/test-conventions.md)** -- Follow naming patterns and checklists when adding tests.
- **[Architecture Decision Records](../adr/)** -- Review design decisions for the technology stack and patterns.
