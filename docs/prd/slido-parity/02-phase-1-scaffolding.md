# Phase 1: Scaffolding — Event and Poll Infrastructure

## Overview

- **Phase**: 1 of N
- **Type**: Scaffolding (no user-facing business functionality delivered)
- **Status**: [ ] TODO
- **Feature**: slido-parity
- **Depends on**: None (first phase)

---

## Context and Purpose

Pulse Board currently operates as a single persistent board: all topics exist in one global namespace. To support Slido-style audience interaction (event join codes, polls, present mode, host view), the application needs a multi-event data model and routing foundation.

This phase creates that foundation without delivering any visible UI or API behavior beyond empty route stubs. All subsequent slido-parity phases depend on the data models, port interfaces, migration, and routing structure established here.

**Existing system constraints:**
- The `topics` table already exists with `id`, `content`, `score`, `created_at` columns (migration `54baf5f8186d`).
- The `votes` table references `topics` via `topic_id` (migration `a1b2c3d4e5f6`).
- Single-board mode MUST continue to work after this phase. The `event_id` column added to `topics` MUST be nullable so existing rows and code paths are unaffected.
- Domain entities MUST NOT import FastAPI, SQLAlchemy, or Pydantic.
- ORM models are separate from domain entities per onion architecture.

---

## Prerequisites

- None. This is the first phase of the slido-parity feature.

---

## Functional Requirements

### FR-1.1 — Event domain entity

**Priority**: P0 — MUST

The system MUST define an `Event` dataclass in `src/pulse_board/domain/entities/event.py` with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | Required, generated on creation |
| `title` | `str` | 1–150 characters, stripped, HTML-escaped |
| `code` | `str` | 4–8 alphanumeric characters, uppercase |
| `passcode` | `str \| None` | Optional; if present, 4–20 characters |
| `start_date` | `datetime` | Timezone-aware |
| `end_date` | `datetime` | Timezone-aware; MUST be after `start_date` |
| `status` | `EventStatus` | Enum: `draft`, `active`, `closed` |
| `created_at` | `datetime` | Timezone-aware, set at creation |

A `create` classmethod MUST perform all validation and raise `ValidationError` on invalid input. Direct construction bypasses validation for repository reconstitution.

**Acceptance criteria:**

```
Given a valid title, code, start_date, and end_date
When Event.create() is called
Then an Event instance is returned with a generated UUID, status=draft, and created_at set to now(UTC)

Given a title that exceeds 150 characters
When Event.create() is called
Then a ValidationError is raised with a descriptive message

Given an end_date that is not after start_date
When Event.create() is called
Then a ValidationError is raised

Given a code that contains non-alphanumeric characters
When Event.create() is called
Then a ValidationError is raised

Given an optional passcode shorter than 4 characters
When Event.create() is called
Then a ValidationError is raised
```

---

### FR-1.2 — Poll domain entity

**Priority**: P0 — MUST

The system MUST define a `Poll` dataclass in `src/pulse_board/domain/entities/poll.py` with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | Required, generated on creation |
| `event_id` | `uuid.UUID` | Required |
| `question` | `str` | 1–500 characters, stripped, HTML-escaped |
| `poll_type` | `PollType` | Enum: `multiple_choice`, `rating`, `open_text`, `word_cloud` |
| `options` | `list[str]` | Empty list for non-multiple-choice types; 2–10 items for `multiple_choice`; each option 1–150 chars |
| `is_active` | `bool` | Defaults to `False` |
| `created_at` | `datetime` | Timezone-aware, set at creation |

A `create` classmethod MUST validate all fields. The `PollType` enum MUST be defined in the same module.

**Acceptance criteria:**

```
Given a valid event_id, question, and poll_type of multiple_choice with 3 options
When Poll.create() is called
Then a Poll instance is returned with is_active=False and a generated UUID

Given poll_type of multiple_choice and an empty options list
When Poll.create() is called
Then a ValidationError is raised

Given poll_type of multiple_choice and 11 options
When Poll.create() is called
Then a ValidationError is raised

Given poll_type of open_text and a non-empty options list
When Poll.create() is called
Then a ValidationError is raised (options must be empty for non-multiple-choice)

Given a question of 501 characters
When Poll.create() is called
Then a ValidationError is raised
```

---

### FR-1.3 — PollResponse domain entity

**Priority**: P0 — MUST

The system MUST define a `PollResponse` dataclass in `src/pulse_board/domain/entities/poll_response.py` with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | Required, generated on creation |
| `poll_id` | `uuid.UUID` | Required |
| `fingerprint_id` | `str` | 1–255 characters, stripped |
| `response_data` | `dict[str, object]` | Arbitrary JSON-serializable dict; MUST NOT be empty |
| `created_at` | `datetime` | Timezone-aware, set at creation |

A `create` classmethod MUST validate all fields.

**Acceptance criteria:**

```
Given a valid poll_id, fingerprint_id, and non-empty response_data
When PollResponse.create() is called
Then a PollResponse instance is returned with a generated UUID and created_at set

Given an empty response_data dict
When PollResponse.create() is called
Then a ValidationError is raised

Given a fingerprint_id of empty string
When PollResponse.create() is called
Then a ValidationError is raised
```

---

### FR-1.4 — Event and Poll repository port interfaces

**Priority**: P0 — MUST

The system MUST define abstract base classes (ABCs) for repository ports in the domain layer:

**`src/pulse_board/domain/ports/event_repository_port.py`** MUST declare:
- `create(event: Event) -> Event`
- `get_by_code(code: str) -> Event | None`
- `get_by_id(id: uuid.UUID) -> Event | None`
- `list_active() -> list[Event]`
- `update_status(id: uuid.UUID, status: EventStatus) -> Event | None`

**`src/pulse_board/domain/ports/poll_repository_port.py`** MUST declare:
- `create(poll: Poll) -> Poll`
- `get_by_id(id: uuid.UUID) -> Poll | None`
- `list_by_event(event_id: uuid.UUID) -> list[Poll]`
- `set_active(id: uuid.UUID, is_active: bool) -> Poll | None`

**`src/pulse_board/domain/ports/poll_response_repository_port.py`** MUST declare:
- `create(response: PollResponse) -> PollResponse`
- `list_by_poll(poll_id: uuid.UUID) -> list[PollResponse]`
- `get_by_fingerprint(poll_id: uuid.UUID, fingerprint_id: str) -> PollResponse | None`

All port files MUST contain only ABC declarations, no framework imports, and full docstrings on every method.

**Acceptance criteria:**

```
Given a class that inherits EventRepository without implementing all abstract methods
When that class is instantiated
Then Python raises TypeError listing the unimplemented methods

Given a class that correctly implements all EventRepository abstract methods
When that class is instantiated
Then it instantiates without error
```

---

### FR-1.5 — WebSocket event type extensions

**Priority**: P0 — MUST

The system MUST extend `src/pulse_board/domain/events.py` with new frozen dataclasses for poll and event lifecycle domain events:

- `PollActivatedEvent(DomainEvent)` — fields: `poll_id: uuid.UUID`, `event_id: uuid.UUID`
- `PollDeactivatedEvent(DomainEvent)` — fields: `poll_id: uuid.UUID`, `event_id: uuid.UUID`
- `PollResponseReceivedEvent(DomainEvent)` — fields: `poll_id: uuid.UUID`, `event_id: uuid.UUID`
- `EventStatusChangedEvent(DomainEvent)` — fields: `event_id: uuid.UUID`, `new_status: str`

These domain events define the contract for what the WebSocket infrastructure will broadcast. No broadcasting logic is implemented in this phase.

**Acceptance criteria:**

```
Given PollActivatedEvent is instantiated with a poll_id and event_id
When the dataclass is created
Then occurred_at is set automatically and the instance is frozen (immutable)

Given an attempt to mutate occurred_at on any new domain event
When the mutation is attempted
Then Python raises FrozenInstanceError
```

---

### FR-1.6 — ORM models for events, polls, and poll_responses

**Priority**: P0 — MUST

The system MUST create SQLAlchemy ORM models in the infrastructure layer:

**`src/pulse_board/infrastructure/database/models/event_model.py`**:
- `EventModel` mapped to `events` table
- Columns: `id` (UUID PK), `title` (String 150), `code` (String 8, unique, indexed), `passcode` (String 20, nullable), `start_date` (DateTime tz), `end_date` (DateTime tz), `status` (String 20), `created_at` (DateTime tz, server_default now())

**`src/pulse_board/infrastructure/database/models/poll_model.py`**:
- `PollModel` mapped to `polls` table
- Columns: `id` (UUID PK), `event_id` (UUID FK → events.id, on_delete=CASCADE), `question` (String 500), `poll_type` (String 30), `options` (JSONB), `is_active` (Boolean, default False), `created_at` (DateTime tz, server_default now())

**`src/pulse_board/infrastructure/database/models/poll_response_model.py`**:
- `PollResponseModel` mapped to `poll_responses` table
- Columns: `id` (UUID PK), `poll_id` (UUID FK → polls.id, on_delete=CASCADE), `fingerprint_id` (String 255), `response_data` (JSONB), `created_at` (DateTime tz, server_default now())

The `TopicModel` in `topic_model.py` MUST be extended with a nullable `event_id` column (UUID FK → events.id, on_delete=SET NULL, nullable=True). The `__init__.py` for models MUST import all models so Alembic autogenerate detects them.

**Acceptance criteria:**

```
Given all ORM models are imported
When SQLAlchemy inspects the metadata
Then events, polls, poll_responses tables are present in the metadata

Given TopicModel is inspected
When columns are listed
Then event_id is present, nullable, and references the events table

Given PollModel is inspected
When the event_id foreign key is inspected
Then on_delete is CASCADE
```

---

### FR-1.7 — Alembic migration for schema changes

**Priority**: P0 — MUST

The system MUST provide a single Alembic migration that:
1. Creates the `events` table with all columns defined in FR-1.6
2. Creates the `polls` table with all columns defined in FR-1.6
3. Creates the `poll_responses` table with all columns defined in FR-1.6
4. Adds nullable `event_id` column to the existing `topics` table with a FK to `events.id` (SET NULL on delete)
5. Creates index on `events.code` for fast join-code lookups

The migration MUST include a correct `downgrade()` function that reverses all changes in reverse order (drop FK from topics, drop poll_responses, drop polls, drop events).

**Acceptance criteria:**

```
Given a database at the prior migration revision
When alembic upgrade head is run
Then all four schema changes are applied without error
And the topics table retains all existing rows with event_id = NULL

Given a database at the new revision
When alembic downgrade -1 is run
Then all four schema changes are reversed without error
And the topics table retains all rows minus the event_id column
```

---

### FR-1.8 — Backend API routing structure

**Priority**: P0 — MUST

The system MUST register two new router prefixes in `src/pulse_board/presentation/api/app.py`:

- `events_router` at prefix `/api/events` with tag `events`
- `polls_router` at prefix `/api/polls` with tag `polls`

Each router file (`routes/events.py`, `routes/polls.py`) MUST exist and contain at minimum one stub endpoint that returns HTTP 501 Not Implemented, so the routes appear in the OpenAPI docs. No business logic is implemented in this phase.

The existing `openapi_tags` list in `create_app()` MUST be extended with entries for `events` and `polls`.

**Acceptance criteria:**

```
Given the FastAPI application is started
When GET /api/events is requested
Then the response status is 501 (or 404 if the stub uses a non-matching method)
And the /docs endpoint lists the events and polls tag sections

Given the application imports are loaded
When the app module is imported
Then no ImportError is raised
And all existing routes (health, topics, votes, websocket) continue to resolve correctly
```

---

### FR-1.9 — Frontend routing structure

**Priority**: P0 — MUST

The system MUST add three new client-side routes to the React application using the existing routing library (React Router or equivalent already in the project):

| Route | Component | Purpose |
|---|---|---|
| `/events/:code` | `EventParticipantPage` (stub) | Participant view for a specific event |
| `/events/:code/present` | `EventPresentPage` (stub) | Presenter/projector display view |
| `/events/:code/admin` | `EventAdminPage` (stub) | Host/admin management view |

Each stub component MUST render a placeholder `<div>` with the route name and the `:code` path parameter displayed, so routing can be verified manually. Components MUST be placed in `frontend/src/presentation/components/events/`.

The existing `/` root route and all single-board functionality MUST remain fully operational.

**Acceptance criteria:**

```
Given the frontend application is running
When the user navigates to /events/TEST01
Then the EventParticipantPage stub renders with "TEST01" visible in the page

Given the user navigates to /events/TEST01/present
Then the EventPresentPage stub renders

Given the user navigates to /events/TEST01/admin
Then the EventAdminPage stub renders

Given the user navigates to /
Then the existing topic board renders exactly as before with no regressions
```

---

### FR-1.10 — Frontend domain entities and port interfaces for Event and Poll

**Priority**: P0 — MUST

The system MUST define TypeScript interfaces in the frontend domain layer:

**`frontend/src/domain/entities/Event.ts`**:
```typescript
export type EventStatus = "draft" | "active" | "closed";

export interface Event {
  readonly id: string;
  readonly title: string;
  readonly code: string;
  readonly passcode: string | null;
  readonly start_date: string;
  readonly end_date: string;
  readonly status: EventStatus;
  readonly created_at: string;
}
```

**`frontend/src/domain/entities/Poll.ts`**:
```typescript
export type PollType = "multiple_choice" | "rating" | "open_text" | "word_cloud";

export interface Poll {
  readonly id: string;
  readonly event_id: string;
  readonly question: string;
  readonly poll_type: PollType;
  readonly options: string[];
  readonly is_active: boolean;
  readonly created_at: string;
}
```

**`frontend/src/domain/ports/EventApiPort.ts`**:
```typescript
export interface EventApiPort {
  getEventByCode(code: string): Promise<Event>;
}
```

**`frontend/src/domain/ports/PollApiPort.ts`**:
```typescript
export interface PollApiPort {
  listPollsByEvent(eventId: string): Promise<Poll[]>;
}
```

All new entity and port files MUST be re-exported from the existing barrel files (`frontend/src/domain/entities/index.ts`, `frontend/src/domain/ports/index.ts`).

**Acceptance criteria:**

```
Given the TypeScript compiler is run against the frontend source
When tsc --noEmit is executed
Then zero type errors are reported for the new entity and port files

Given the barrel index files are imported
When the Event, Poll, EventApiPort, and PollApiPort named exports are accessed
Then they resolve to the correct types without TypeScript errors
```

---

## Non-Goals for This Phase

The following are explicitly out of scope and MUST NOT be implemented:

- Event creation, listing, or join UI (deferred to Phase 2)
- Poll creation, activation, or participation UI (deferred to Phase 3+)
- Any API endpoint that returns real data (stubs only)
- WebSocket broadcasting of poll events (deferred to Phase 4+)
- Authentication or authorization of any kind
- Event passcode validation logic
- Repository implementations (SQLAlchemy concrete classes) — port interfaces only
- Event join code generation algorithm
- QR code generation
- Present mode display content
- Any analytics, reporting, or export

---

## Testing Requirements

### Unit Tests — Backend

**Location**: `tests/unit/pulse_board/domain/entities/`

All tests MUST be pure unit tests with no database, no mocks of framework code, and execution under 2 seconds each.

**`tests/unit/pulse_board/domain/entities/event_tests.py`**:
- [ ] `test_create_valid_event` — FR-1.1 happy path
- [ ] `test_create_event_title_too_long` — raises `ValidationError`
- [ ] `test_create_event_title_empty` — raises `ValidationError`
- [ ] `test_create_event_end_before_start` — raises `ValidationError`
- [ ] `test_create_event_end_equals_start` — raises `ValidationError`
- [ ] `test_create_event_code_invalid_chars` — raises `ValidationError`
- [ ] `test_create_event_code_too_short` — raises `ValidationError`
- [ ] `test_create_event_code_too_long` — raises `ValidationError`
- [ ] `test_create_event_passcode_too_short` — raises `ValidationError`
- [ ] `test_create_event_no_passcode_allowed` — None passcode is valid
- [ ] `test_event_title_html_escaped` — `<script>` in title is escaped
- [ ] `test_event_status_defaults_to_draft` — newly created event has `status == EventStatus.DRAFT`
- [ ] `test_event_created_at_is_utc` — `created_at.tzinfo` is UTC

**`tests/unit/pulse_board/domain/entities/poll_tests.py`**:
- [ ] `test_create_multiple_choice_poll_valid`
- [ ] `test_create_poll_question_empty` — raises `ValidationError`
- [ ] `test_create_poll_question_too_long` — raises `ValidationError`
- [ ] `test_create_multiple_choice_no_options` — raises `ValidationError`
- [ ] `test_create_multiple_choice_too_many_options` — raises `ValidationError`
- [ ] `test_create_open_text_poll_with_options` — raises `ValidationError`
- [ ] `test_create_rating_poll_valid`
- [ ] `test_create_word_cloud_poll_valid`
- [ ] `test_poll_defaults_to_inactive`
- [ ] `test_poll_question_html_escaped`

**`tests/unit/pulse_board/domain/entities/poll_response_tests.py`**:
- [ ] `test_create_poll_response_valid`
- [ ] `test_create_poll_response_empty_response_data` — raises `ValidationError`
- [ ] `test_create_poll_response_empty_fingerprint` — raises `ValidationError`

**`tests/unit/pulse_board/domain/events_tests.py`** (extends existing events tests if any):
- [ ] `test_poll_activated_event_is_frozen`
- [ ] `test_poll_deactivated_event_is_frozen`
- [ ] `test_poll_response_received_event_is_frozen`
- [ ] `test_event_status_changed_event_is_frozen`
- [ ] `test_domain_events_have_occurred_at`

### Migration Tests

**Location**: `tests/integration/pulse_board/infrastructure/database/`

**`tests/integration/pulse_board/infrastructure/database/migration_tests.py`**:
- [ ] `test_migration_upgrade_creates_events_table` — after upgrade, `events` table exists with correct columns
- [ ] `test_migration_upgrade_creates_polls_table`
- [ ] `test_migration_upgrade_creates_poll_responses_table`
- [ ] `test_migration_upgrade_adds_event_id_to_topics` — column exists and is nullable
- [ ] `test_migration_downgrade_removes_event_id_from_topics` — column absent after downgrade
- [ ] `test_migration_downgrade_drops_new_tables`
- [ ] `test_existing_topic_rows_unaffected` — topics created before migration still exist after upgrade with `event_id = NULL`

### Regression Tests

All existing tests in `tests/unit/` and `tests/integration/` MUST pass without modification after this phase. No test file may be altered to accommodate this phase's changes (except adding new test files).

- [ ] Run `make test-all` and confirm zero failures

---

## Documentation Deliverables

### ADR — Event and Poll Data Model Design

**Location**: `docs/adr/001-event-poll-data-model.md`

The ADR MUST document:

1. **Context**: Pulse Board is transitioning from single-board to multi-event model to achieve Slido parity. Decision captures why the chosen schema was selected over alternatives.

2. **Decision — nullable `event_id` on `topics`**: Topics gain a nullable FK to `events`. Rationale: preserves single-board quick-start mode (no breaking change). Alternative considered: separate `event_topics` join table — rejected because it adds join complexity with no benefit given the 1:1 relationship.

3. **Decision — JSONB for `options` and `response_data`**: Poll options and response data use PostgreSQL JSONB. Rationale: poll types have heterogeneous shapes (MC options list vs. rating scale vs. free text). Alternative considered: separate options table — rejected because it requires N+1 queries and complicates the domain model for this stage. Note: JSONB is PostgreSQL-specific; accepted as the project already uses PostgreSQL exclusively.

4. **Decision — `poll_type` as string enum column**: The `poll_type` field is stored as a VARCHAR string rather than a PostgreSQL native ENUM type. Rationale: SQLAlchemy string columns are easier to migrate (adding a new poll type requires no ALTER TYPE). Alternative considered: PostgreSQL ENUM — rejected due to migration friction.

5. **Consequences**: Future phases requiring poll type–specific query filtering (e.g., "list all word cloud polls") will use a WHERE clause on the string column, which is fast with an index if needed.

### README Update

**Location**: Root `README.md`

Add a section titled "Route Structure" (or extend an existing section) that documents:
- Backend API prefixes: `/api/events`, `/api/polls`, existing `/api/topics`, `/api/votes`
- Frontend routes: `/` (board), `/events/:code` (participant), `/events/:code/present` (presenter), `/events/:code/admin` (admin)

---

## Technical Notes

### Maintaining Single-Board Mode Compatibility

The `event_id` FK on `topics` is nullable. No existing query in `TopicRepository`, `CreateTopicUseCase`, `ListTopicsUseCase`, or `CastVoteUseCase` may be modified to require `event_id`. All existing code paths treat `event_id` as absent and MUST function identically to pre-phase behavior.

### Domain Entity vs. ORM Model Separation

Follow the established pattern from `Topic` / `TopicModel`:
- Domain entities (`src/pulse_board/domain/entities/`) use `@dataclass`, have no SQLAlchemy imports, and validate through classmethods.
- ORM models (`src/pulse_board/infrastructure/database/models/`) extend `Base` and are the persistence representation.
- Repositories (not implemented in this phase) translate between the two.

### EventStatus and PollType as Python Enums

Define `EventStatus` and `PollType` as `enum.StrEnum` (Python 3.11+) so that enum values are also their string representations. This simplifies ORM storage (store `.value` directly) and JSON serialization without a custom encoder.

```python
import enum

class EventStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
```

### JSONB on PostgreSQL — SQLAlchemy Mapping

Use `sqlalchemy.dialects.postgresql.JSONB` in ORM models. In the domain entities, `options: list[str]` and `response_data: dict[str, object]` are plain Python types — no SQLAlchemy dependency leaks into the domain.

### Frontend Route Stub Components

Stub page components MUST use the existing Tailwind layout patterns from `frontend/src/presentation/components/layout/`. Each stub MUST include the `id` attribute convention established in `CLAUDE.md`:
- `id="event-participant-page"`, `id="event-present-page"`, `id="event-admin-page"`

This ensures Playwright E2E tests in future phases can reliably select the correct page.

### Alembic Migration Checklist

When generating the migration:
1. Import all new ORM models in `migrations/env.py` (or confirm the existing model auto-discovery imports `models/__init__.py` which exports all models).
2. Run `uv run alembic revision --autogenerate -m "add_events_polls_and_poll_responses"` and review the generated file before committing.
3. Manually verify the `downgrade()` function reverses operations in correct dependency order.

---

## Validation Checklist

Complete all items before marking this phase DONE.

### Domain Layer
- [ ] `Event` dataclass exists at `src/pulse_board/domain/entities/event.py`
- [ ] `EventStatus` StrEnum defined in the same module
- [ ] `Poll` dataclass exists at `src/pulse_board/domain/entities/poll.py`
- [ ] `PollType` StrEnum defined in the same module
- [ ] `PollResponse` dataclass exists at `src/pulse_board/domain/entities/poll_response.py`
- [ ] All three domain entities have `create` classmethods with full validation
- [ ] No SQLAlchemy, FastAPI, or Pydantic imports in any domain entity file
- [ ] `EventRepository` ABC exists at `src/pulse_board/domain/ports/event_repository_port.py`
- [ ] `PollRepository` ABC exists at `src/pulse_board/domain/ports/poll_repository_port.py`
- [ ] `PollResponseRepository` ABC exists at `src/pulse_board/domain/ports/poll_response_repository_port.py`
- [ ] Four new domain event dataclasses added to `src/pulse_board/domain/events.py`

### Infrastructure Layer
- [ ] `EventModel` ORM class exists at `src/pulse_board/infrastructure/database/models/event_model.py`
- [ ] `PollModel` ORM class exists at `src/pulse_board/infrastructure/database/models/poll_model.py`
- [ ] `PollResponseModel` ORM class exists at `src/pulse_board/infrastructure/database/models/poll_response_model.py`
- [ ] `TopicModel` has nullable `event_id` FK column pointing to `events.id`
- [ ] All new models imported in `src/pulse_board/infrastructure/database/models/__init__.py`
- [ ] Alembic migration file exists in `migrations/versions/`
- [ ] `alembic upgrade head` completes without error on a clean database
- [ ] `alembic downgrade -1` completes without error and restores prior state

### Presentation Layer — Backend
- [ ] `src/pulse_board/presentation/api/routes/events.py` exists with at least one stub endpoint
- [ ] `src/pulse_board/presentation/api/routes/polls.py` exists with at least one stub endpoint
- [ ] Both routers registered in `create_app()` with correct prefixes and tags
- [ ] `/docs` shows `events` and `polls` tag sections
- [ ] All existing endpoints (`/api/topics`, `/api/votes`, `/ws`, `/health`) return correct responses

### Presentation Layer — Frontend
- [ ] `EventParticipantPage` stub component exists in `frontend/src/presentation/components/events/`
- [ ] `EventPresentPage` stub component exists in the same folder
- [ ] `EventAdminPage` stub component exists in the same folder
- [ ] Three new routes registered in the app router (`/events/:code`, `/events/:code/present`, `/events/:code/admin`)
- [ ] `frontend/src/domain/entities/Event.ts` exists with correct interface
- [ ] `frontend/src/domain/entities/Poll.ts` exists with correct interface
- [ ] `frontend/src/domain/ports/EventApiPort.ts` exists
- [ ] `frontend/src/domain/ports/PollApiPort.ts` exists
- [ ] New entities and ports re-exported from barrel index files
- [ ] `tsc --noEmit` passes with zero errors

### Tests
- [ ] All unit tests for `Event`, `Poll`, `PollResponse` entities pass
- [ ] All unit tests for new domain events pass
- [ ] All migration integration tests pass
- [ ] `make test-all` passes with zero failures (no regressions)

### Documentation
- [ ] `docs/adr/001-event-poll-data-model.md` written and covers all five decision points
- [ ] Root `README.md` updated with route structure section
