# Database Migration Guide

How-to guide for managing database schema changes in Pulse Board using Alembic.

## Overview

Alembic manages all database schema changes through versioned migration scripts. Each migration represents an atomic change to the database schema -- a new table, a new column, a new constraint -- and is tracked by a unique revision ID.

**Key files and directories**:

| Path | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration (script location, logging) |
| `migrations/env.py` | Runtime configuration (database URL, model metadata) |
| `migrations/versions/` | Individual migration scripts |
| `src/pulse_board/infrastructure/database/models/` | SQLAlchemy ORM models |

**Database URL resolution**: Alembic reads the database URL from application settings, not from `alembic.ini`. The `migrations/env.py` file calls `get_settings()` which constructs the URL from environment variables (`POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`) or uses `DATABASE_URL` directly if set. See `.env.example` for all available variables.

## Running Migrations

Apply all pending migrations:

```bash
make migrate
```

This command starts the development database (`make infra-up`) automatically, then runs `uv run alembic upgrade head` to apply every migration that has not yet been applied.

Run `make migrate` after:

- Pulling changes that include new migration files
- Creating a new migration locally
- Resetting the database with `make clean`

## Creating a New Migration

Follow these steps to add a schema change.

### Step 1: Modify the SQLAlchemy Model

Edit or create the model in `src/pulse_board/infrastructure/database/models/`. Each model inherits from `Base` and defines the table schema using SQLAlchemy's declarative syntax.

```python
# src/pulse_board/infrastructure/database/models/example_model.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from pulse_board.infrastructure.database.base import Base


class ExampleModel(Base):
    """SQLAlchemy model for the examples table."""

    __tablename__ = "examples"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
```

### Step 2: Import the Model in env.py

Alembic's autogenerate feature detects schema changes by comparing the model metadata against the current database state. For this to work, every model must be imported in `migrations/env.py` so that it registers with `Base.metadata`.

Open `migrations/env.py` and add the import:

```python
from pulse_board.infrastructure.database.models.example_model import (
    ExampleModel,  # noqa: F401
)
```

The `# noqa: F401` comment suppresses the "imported but unused" linter warning. The import's side effect (registering the model with `Base.metadata`) is its purpose.

### Step 3: Generate the Migration

```bash
uv run alembic revision --autogenerate -m "description of change"
```

Use a short, lowercase description that explains what the migration does. Examples:

- `"create examples table"`
- `"add email column to users"`
- `"add unique constraint on poll_responses"`

Alembic creates a new file in `migrations/versions/` with `upgrade()` and `downgrade()` functions.

### Step 4: Review the Generated Migration

Open the generated file and verify:

- The `upgrade()` function contains the expected DDL operations
- The `downgrade()` function correctly reverses the upgrade
- No unintended changes leaked in (Alembic autogenerate can miss or misinterpret certain changes)

Common issues to watch for:

| Issue | What to check |
|-------|---------------|
| Missing index or constraint | Autogenerate may not detect all constraint types -- add manually |
| Incorrect column type | Verify types match your model definition |
| Dropped table or column | Autogenerate may generate drops for models not imported in `env.py` |
| Empty migration | The model was not imported in `env.py`, or no actual change was detected |

### Step 5: Apply the Migration

```bash
make migrate
```

Verify the migration applied successfully by checking the current revision:

```bash
uv run alembic current
```

## Current Migration History

Migrations are applied in order, from the initial revision to the head.

| Revision | Description | Depends On |
|----------|-------------|------------|
| `54baf5f8186d` | Create topics table | -- (initial) |
| `a1b2c3d4e5f6` | Create votes table | `54baf5f8186d` |
| `b2c3d4e5f6a7` | Create events and polls tables | `a1b2c3d4e5f6` |
| `c3d4e5f6a7b8` | Add unique constraint on poll_responses | `b2c3d4e5f6a7` |

View the full history at any time:

```bash
uv run alembic history
```

## Rolling Back Migrations

Roll back the last applied migration:

```bash
uv run alembic downgrade -1
```

Roll back to a specific revision:

```bash
uv run alembic downgrade a1b2c3d4e5f6
```

Roll back all migrations (returns the database to an empty state):

```bash
uv run alembic downgrade base
```

Rolling back runs the `downgrade()` function of each migration in reverse order. Always verify that `downgrade()` is correct when reviewing new migrations.

## Checking Migration Status

Show the current database revision:

```bash
uv run alembic current
```

Show the full migration history with applied status:

```bash
uv run alembic history
```

Compare the database state against the current models (useful for verifying no drift):

```bash
uv run alembic check
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `make migrate` | Start database and apply all pending migrations |
| `uv run alembic revision --autogenerate -m "msg"` | Generate a new migration from model changes |
| `uv run alembic upgrade head` | Apply all pending migrations |
| `uv run alembic downgrade -1` | Roll back the last migration |
| `uv run alembic downgrade base` | Roll back all migrations |
| `uv run alembic current` | Show current database revision |
| `uv run alembic history` | Show full migration history |
| `uv run alembic check` | Check for model/database drift |

## Rules and Best Practices

1. **One migration per atomic change.** Each migration should represent a single, self-contained schema change. Do not bundle unrelated changes into one migration.

2. **Always review autogenerated migrations.** Alembic's autogenerate is a starting point, not a finished product. It can miss index changes, produce incorrect types, or generate unintended drops.

3. **Migrations are immutable after deployment.** Never edit a migration that has been applied to a shared or production database. Create a new migration to correct issues.

4. **Import new models in `migrations/env.py`.** Alembic cannot detect changes for models it does not know about. Missing imports are the most common cause of empty migrations.

5. **Test migrations on realistic data.** Run `make migrate` against a database with representative data before deploying to production. Schema changes can fail or perform poorly on large tables.

6. **Write correct `downgrade()` functions.** Every migration must be reversible. Test rollbacks locally before merging.

7. **Use descriptive migration messages.** The message appears in the filename and in `alembic history` output. Write messages that explain what changed, not why.
