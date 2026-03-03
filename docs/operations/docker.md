# Docker Reference

Reference documentation for Docker configuration and container management in Pulse Board. Covers development infrastructure, production deployment, and the application image.

## Prerequisites

| Tool | Minimum Version | Verify With |
|------|-----------------|-------------|
| Docker Engine or Docker Desktop | 24+ | `docker --version` |
| Docker Compose (v2 plugin) | 2.0+ | `docker compose version` |

Docker Compose must be the v2 plugin (`docker compose`), not the legacy standalone binary (`docker-compose`).

## Development Infrastructure

Development uses a single PostgreSQL container defined in `docker-compose.yml`. The Makefile handles starting, stopping, and readiness checks automatically.

### Starting and Stopping

```bash
make infra-up      # Start PostgreSQL and wait until it accepts connections
make infra-down    # Stop PostgreSQL (data is preserved in the volume)
make clean         # Stop PostgreSQL, remove volumes, and delete all build artifacts
```

`make infra-up` runs `docker compose up -d` and then polls `pg_isready` in a loop (up to 30 seconds) before returning. Commands that depend on the database -- `make dev`, `make dev-backend`, `make migrate`, `make test-integration`, and `make test-e2e` -- call `make infra-up` internally, so you rarely need to run it directly.

### Services

| Service | Image | Host Port | Container Port | Description |
|---------|-------|-----------|----------------|-------------|
| `db` | `postgres:16-alpine` | `${POSTGRES_PORT:-5432}` | 5432 | PostgreSQL database |

### Environment Variables

The development compose file reads these variables from your `.env` file (or shell environment), with defaults for local development:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `pulse` | Database username |
| `POSTGRES_PASSWORD` | `pulse_dev_password` | Database password |
| `POSTGRES_DB` | `pulse_board` | Database name |
| `POSTGRES_PORT` | `5432` | Host port mapping for PostgreSQL |

Override the host port when 5432 is already in use:

```bash
POSTGRES_PORT=5433 make infra-up
```

### Volume

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `postgres_data` | `/var/lib/postgresql/data` | Persists database data between container restarts |

To remove the volume and reset the database to a clean state, run `make clean`. This also deletes Python caches, frontend build artifacts, and `node_modules`.

### Health Check

The development database container uses a health check to signal readiness:

| Parameter | Value |
|-----------|-------|
| Command | `pg_isready -U ${POSTGRES_USER:-pulse} -d ${POSTGRES_DB:-pulse_board}` |
| Interval | 5 seconds |
| Timeout | 5 seconds |
| Retries | 5 |
| Start period | 10 seconds |

## Production Stack

The production stack is defined in `docker-compose.prod.yml`. It runs the application and database together behind a bridge network.

### Starting and Stopping

```bash
make docker-prod-up     # Build and start the production stack
make docker-prod-down   # Stop the production stack
make docker-prod-logs   # Tail logs from all production services
```

`make docker-prod-up` passes `--build` to Docker Compose, so it rebuilds the application image on every invocation. This ensures the running container always reflects the latest source code.

### Services

| Service | Host Port | Description |
|---------|-----------|-------------|
| `app` | `${APP_PORT:-8000}` | Pulse Board application (backend + static frontend) |
| `db` | Internal only | PostgreSQL database (not exposed to the host) |

The `app` service depends on `db` with `condition: service_healthy`, so Docker Compose waits for the database health check to pass before starting the application.

### Network

| Network | Driver | Purpose |
|---------|--------|---------|
| `pulse-network` | `bridge` | Isolates inter-service communication between `app` and `db` |

The application connects to the database using the hostname `db` (the Docker Compose service name) on port 5432 within the `pulse-network` bridge network.

### Required Environment Variables

The production compose file requires `POSTGRES_PASSWORD` to be set. If it is missing, Docker Compose exits with an error:

```
POSTGRES_PASSWORD is required
```

Set it before starting the stack:

```bash
export POSTGRES_PASSWORD=your-secure-password
make docker-prod-up
```

Additional environment variables for the `app` service:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `pulse` | Database username |
| `POSTGRES_DB` | `pulse_board` | Database name |
| `CORS_ORIGINS` | `http://localhost:8000` | Comma-separated allowed CORS origins |
| `APP_PORT` | `8000` | Host port mapping for the application |
| `LOG_LEVEL` | `INFO` | Application log level |

## Application Docker Image

The `Dockerfile` uses a multi-stage build to produce a minimal production image.

### Build Stages

| Stage | Base Image | Purpose |
|-------|------------|---------|
| `frontend-builder` | `node:22-alpine` | Installs npm dependencies and builds the React frontend |
| `runtime` | `python:3.13-slim` | Installs Python dependencies and runs the application |

### Building the Image

```bash
make docker-build
```

This builds and tags the image as both `pulse-board:<version>` (from `pyproject.toml`) and `pulse-board:latest`.

### Running the Image Standalone

```bash
make docker-run
```

This runs the container with `--network host` and loads environment variables from `.env`. The application listens on port 8000. Use this for quick local testing of the production image against a database running on the host.

### Security

- The container runs as a non-root user (`appuser`, UID 1000, GID 1000).
- The runtime stage uses `python:3.13-slim` to minimize the attack surface.
- Application source files are owned by `appuser`.

### Health Check

| Parameter | Value |
|-----------|-------|
| Command | `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"` |
| Interval | 30 seconds |
| Timeout | 5 seconds |
| Start period | 10 seconds |
| Retries | 3 |

The health check uses Python's standard library (`urllib.request`) instead of `curl` to avoid installing additional packages in the image.

### Exposed Port

The container exposes port 8000. The `CMD` starts Uvicorn bound to `0.0.0.0:8000`.

### What the Image Contains

| Path | Contents |
|------|----------|
| `/app/src/` | Python application source code |
| `/app/migrations/` | Alembic migration scripts |
| `/app/alembic.ini` | Alembic configuration |
| `/app/static/` | Built frontend assets (copied from the `frontend-builder` stage) |
| `/app/pyproject.toml` | Python project metadata and dependency lock |

## Commands Reference

| Command | Description |
|---------|-------------|
| `make infra-up` | Start development PostgreSQL and wait for readiness |
| `make infra-down` | Stop development infrastructure |
| `make docker-build` | Build the application Docker image |
| `make docker-run` | Run the application image with host networking |
| `make docker-prod-up` | Build and start the production stack |
| `make docker-prod-down` | Stop the production stack |
| `make docker-prod-logs` | Tail production service logs |
| `make clean` | Stop infrastructure, remove volumes, and delete all build artifacts |

## Troubleshooting

### Port Conflict on 5432

**Symptom**: `make infra-up` fails with "port is already allocated" or the container exits immediately.

**Cause**: Another process (a local PostgreSQL installation or another Docker container) is using port 5432.

**Solutions**:

1. Stop the conflicting process:
   ```bash
   # Check what is using port 5432
   lsof -i :5432
   ```

2. Use a different host port:
   ```bash
   POSTGRES_PORT=5433 make infra-up
   ```
   Update `POSTGRES_PORT` in your `.env` file to make the change persistent.

### Database Not Ready

**Symptom**: `make infra-up` prints "Error: Database did not become ready in time" after 30 seconds.

**Cause**: The PostgreSQL container failed to start or is taking unusually long to initialize.

**Solutions**:

1. Check the container logs:
   ```bash
   docker compose logs db
   ```

2. Verify the container is running:
   ```bash
   docker compose ps
   ```

3. Remove the volume and start fresh (this deletes all data):
   ```bash
   make clean
   make infra-up
   ```

### Permission Denied on Volume Mount

**Symptom**: The database container logs show permission errors when writing to the data directory.

**Cause**: The Docker volume has files owned by a different UID from a previous configuration.

**Solution**: Remove the volume and let Docker recreate it:

```bash
make clean
make infra-up
```

### Production App Exits Immediately

**Symptom**: `make docker-prod-up` starts but the `app` container exits with code 1.

**Cause**: Missing required environment variables or the database is not reachable.

**Solutions**:

1. Verify `POSTGRES_PASSWORD` is set:
   ```bash
   echo $POSTGRES_PASSWORD
   ```

2. Check application logs:
   ```bash
   make docker-prod-logs
   ```

3. Verify the database health check is passing:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

### Image Build Fails at Frontend Stage

**Symptom**: `make docker-build` fails during `npm ci` or `npm run build`.

**Cause**: Corrupted npm cache in Docker's build cache or incompatible `package-lock.json`.

**Solution**: Build without cache:

```bash
docker build --no-cache -t pulse-board:latest .
```
