# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.13-slim AS runtime

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-editable

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser alembic.ini ./

# Copy built frontend
COPY --chown=appuser:appuser --from=frontend-builder /app/frontend/dist ./static/

# Set environment defaults
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

EXPOSE 8000

# Health check using Python stdlib (no curl needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Switch to non-root user
USER appuser

CMD ["uv", "run", "uvicorn", "pulse_board.presentation.api.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
