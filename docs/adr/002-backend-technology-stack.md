# ADR 002: Backend Technology Stack -- FastAPI + SQLAlchemy + PostgreSQL

## Status

Accepted

## Date

2024-12-01

## Context and Problem Statement

The Community Pulse Board backend must serve a REST API for topic management and voting, handle concurrent vote submissions from many users, maintain ACID-compliant vote tallies, broadcast real-time events over WebSocket connections, and auto-generate API documentation for frontend integration. We need a backend stack that supports async request handling natively, provides a mature ORM for relational data modeling, and integrates with PostgreSQL for reliable data storage.

## Decision Drivers

- **Async support**: Native `async/await` for handling concurrent WebSocket connections and HTTP requests without thread pool exhaustion
- **ORM maturity**: A well-established ORM that supports both sync and async operations, schema migrations, and relationship modeling
- **Database reliability**: ACID transactions to guarantee vote count accuracy and prevent data corruption under concurrent writes
- **Automatic API documentation**: Machine-readable OpenAPI schema generation to accelerate frontend development
- **Python ecosystem**: Access to libraries for configuration management (Pydantic Settings), schema migrations (Alembic), and testing (pytest, httpx)
- **Developer productivity**: Minimal boilerplate for defining endpoints, request validation, and dependency injection

## Considered Options

1. FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Alembic + Pydantic Settings
2. Django + Django REST Framework + PostgreSQL
3. Flask + SQLAlchemy + PostgreSQL
4. Node.js + Express + Prisma + PostgreSQL

## Decision Outcome

We chose **Option 1: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16** because it provides native async support, automatic OpenAPI documentation, and a clean dependency injection system that aligns with our onion architecture. FastAPI's `Depends()` mechanism maps directly to the port/adapter pattern -- use cases receive repository implementations through dependency injection at the route level (see `presentation/api/dependencies.py`). SQLAlchemy 2.0's declarative models live in the infrastructure layer, cleanly separated from domain entities.

### Consequences

- **Good**: FastAPI's native async support handles WebSocket connections (ADR 004) and HTTP requests on the same event loop without blocking.
- **Good**: Automatic OpenAPI schema generation at `/docs` eliminates manual API documentation and enables frontend developers to explore endpoints interactively.
- **Good**: SQLAlchemy 2.0's type-annotated query API works well with Pyright for static type checking across the data access layer.
- **Good**: Alembic migrations are versioned alongside application code, ensuring database schema changes are tracked and reproducible.
- **Good**: Pydantic Settings loads configuration from environment variables with type validation, supporting 12-factor app principles.
- **Good**: PostgreSQL 16's `pg_isready` healthcheck integrates cleanly with Docker Compose (see `docker-compose.yml`).
- **Bad**: SQLAlchemy's ORM models in the infrastructure layer must be mapped to domain entities, creating a translation layer.
- **Bad**: FastAPI's async ecosystem requires careful handling of sync database drivers -- we use `psycopg2-binary` which requires sync session usage or thread pool execution.
- **Neutral**: The stack requires explicit layer boundaries (domain, application, infrastructure, presentation) rather than providing a convention-over-configuration approach.

## Pros and Cons of the Options

### Option 1: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16

- **Good**: Native `async def` route handlers and WebSocket endpoints share a single event loop, reducing resource consumption under concurrent load.
- **Good**: `Depends()` enables dependency injection without a framework -- repositories and use cases are wired at the route level.
- **Good**: Pydantic models for request/response validation generate OpenAPI schemas automatically with full type information.
- **Good**: SQLAlchemy 2.0's declarative API supports both synchronous and asynchronous sessions, providing migration flexibility.
- **Good**: Alembic auto-generates migration scripts from model changes via `alembic revision --autogenerate`.
- **Good**: Mature testing ecosystem -- `pytest-asyncio` for async tests, `httpx.AsyncClient` for API testing, `pytest-cov` for coverage.
- **Bad**: FastAPI is younger than Django/Flask, with a smaller (though rapidly growing) community.
- **Bad**: No built-in admin interface, user authentication framework, or ORM migration management -- each requires separate libraries.
- **Neutral**: Requires Python 3.13+ (specified in `pyproject.toml`), which is current but limits deployment to environments with this version available.

### Option 2: Django + Django REST Framework + PostgreSQL

- **Good**: Batteries-included framework with built-in admin, authentication, ORM, and migration system.
- **Good**: Largest Python web framework community with extensive documentation and third-party packages.
- **Good**: Django ORM provides a simple, Pythonic API for database queries.
- **Bad**: Django's ORM is synchronous by default; async support (introduced in Django 4.1+) is still maturing and not all ORM operations support async.
- **Bad**: Django REST Framework's serializers add overhead compared to Pydantic's validation performance.
- **Bad**: Django's monolithic structure conflicts with onion architecture -- models, views, and business logic are tightly coupled by convention.
- **Bad**: No native WebSocket support; requires Django Channels with an ASGI server and Redis backend, adding infrastructure complexity.

### Option 3: Flask + SQLAlchemy + PostgreSQL

- **Good**: Lightweight and flexible, with minimal opinions about application structure.
- **Good**: Flask-SQLAlchemy provides simple ORM integration.
- **Good**: Large ecosystem of extensions for common functionality.
- **Bad**: Flask is WSGI-based -- async support requires workarounds or migration to Quart.
- **Bad**: No built-in request validation or API documentation generation; requires Flask-Marshmallow or similar extensions.
- **Bad**: No built-in dependency injection; requires a separate library or manual wiring.
- **Bad**: WebSocket support requires Flask-SocketIO or a separate ASGI application.

### Option 4: Node.js + Express + Prisma + PostgreSQL

- **Good**: JavaScript/TypeScript on both frontend and backend enables code sharing (types, validation schemas).
- **Good**: Node.js event loop handles concurrent connections efficiently.
- **Good**: Prisma provides type-safe database access with auto-generated TypeScript types.
- **Bad**: Introduces a second language runtime in the deployment pipeline, increasing operational complexity.
- **Bad**: Express lacks built-in request validation and OpenAPI generation comparable to FastAPI.
- **Bad**: The team's primary expertise is in Python, which would slow development and increase the defect rate.
- **Neutral**: npm ecosystem is vast but package quality varies more widely than Python's.

## More Information

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL 16 documentation](https://www.postgresql.org/docs/16/)
- [Alembic documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Settings documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- Application factory: `src/pulse_board/presentation/api/app.py`
- Database models: `src/pulse_board/infrastructure/database/models/`
- Repository implementations: `src/pulse_board/infrastructure/repositories/`
- Configuration: `src/pulse_board/infrastructure/config/settings.py`
- Docker Compose infrastructure: `docker-compose.yml` (PostgreSQL 16 Alpine)
