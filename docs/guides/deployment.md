# Deployment Guide

This guide covers building and deploying Pulse Board using Docker. It includes instructions for local Docker builds, production deployment with Docker Compose, environment configuration, health monitoring, and operational commands.

For local development without Docker, see the [Development Setup](development-setup.md) guide.

## Overview

Pulse Board uses a multi-stage Docker build that produces a single container image with both the Python backend and the compiled frontend assets:

1. **Stage 1 (frontend-builder)**: Builds the React frontend with Vite, producing optimized static files.
2. **Stage 2 (runtime)**: Installs Python dependencies, copies the application source and Alembic migrations, and copies the built frontend assets into the `static/` directory.

The resulting image runs as a non-root user, includes a health check, and serves both the API and the frontend from a single process.

The production Docker Compose stack (`docker-compose.prod.yml`) runs two services -- the application and PostgreSQL -- on a dedicated bridge network with health checks, automatic restarts, and persistent database storage.

## Prerequisites

| Tool | Minimum Version |
|------|-----------------|
| **Docker** | Latest (with Compose plugin) |

Verify Docker and Compose are available:

```bash
docker --version
docker compose version
```

## Local Docker Build

Build and run the application image locally to verify the production build works before deploying.

### Build the Image

```bash
make docker-build
```

This builds a Docker image tagged with the current project version (from `pyproject.toml`) and `latest`:

```
pulse-board:0.1.0
pulse-board:latest
```

Verify the image was created:

```bash
docker images pulse-board
```

### Run on Host Network

To run the container against a local PostgreSQL instance (started via `make infra-up`):

```bash
make infra-up
make migrate
make docker-run
```

This runs the container with `--network host`, which allows it to reach PostgreSQL on `localhost:5432` using the connection settings from your `.env` file. The application serves on `http://localhost:8000`.

Verify the application is running:

```bash
curl http://localhost:8000/health
```

Open [http://localhost:8000](http://localhost:8000) in your browser to access the frontend (served as static files from the same origin).

## Production Deployment

The production stack runs both the application and PostgreSQL in Docker with a dedicated bridge network. No host services are required beyond Docker itself.

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set production-appropriate values:

```bash
# REQUIRED: Set a strong password (do not use the development default)
POSTGRES_PASSWORD=your-strong-password-here

# REQUIRED: Set allowed origins to your domain
CORS_ORIGINS=https://your-domain.com

# Optional: Customize other settings as needed
POSTGRES_USER=pulse
POSTGRES_DB=pulse_board
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

**Important**: The production Compose file requires `POSTGRES_PASSWORD` to be set. It will fail to start if this variable is missing or empty.

### 2. Start the Production Stack

```bash
make docker-prod-up
```

This command builds the application image (if not already built), starts PostgreSQL, waits for it to become healthy, and then starts the application container. Both services run in the background.

Verify both services are running and healthy:

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected output shows both `app` and `db` with a status of `Up` and health status of `healthy`.

Verify the application responds:

```bash
curl http://localhost:8000/health
```

Open `http://localhost:8000` in your browser to access the application (or your configured domain if behind a reverse proxy).

## Production Compose Services

The `docker-compose.prod.yml` file defines two services on a shared bridge network.

### app (Application)

| Property | Value |
|----------|-------|
| **Build** | Multi-stage Dockerfile (frontend + Python runtime) |
| **Port** | `${APP_PORT:-8000}:8000` (host:container) |
| **Depends on** | `db` (waits for healthy status) |
| **Health check** | `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"` |
| **Health check interval** | Every 30 seconds, 5-second timeout, 15-second start period, 3 retries |
| **Restart policy** | `unless-stopped` |
| **User** | `appuser` (UID 1000, non-root) |
| **Network** | `pulse-network` (bridge) |

The application connects to PostgreSQL using the service name `db` as the hostname (resolved via Docker's internal DNS on the bridge network). The `DATABASE_URL` is constructed automatically in the Compose file.

### db (PostgreSQL 16)

| Property | Value |
|----------|-------|
| **Image** | `postgres:16-alpine` |
| **Data persistence** | Named volume `postgres_data` mounted at `/var/lib/postgresql/data` |
| **Health check** | `pg_isready -U ${POSTGRES_USER:-pulse} -d ${POSTGRES_DB:-pulse_board}` |
| **Health check interval** | Every 5 seconds, 5-second timeout, 10-second start period, 5 retries |
| **Restart policy** | `unless-stopped` |
| **Network** | `pulse-network` (bridge) |

The database port is **not** exposed to the host in production. Only the application container can reach it via the bridge network.

### Network

| Property | Value |
|----------|-------|
| **Name** | `pulse-network` |
| **Driver** | `bridge` |

The bridge network isolates the application and database from other Docker containers on the host. External traffic reaches only the application container through the published port.

## Environment Variables

| Variable | Description | Default | Required in Production |
|----------|-------------|---------|------------------------|
| `POSTGRES_PASSWORD` | Database password | -- | **Yes** |
| `POSTGRES_USER` | Database username | `pulse` | No |
| `POSTGRES_DB` | Database name | `pulse_board` | No |
| `CORS_ORIGINS` | Comma-separated allowed origins for CORS | `http://localhost:8000` | **Yes** (set to your domain) |
| `API_HOST` | Backend bind address | `0.0.0.0` | No |
| `API_PORT` | Application port inside the container | `8000` | No |
| `APP_PORT` | Host port mapped to the container | `8000` | No |
| `LOG_LEVEL` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | No |

**Notes**:

- `APP_PORT` controls which host port maps to the container's port 8000. Set it if port 8000 is occupied on your host.
- `CORS_ORIGINS` must include the exact origin(s) your users access the application from. For production behind a reverse proxy, set this to your public domain (e.g., `https://pulse.example.com`).

## Health Checks

Both services include health checks that Docker uses to determine readiness and trigger automatic restarts.

### Application Health Check

The application exposes a `/health` endpoint that returns the service status and database connectivity:

```bash
curl http://localhost:8000/health
```

```json
{"status": "healthy", "database": "connected"}
```

Docker checks this endpoint every 30 seconds. If three consecutive checks fail, Docker restarts the container.

### Database Health Check

PostgreSQL health is verified using the `pg_isready` utility:

```bash
docker compose -f docker-compose.prod.yml exec db pg_isready -U pulse -d pulse_board
```

Docker checks database readiness every 5 seconds. The application container waits for the database to become healthy before starting (via the `depends_on` condition).

## Monitoring

### View Logs

Stream logs from both services in real time:

```bash
make docker-prod-logs
```

Press `Ctrl+C` to stop following logs.

To view logs from a specific service:

```bash
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f db
```

### Check Service Status

View the running state and health of all production services:

```bash
docker compose -f docker-compose.prod.yml ps
```

### Inspect Resource Usage

View CPU, memory, and network statistics:

```bash
docker compose -f docker-compose.prod.yml stats
```

## Stopping the Production Stack

Stop all services while preserving the database volume:

```bash
make docker-prod-down
```

To stop services **and remove the database volume** (destroys all data):

```bash
docker compose -f docker-compose.prod.yml down -v
```

**Warning**: The `-v` flag permanently deletes the `postgres_data` volume and all stored data. Use this only when you intend to start with a fresh database.

## Operational Reference

| Task | Command |
|------|---------|
| Build the Docker image | `make docker-build` |
| Run on host network (local testing) | `make docker-run` |
| Start the production stack | `make docker-prod-up` |
| Stop the production stack | `make docker-prod-down` |
| Stream production logs | `make docker-prod-logs` |
| Check service status | `docker compose -f docker-compose.prod.yml ps` |
| View resource usage | `docker compose -f docker-compose.prod.yml stats` |
| Remove everything including data | `docker compose -f docker-compose.prod.yml down -v` |

## Next Steps

- **[Development Setup](development-setup.md)** -- Configure a local development environment with hot reload and testing.
- **[Getting Started](getting-started.md)** -- Quick tutorial for first-time users.
- **[Architecture Decision Records](../adr/)** -- Review design decisions including the Docker and deployment strategy.
