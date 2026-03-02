# Phase 2: Event Management (Vertical Slice)

## Overview

Deliver complete event creation and joining functionality end-to-end across all architecture layers. After this phase, an organizer can create a named event that generates a unique join code, and participants can enter that code to join the event and see its topic board — with full up/down voting and real-time WebSocket updates scoped to that event. The existing single-board mode continues to work without modification.

This is a vertical slice: domain entity, repository port, use cases, database migration, REST API, WebSocket channel, and React UI are all delivered together for the event creation and joining capability.

## Context

**Phase type**: Vertical slice

**Prerequisite**: Phase 1 (Scaffolding) must be complete — project structure, database connectivity, and CI are all in place.

**Gap analysis references**: Feature gap items #1 (Event/session creation) and #2 (Event join codes) from `docs/feature-gap-slido.md`.

## Functional Requirements

### FR-2.1: Event Domain Entity

**Status**: [ ] TODO

**Description**: Create an `Event` domain entity in the domain layer with business validation rules. The entity has zero framework dependencies.

**Acceptance Criteria**:

- Given an `Event` entity, When I inspect its properties, Then it has: `id` (UUID), `title` (str), `code` (str), `description` (str | None), `start_date` (datetime | None), `end_date` (datetime | None), `created_at` (datetime), `status` (EventStatus enum: ACTIVE | CLOSED)
- Given an empty or whitespace-only title, When creating an `Event`, Then a domain validation error is raised
- Given a title exceeding 200 characters, When creating an `Event`, Then a domain validation error is raised
- Given a `code` that is not 4-6 numeric digits, When creating an `Event`, Then a domain validation error is raised
- Given `start_date` and `end_date` both provided, When `end_date` is before `start_date`, Then a domain validation error is raised
- Given a new `Event`, When created, Then `status` defaults to `ACTIVE` and `created_at` defaults to now
- Given the `Event` entity file, When I inspect imports, Then there are NO imports from FastAPI, SQLAlchemy, Pydantic, or any other framework

### FR-2.2: Event Repository Port

**Status**: [ ] TODO

**Description**: Define an abstract `EventRepository` interface (port) in the domain layer that application use cases depend on.

**Acceptance Criteria**:

- Given the `EventRepository` port, When I inspect it, Then it defines the following methods: `create(event: Event) -> Event`, `get_by_id(event_id: UUID) -> Event | None`, `get_by_code(code: str) -> Event | None`, `list_active() -> list[Event]`, `is_code_unique_among_active(code: str) -> bool`
- Given the port, When I inspect it, Then it is an Abstract Base Class (ABC) with no concrete implementation
- Given the port file, When I inspect imports, Then there are only domain-layer imports (no framework, no SQLAlchemy)

### FR-2.3: Join Code Generation Domain Service

**Status**: [ ] TODO

**Description**: Implement a `JoinCodeGenerator` domain service that produces cryptographically random 6-digit numeric codes and retries on collision.

**Acceptance Criteria**:

- Given the `JoinCodeGenerator`, When `generate()` is called, Then it returns a string of exactly 6 numeric digits (e.g., `"482931"`)
- Given a repository where every candidate code is already taken (mocked for testing), When `generate()` is called 10 times without finding a unique code, Then it raises a `CodeGenerationError` domain exception
- Given the `JoinCodeGenerator` in the domain layer, When I inspect imports, Then there are NO framework imports; only Python standard library (`secrets`, `random`, or `os.urandom`)

### FR-2.4: Create Event Use Case

**Status**: [ ] TODO

**Description**: Implement the `CreateEventUseCase` in the application layer. It validates input, generates a unique join code via the domain service, and persists the event through the repository port.

**Acceptance Criteria**:

- Given a valid title and optional description/dates, When the use case executes, Then a new `Event` is persisted via the `EventRepository` and returned
- Given an empty title, When the use case executes, Then a domain validation error is raised and the repository is never called
- Given a `JoinCodeGenerator` that returns a code already in use, When the use case executes, Then the generator is retried until a unique code is found and the event is persisted with the unique code
- Given the use case constructor, When I inspect it, Then it accepts `EventRepository` and `JoinCodeGenerator` as injected dependencies (no concrete imports)
- Given the use case, When I inspect its input DTO, Then it has: `title` (str), `description` (str | None), `start_date` (datetime | None), `end_date` (datetime | None)

### FR-2.5: Join Event Use Case

**Status**: [ ] TODO

**Description**: Implement the `JoinEventUseCase` in the application layer. It looks up an event by its join code and validates it is active.

**Acceptance Criteria**:

- Given a valid 6-digit code matching an ACTIVE event, When the use case executes, Then the `Event` entity is returned
- Given a code that does not match any event, When the use case executes, Then an `EventNotFoundError` application exception is raised
- Given a code that matches a CLOSED event, When the use case executes, Then an `EventNotActiveError` application exception is raised
- Given the use case constructor, When I inspect it, Then it accepts `EventRepository` as its only injected dependency

### FR-2.6: Get Event Use Case

**Status**: [ ] TODO

**Description**: Implement the `GetEventUseCase` in the application layer. It retrieves a single event by its internal UUID.

**Acceptance Criteria**:

- Given a valid UUID matching an existing event, When the use case executes, Then the `Event` entity is returned
- Given a UUID that does not match any event, When the use case executes, Then an `EventNotFoundError` application exception is raised

### FR-2.7: List Event Topics Use Case

**Status**: [ ] TODO

**Description**: Implement the `ListEventTopicsUseCase` in the application layer. It retrieves topics scoped to a specific event, sorted by score descending then created_at descending.

**Acceptance Criteria**:

- Given a valid event ID, When the use case executes, Then only `Topic` records with a matching `event_id` are returned
- Given topics with `event_id = NULL` (single-board mode), When this use case executes, Then those topics are NOT included in the result
- Given the event-scoped topics, When the use case executes, Then topics are sorted by score descending, then created_at descending
- Given an event with no topics, When the use case executes, Then an empty list is returned

### FR-2.8: Update Topic Entity to Support event_id

**Status**: [ ] TODO

**Description**: Extend the existing `Topic` domain entity and repository port to accept an optional `event_id` foreign key, preserving backward compatibility with the existing single-board mode.

**Acceptance Criteria**:

- Given the updated `Topic` entity, When I inspect its properties, Then it includes `event_id` (UUID | None) in addition to existing fields
- Given `event_id = None`, When a topic is created, Then it behaves identically to the current single-board topic (no regression)
- Given `event_id` set to a valid event UUID, When a topic is created, Then it is scoped to that event
- Given the existing `TopicRepository` port, When I inspect it, Then `create(topic)` still works and `list_active()` continues to return only topics where `event_id IS NULL`
- Given the existing `GET /api/topics` endpoint, When called, Then it ONLY returns topics where `event_id IS NULL` (single-board behavior is unchanged)

### FR-2.9: Create Topic Use Case Updated for event_id

**Status**: [ ] TODO

**Description**: Update the existing `CreateTopicUseCase` to accept an optional `event_id`. When provided, the topic is scoped to that event; when absent, it falls through to single-board mode.

**Acceptance Criteria**:

- Given `event_id = None` in the input DTO, When the use case executes, Then the topic is created with `event_id = None` (single-board, no regression)
- Given a valid `event_id` in the input DTO, When the use case executes, Then the topic is persisted with that `event_id`
- Given an `event_id` that does not correspond to an ACTIVE event, When the use case executes, Then an `EventNotActiveError` is raised and no topic is persisted

### FR-2.10: SQLAlchemy Event Repository Implementation

**Status**: [ ] TODO

**Description**: Implement the `EventRepository` port using SQLAlchemy 2.0 in the infrastructure layer.

**Acceptance Criteria**:

- Given valid event data, When `create(event)` is called, Then a row is inserted into the `events` table and the domain entity is returned
- Given a code that exists in the `events` table with status `ACTIVE`, When `get_by_code(code)` is called, Then the matching domain entity is returned
- Given a code that does not exist, When `get_by_code(code)` is called, Then `None` is returned
- Given an event UUID, When `get_by_id(event_id)` is called, Then the matching domain entity is returned or `None`
- Given the implementation, When I inspect it, Then it maps between SQLAlchemy ORM models and domain `Event` entities (ORM models are NOT used as domain entities)
- Given `is_code_unique_among_active(code)`, When the code exists among ACTIVE events, Then `False` is returned; otherwise `True`

### FR-2.11: Alembic Migrations for Event Support

**Status**: [ ] TODO

**Description**: Create Alembic migrations to add the `events` table and add `event_id` as a nullable foreign key on the `topics` table.

**Acceptance Criteria**:

- Given the migrations, When applied with `uv run alembic upgrade head`, Then an `events` table exists with columns: `id` (UUID PK), `title` (VARCHAR 200, NOT NULL), `code` (VARCHAR 6, NOT NULL, UNIQUE), `description` (TEXT, NULLABLE), `start_date` (TIMESTAMPTZ, NULLABLE), `end_date` (TIMESTAMPTZ, NULLABLE), `status` (VARCHAR, NOT NULL, default `ACTIVE`), `created_at` (TIMESTAMPTZ, NOT NULL)
- Given the migrations, When applied, Then the `topics` table gains a nullable `event_id` (UUID FK → `events.id`) column with an index
- Given the migrations, When rolled back, Then the `event_id` column is removed from `topics` and the `events` table is dropped — in that order to respect FK constraints
- Given all existing topic rows, When the migration is applied, Then their `event_id` defaults to NULL (no data loss)

### FR-2.12: Event REST API Endpoints

**Status**: [ ] TODO

**Description**: Create REST API endpoints for event management in the presentation layer, following the existing FastAPI patterns.

**Acceptance Criteria**:

- Given a valid JSON body `{"title": "Team Retro"}`, When I `POST /api/events/`, Then a 201 response is returned with the created event including its generated `code`
- Given an invalid body (empty title), When I `POST /api/events/`, Then a 422 response is returned
- Given a valid 6-digit code for an ACTIVE event, When I `GET /api/events/join/{code}`, Then a 200 response is returned with the event details
- Given a code for a non-existent event, When I `GET /api/events/join/{code}`, Then a 404 response is returned
- Given a code for a CLOSED event, When I `GET /api/events/join/{code}`, Then a 409 response is returned with an error message indicating the event is no longer active
- Given a valid event UUID, When I `GET /api/events/{id}`, Then a 200 response is returned with the event details
- Given a valid event UUID, When I `GET /api/events/{id}/topics`, Then a 200 response is returned with topics scoped to that event, sorted by score descending
- Given all new endpoints, When I inspect `/docs`, Then they are documented with request and response schemas

### FR-2.13: Event-Scoped WebSocket Channel

**Status**: [ ] TODO

**Description**: Extend the existing WebSocket infrastructure to support per-event channels so real-time updates (new topic, score update, censure) are broadcast only to participants of the same event, not to single-board users.

**Acceptance Criteria**:

- Given an event with code `"482931"`, When a participant connects to `ws://localhost:8000/ws/events/482931`, Then they are subscribed to the event-scoped channel
- Given a participant in event `"482931"` casts a vote, When the vote is processed, Then the score update is broadcast ONLY to participants in channel `"482931"` — not to single-board WebSocket clients
- Given the existing `/ws` endpoint (single-board), When a vote is cast on a single-board topic (`event_id = NULL`), Then the broadcast goes ONLY to single-board clients — not to event-channel clients
- Given a participant disconnects from an event channel, When the disconnection occurs, Then the connection is removed from that event's channel without affecting other channels
- Given a new topic is submitted to an event via `POST /api/events/{id}/topics`, When it is persisted, Then a `new_topic` message is broadcast to the event's WebSocket channel

### FR-2.14: Event Creation UI — EventCreationForm

**Status**: [ ] TODO

**Description**: Implement the `EventCreationForm` React component and its `EventCreationViewModel` (MobX). An organizer fills out the form to create an event and receives the generated join code.

**Acceptance Criteria**:

- Given the `EventCreationForm`, When rendered, Then it displays fields: title (required), description (optional textarea), start date (optional date picker), end date (optional date picker)
- Given a title exceeding 200 characters, When typing, Then the character counter turns red and the submit button is disabled
- Given an empty title, When the submit button is inspected, Then it is disabled
- Given start date and end date both entered where end is before start, When inspecting the form, Then a validation message is displayed and submit is disabled
- Given a valid form submission, When the organizer clicks "Create Event", Then `POST /api/events/` is called via the `EventCreationViewModel`
- Given a successful creation response, When the API returns, Then the generated join code is displayed prominently in a confirmation view (e.g., "Your event code is 482931") with a copy-to-clipboard button
- Given the form, When I inspect it, Then the form container has `id="event-creation-form"`, the title input has `id="event-title-input"`, the description textarea has `id="event-description-input"`, and the submit button has `id="event-create-submit"`
- Given the copy button, When clicked, Then the join code is copied to the clipboard and a success toast is shown
- Given the `EventCreationViewModel`, When I inspect it, Then it has observable properties: `title`, `description`, `startDate`, `endDate`, `isSubmitting`, `error`, `createdEvent` (Event | null)
- Given the React components, When I inspect them, Then they are wrapped with `observer()` and contain NO business logic — all state and actions are delegated to the ViewModel

### FR-2.15: Event Join UI — EventJoinPage

**Status**: [ ] TODO

**Description**: Implement the `EventJoinPage` React component and its `EventJoinViewModel` (MobX). A participant enters a join code to navigate into the event topic board.

**Acceptance Criteria**:

- Given the `EventJoinPage`, When rendered, Then it displays a numeric code input field and a "Join" button
- Given the code input, When I inspect it, Then it accepts only numeric digits and is limited to 6 characters
- Given a 6-digit code for an ACTIVE event, When the participant clicks "Join", Then `GET /api/events/join/{code}` is called and on success the participant is navigated to `/events/{code}`
- Given a code for a non-existent or CLOSED event, When the API responds with 404 or 409, Then an inline error message is shown (not a crash)
- Given the join page, When I inspect elements, Then the code input has `id="event-join-code-input"` and the submit button has `id="event-join-submit"`
- Given the `EventJoinViewModel`, When I inspect it, Then it has observable properties: `code`, `isLoading`, `error`
- Given the React component, When I inspect it, Then it is wrapped with `observer()` and contains NO inline state — all state is in the ViewModel

### FR-2.16: Event Board View — EventBoardView

**Status**: [ ] TODO

**Description**: Implement the `EventBoardView` React component and its `EventBoardViewModel` (MobX). It reuses the existing topic board UI scoped to a specific event, including real-time updates via the event-scoped WebSocket channel.

**Acceptance Criteria**:

- Given the route `/events/:code`, When a participant navigates to it, Then `GET /api/events/join/{code}` is called first to resolve the event, and then `GET /api/events/{id}/topics` loads the event-scoped topic list
- Given the event topic board, When rendered, Then it displays the event title, a topic list (same `TopicCard` component as single-board), and a topic submission form
- Given a topic submitted on the event board, When the participant submits, Then `POST /api/events/{id}/topics` is called (with the resolved `event_id`) — NOT `POST /api/topics`
- Given the `EventBoardViewModel`, When it initializes, Then it connects to `ws://localhost:8000/ws/events/{code}` for event-scoped real-time updates
- Given a `score_update` WebSocket message on the event channel, When received, Then the affected topic's score is updated in the ViewModel's observable topic list
- Given a `topic_censured` message on the event channel, When received, Then the topic is removed from the event's observable topic list and a toast notification is shown
- Given a `new_topic` message on the event channel, When received, Then the new topic is inserted into the event's observable topic list at the correct sorted position
- Given the `EventBoardViewModel`, When I inspect it, Then it has observable properties: `event` (Event | null), `topics` (array), `isLoading`, `error`; and a computed property `sortedTopics` sorted by score descending then created_at descending
- Given the React component, When I inspect it, Then it is wrapped with `observer()` and the topic board elements follow the existing ID convention (e.g., `id="topic-form"`, `id="topic-input"` reused within event context)

### FR-2.17: Landing Page Updated with Event Entry Points

**Status**: [ ] TODO

**Description**: Update the existing application landing page to surface "Create Event" and "Join Event" buttons alongside the existing single-board quick-start path.

**Acceptance Criteria**:

- Given the landing page, When rendered, Then it displays three clearly labeled options: "Start Board" (existing single-board path), "Create Event" (navigates to event creation form), and "Join Event" (navigates to the join code input page)
- Given the "Create Event" button, When clicked, Then the user is navigated to the `EventCreationForm` route
- Given the "Join Event" button, When clicked, Then the user is navigated to the `EventJoinPage` route
- Given the existing "Start Board" path, When used, Then behavior is identical to the pre-Phase-2 flow (no regression)
- Given the landing page, When I inspect elements, Then the "Create Event" button has `id="landing-create-event"`, the "Join Event" button has `id="landing-join-event"`, and the existing board button retains its existing ID

### FR-2.18: Frontend Routing for Event Pages

**Status**: [ ] TODO

**Description**: Add React Router routes for the new event pages without breaking existing routes.

**Acceptance Criteria**:

- Given the router configuration, When I inspect it, Then it includes: `/events/new` → `EventCreationForm`, `/events/join` → `EventJoinPage`, `/events/:code` → `EventBoardView`
- Given the existing `/` route, When navigated to, Then the landing page renders unchanged (no regression)
- Given the existing single-board route (if any), When navigated to, Then it renders unchanged

## Non-Goals for This Phase

- No passcode protection on events — this is deferred to a future tier-3 feature
- No event archival, closure, or deletion by organizers
- No co-host or collaborator access
- No present mode (a future phase)
- No multiple-choice polls (a future phase)
- No event analytics dashboard
- No QR code display (a future phase)
- No named vs. anonymous toggle
- No question moderation
- No data export

## Testing Requirements

### Unit Tests

All Python unit test files MUST mirror the source directory structure under `tests/unit/`.

**Event Domain Entity** (`tests/unit/domain/entities/event_tests.py`):
- [ ] Valid `Event` creation with all fields succeeds
- [ ] Empty title raises domain validation error
- [ ] Title exceeding 200 characters raises domain validation error
- [ ] Code shorter than 4 digits raises domain validation error
- [ ] Code longer than 6 digits raises domain validation error
- [ ] Code containing non-numeric characters raises domain validation error
- [ ] `end_date` before `start_date` raises domain validation error
- [ ] New event defaults `status` to `ACTIVE` and `created_at` to now
- [ ] `Event` entity file has zero framework imports

**JoinCodeGenerator Domain Service** (`tests/unit/domain/services/join_code_generator_tests.py`):
- [ ] `generate()` returns a 6-digit numeric string
- [ ] `generate()` raises `CodeGenerationError` after 10 failed uniqueness checks (mock repository)
- [ ] Generated codes have no leading zeros (or document if they are permitted)

**CreateEventUseCase** (`tests/unit/application/use_cases/create_event_use_case_tests.py`):
- [ ] Valid input persists an event via the mocked repository and returns the entity
- [ ] Empty title raises domain validation error; repository is never called
- [ ] Code collision causes retry; second attempt with unique code succeeds
- [ ] All dependencies are injected (no concrete infrastructure imports in the use case)

**JoinEventUseCase** (`tests/unit/application/use_cases/join_event_use_case_tests.py`):
- [ ] Valid code for ACTIVE event returns the event entity
- [ ] Unknown code raises `EventNotFoundError`
- [ ] Valid code for CLOSED event raises `EventNotActiveError`

**GetEventUseCase** (`tests/unit/application/use_cases/get_event_use_case_tests.py`):
- [ ] Valid UUID returns the event entity from the mocked repository
- [ ] Unknown UUID raises `EventNotFoundError`

**ListEventTopicsUseCase** (`tests/unit/application/use_cases/list_event_topics_use_case_tests.py`):
- [ ] Returns topics with matching `event_id` sorted by score descending, then `created_at` descending
- [ ] Topics with `event_id = None` are excluded from results
- [ ] Empty event returns an empty list

**Updated Topic Entity** (`tests/unit/domain/entities/topic_tests.py` — regression):
- [ ] Topic with `event_id = None` behaves identically to pre-Phase-2 behavior (no regression)
- [ ] Topic with a valid `event_id` UUID is valid

**Updated CreateTopicUseCase** (`tests/unit/application/use_cases/create_topic_use_case_tests.py` — regression + new):
- [ ] `event_id = None` creates a single-board topic (regression — existing tests must still pass)
- [ ] Valid `event_id` creates an event-scoped topic
- [ ] Invalid `event_id` (no matching ACTIVE event) raises `EventNotActiveError`

### Integration Tests

**SQLAlchemy Event Repository** (`tests/integration/infrastructure/repositories/event_repository_tests.py`):
- [ ] `create(event)` inserts a row in the `events` table and returns the domain entity
- [ ] `get_by_code(code)` retrieves the correct event for an ACTIVE event
- [ ] `get_by_code(code)` returns `None` for an unknown code
- [ ] `is_code_unique_among_active(code)` returns `False` when code exists among ACTIVE events
- [ ] Unique constraint on `code` column prevents duplicate ACTIVE codes at the database level

**Event API Endpoints** (`tests/integration/presentation/api/routes/event_routes_tests.py`):
- [ ] `POST /api/events/` with valid body returns 201 and event with generated code
- [ ] `POST /api/events/` with empty title returns 422
- [ ] `GET /api/events/join/{code}` with valid ACTIVE code returns 200 with event details
- [ ] `GET /api/events/join/{code}` with unknown code returns 404
- [ ] `GET /api/events/join/{code}` with CLOSED event code returns 409
- [ ] `GET /api/events/{id}` with valid UUID returns 200
- [ ] `GET /api/events/{id}/topics` returns only topics scoped to that event, sorted correctly

**Topics in Event Scope** (`tests/integration/presentation/api/routes/topics_in_event_tests.py`):
- [ ] `POST /api/events/{id}/topics` creates a topic with the correct `event_id`
- [ ] `GET /api/topics` (single-board) returns ONLY topics with `event_id IS NULL` after adding event-scoped topics

**Alembic Migration**:
- [ ] `uv run alembic upgrade head` succeeds with the new migration applied
- [ ] `uv run alembic downgrade -1` succeeds and removes `event_id` from topics and drops the `events` table

### End-to-End Tests

All E2E tests MUST use element `id` attributes for locators following the convention `{component}-{element}-{identifier}`.

**File**: `tests/e2e/event_management_tests.py` (or `event_management.spec.ts` if using Playwright TypeScript):

- [ ] **Full event flow**: Navigate to landing page → click "Create Event" → fill title → submit → confirm code is displayed → copy code → navigate to join page → enter code → join event → verify event title shown → submit a topic → verify topic appears in event board
- [ ] **Vote within event**: Join event → submit topic → upvote it → verify score increments → downvote it → verify score transitions (cancel upvote, then downvote)
- [ ] **Real-time event updates**: Open two browser tabs on same event board → submit topic in tab 1 → verify topic appears in tab 2 without reload → vote in tab 1 → verify score updates in tab 2
- [ ] **Invalid join code**: Navigate to join page → enter unknown code → verify error message displayed (no crash)
- [ ] **Single-board regression**: Navigate to `/` → use existing single-board flow → submit topic → vote → verify behavior is unchanged

**Regression — existing E2E tests MUST still pass**:
- [ ] All pre-existing Playwright tests for single-board topic submission pass unchanged
- [ ] All pre-existing Playwright tests for voting (upvote, downvote, cancel) pass unchanged
- [ ] All pre-existing Playwright tests for real-time WebSocket updates (two-tab test) pass unchanged

## Documentation Deliverables

- [ ] **API documentation**: All 7 new endpoints (`POST /api/events/`, `GET /api/events/join/{code}`, `GET /api/events/{id}`, `GET /api/events/{id}/topics`, `POST /api/events/{id}/topics`, and the event-scoped WebSocket `ws://.../ws/events/{code}`) are documented in the FastAPI auto-generated Swagger UI with accurate request/response schemas and status code descriptions
- [ ] **README update**: The top-level `README.md` is updated with a "Creating and Joining Events" section that explains: (1) how to create an event as an organizer, (2) how participants join using the code, and (3) that the original quick-start single-board mode remains available at `/`
- [ ] **Docstrings**: All new Python modules (entity, repository port, use cases, repository implementation, route handlers) have PEP 257-compliant docstrings
- [ ] **ADR (optional)**: If the team chooses to use a per-event WebSocket channel strategy over a single shared channel with filtering, document the decision in `docs/decisions/` with rationale

## Technical Notes

### Event Join Code Strategy

- Use Python `secrets.randbelow(900000) + 100000` to generate 6-digit codes in the range 100000–999999 (ensures no leading zeros)
- Uniqueness is checked against ACTIVE events only; CLOSED event codes may be reused
- The use case retries code generation up to 10 times before raising `CodeGenerationError`
- A unique index on `(code, status)` where `status = 'ACTIVE'` is preferred at the database level to enforce uniqueness at the storage layer as a safety net

### Backward Compatibility

- The `Topic` entity gains `event_id: UUID | None = None` — adding an optional field with a default is a non-breaking change
- `GET /api/topics` (single-board) filters `WHERE event_id IS NULL` — existing clients are unaffected
- The single-board WebSocket `/ws` route is untouched; the new per-event channel is a separate route at `/ws/events/{code}`
- All existing integration and E2E tests for single-board behavior MUST pass without modification

### WebSocket Channel Architecture

- The existing `ConnectionManager` is extended (or subclassed) to support named channels keyed by event code
- `connect(websocket, channel: str = "global")` places the connection in the named channel group
- `broadcast_to_channel(channel, message)` sends only to that channel's group
- Single-board broadcasts use `channel = "global"` (the existing behavior, unchanged)

### Onion Architecture Placement

| Artifact | Layer |
|---|---|
| `Event` entity, `EventStatus` enum, `JoinCodeGenerator`, `CodeGenerationError` | `domain/` |
| `EventRepository` port | `domain/ports/` |
| `CreateEventUseCase`, `JoinEventUseCase`, `GetEventUseCase`, `ListEventTopicsUseCase` | `application/use_cases/` |
| `CreateEventDTO`, `EventResponseDTO` | `application/dtos/` |
| `SQLAlchemyEventRepository`, event ORM model, Alembic migration | `infrastructure/` |
| Route handlers, Pydantic request/response schemas | `presentation/api/` |
| `EventCreationForm`, `EventJoinPage`, `EventBoardView`, ViewModels | `frontend/src/presentation/` |
| HTTP API client for event endpoints | `frontend/src/infrastructure/api/` |

### Frontend Route Structure

```
/                       → Landing page (updated with Create/Join buttons)
/events/new             → EventCreationForm
/events/join            → EventJoinPage
/events/:code           → EventBoardView (resolves code → event, then loads topics)
```

### Scale Constraint

- Target: 100 concurrent participants per event (per `00-config.md`)
- Each event WebSocket channel should handle 100 concurrent connections without degradation
- No special sharding or Redis pub/sub is required for this phase; a single FastAPI process is sufficient for the target scale

## Validation Checklist

Before marking this phase complete, verify all of the following:

**Domain Layer**:
- [ ] `Event` entity exists in `src/domain/entities/` with zero framework imports
- [ ] `EventStatus` enum exists in `src/domain/` (or co-located with the entity)
- [ ] `EventRepository` abstract port exists in `src/domain/ports/`
- [ ] `JoinCodeGenerator` domain service exists in `src/domain/services/`
- [ ] `CodeGenerationError` domain exception exists in `src/domain/`

**Application Layer**:
- [ ] `CreateEventUseCase` exists in `src/application/use_cases/`
- [ ] `JoinEventUseCase` exists in `src/application/use_cases/`
- [ ] `GetEventUseCase` exists in `src/application/use_cases/`
- [ ] `ListEventTopicsUseCase` exists in `src/application/use_cases/`
- [ ] `CreateTopicUseCase` updated to handle optional `event_id`
- [ ] DTOs exist for event creation input and response

**Infrastructure Layer**:
- [ ] `SQLAlchemyEventRepository` exists in `src/infrastructure/repositories/`
- [ ] Alembic migration exists for `events` table and `topics.event_id`
- [ ] `uv run alembic upgrade head` succeeds
- [ ] `uv run alembic downgrade -1` succeeds

**Presentation Layer**:
- [ ] `POST /api/events/` endpoint exists and returns 201 with generated code
- [ ] `GET /api/events/join/{code}` endpoint returns 200 (active) or 404/409
- [ ] `GET /api/events/{id}` endpoint returns 200 or 404
- [ ] `GET /api/events/{id}/topics` endpoint returns scoped, sorted topics
- [ ] Event-scoped WebSocket route `ws://.../ws/events/{code}` is registered
- [ ] Single-board `GET /api/topics` still returns only `event_id IS NULL` topics

**Frontend**:
- [ ] Landing page has "Create Event" and "Join Event" buttons with correct IDs
- [ ] `EventCreationForm` renders, validates, submits, and displays the generated code
- [ ] `EventJoinPage` accepts a code, calls join API, navigates on success, shows error on failure
- [ ] `EventBoardView` loads event-scoped topics, supports topic submission and voting
- [ ] `EventBoardView` connects to event-scoped WebSocket and handles `score_update`, `new_topic`, `topic_censured` messages
- [ ] All ViewModels use MobX `observable`, `computed`, and `action` decorators; components are `observer()`-wrapped

**Tests**:
- [ ] All new unit tests pass: `make test-unit`
- [ ] All new integration tests pass: `make test-integration`
- [ ] All new E2E tests pass: `make test-e2e`
- [ ] All pre-existing tests (single-board) still pass without modification
- [ ] `uv run ruff format . --check` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run pyright` reports no errors

**Documentation**:
- [ ] All 7 new endpoints documented in Swagger UI (`/docs`)
- [ ] `README.md` updated with event creation and joining instructions
- [ ] All new Python modules have docstrings
