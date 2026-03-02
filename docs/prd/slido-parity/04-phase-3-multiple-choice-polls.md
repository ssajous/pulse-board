# Phase 3: Multiple Choice Polls

## Overview

**Type**: Vertical slice — delivers one complete business capability end-to-end.

This phase implements the full lifecycle of a multiple choice poll: an event organizer creates a poll with a question and predefined options, activates it for their event, participants vote (one response per browser fingerprint per poll enforced), and results update in real-time for all viewers via WebSocket. Every layer is delivered together — domain entities, repository ports, use cases, PostgreSQL implementations, REST API endpoints, WebSocket events, and React UI components with MobX ViewModels.

After this phase, a user can open an event board, create a multiple choice poll, activate it, and watch votes arrive live as participants submit responses. This poll infrastructure also establishes the patterns that rating polls (Phase 5), open text polls (Phase 5), and word cloud polls (Phase 6) will build upon.

## Prerequisites

- Phase 2 (Event Management) MUST be complete
- Event domain entity and EventRepository port must exist
- Browser fingerprinting infrastructure (FingerprintJS v5) must be in place
- WebSocket `ConnectionManager` and `EventPublisher` port must be operational
- Alembic migration tooling must be configured

## Functional Requirements

### FR-3.1: Poll Domain Entity

**Description**: Create the `Poll` domain entity in the domain layer. The entity enforces question length limits and option count constraints as invariants. It has zero framework imports.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a `Poll` entity, When I inspect its properties, Then it has: `id` (UUID), `event_id` (UUID), `question` (str), `poll_type` (str, fixed to `"multiple_choice"` for this phase), `options` (list of `PollOption` value objects), `is_active` (bool, default `False`), `created_at` (datetime)
- Given a `PollOption` value object, When I inspect it, Then it has: `id` (UUID), `text` (str)
- Given a question exceeding 500 characters, When `Poll.create()` is called, Then a `ValidationError` is raised
- Given an empty question string, When `Poll.create()` is called, Then a `ValidationError` is raised
- Given fewer than 2 options, When `Poll.create()` is called, Then a `ValidationError` is raised with message "Poll requires at least 2 options"
- Given more than 10 options, When `Poll.create()` is called, Then a `ValidationError` is raised with message "Poll allows at most 10 options"
- Given an option with an empty text string, When `Poll.create()` is called, Then a `ValidationError` is raised
- Given the `Poll` entity file, When I inspect its imports, Then there are NO imports from FastAPI, SQLAlchemy, Pydantic, or any framework

### FR-3.2: PollResponse Domain Entity

**Description**: Create the `PollResponse` domain entity representing a single participant's answer to a poll. It enforces that a response must reference a valid option from the poll.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a `PollResponse` entity, When I inspect its properties, Then it has: `id` (UUID), `poll_id` (UUID), `option_id` (UUID), `fingerprint_id` (str), `created_at` (datetime)
- Given the `PollResponse` entity file, When I inspect its imports, Then there are NO framework imports
- Given a `PollResponse`, When constructed via the direct constructor, Then no validation is performed (for repository reconstitution)
- Given a `PollResponse`, When constructed via `PollResponse.create()`, Then `created_at` defaults to `datetime.now(UTC)` and `id` is a new UUID

### FR-3.3: Poll Repository Port

**Description**: Define an abstract `PollRepository` interface (port) in the domain layer that covers poll persistence operations.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given the `PollRepository` port, When I inspect it, Then it is an ABC with these abstract methods: `create(poll: Poll) -> Poll`, `get_by_id(id: UUID) -> Poll | None`, `list_by_event(event_id: UUID) -> list[Poll]`, `save(poll: Poll) -> Poll`
- Given the port, When I inspect its imports, Then only domain-layer imports are present (no infrastructure imports)

### FR-3.4: PollResponse Repository Port

**Description**: Define an abstract `PollResponseRepository` interface (port) in the domain layer.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given the `PollResponseRepository` port, When I inspect it, Then it is an ABC with these abstract methods: `create(response: PollResponse) -> PollResponse`, `find_by_poll_and_fingerprint(poll_id: UUID, fingerprint_id: str) -> PollResponse | None`, `count_by_option(poll_id: UUID, option_id: UUID) -> int`, `count_all_by_poll(poll_id: UUID) -> int`
- Given the port, When I inspect its imports, Then only domain-layer imports are present

### FR-3.5: CreatePollUseCase

**Description**: Implement the application use case for creating a multiple choice poll associated with an event.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a valid `event_id`, question string, and list of option texts (2-10 items), When `CreatePollUseCase.execute()` is called, Then a new `Poll` entity is persisted via `PollRepository` and returned as a `CreatePollResult` DTO
- Given an `event_id` that does not exist in `EventRepository`, When `CreatePollUseCase.execute()` is called, Then an `EntityNotFoundError` is raised and the poll is NOT persisted
- Given option texts containing only whitespace, When `CreatePollUseCase.execute()` is called, Then a `ValidationError` is raised before reaching the repository
- Given the use case constructor, When I inspect it, Then it accepts `PollRepository` and `EventRepository` via dependency injection
- Given a valid request, When the use case executes, Then the returned `CreatePollResult` contains: `id`, `event_id`, `question`, `options` (list of `{id, text}`), `is_active`, `created_at`

### FR-3.6: ActivatePollUseCase

**Description**: Implement the application use case for toggling a poll's active state. Only one poll per event may be active at a time; activating a new poll automatically deactivates any currently active poll in that event.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given an inactive poll, When `ActivatePollUseCase.execute(poll_id, activate=True)` is called, Then `poll.is_active` is set to `True` and persisted
- Given an active poll for event E, When a different poll in event E is activated, Then the first poll's `is_active` is set to `False` before the second poll is set to `True`
- Given `activate=False`, When `ActivatePollUseCase.execute()` is called, Then `poll.is_active` is set to `False` and persisted
- Given a `poll_id` that does not exist, When `ActivatePollUseCase.execute()` is called, Then an `EntityNotFoundError` is raised
- Given an activation, When it succeeds, Then the use case returns the updated `Poll` entity
- Given the use case constructor, When I inspect it, Then it accepts `PollRepository` via dependency injection
- Given the `PollRepository` port, When I inspect it, Then it includes `find_active_by_event(event_id: UUID) -> Poll | None` to support the deactivation step

### FR-3.7: SubmitPollResponseUseCase

**Description**: Implement the application use case for recording a participant's choice. Enforces one response per browser fingerprint per poll.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a poll that is active, a valid `option_id` belonging to that poll, and a `fingerprint_id` with no prior response, When `SubmitPollResponseUseCase.execute()` is called, Then a `PollResponse` is created and persisted
- Given a `fingerprint_id` that has already responded to the same poll, When `SubmitPollResponseUseCase.execute()` is called, Then a `DuplicateResponseError` is raised and no new record is written
- Given a poll that is NOT active, When `SubmitPollResponseUseCase.execute()` is called, Then a `PollNotActiveError` is raised
- Given an `option_id` that does not belong to the specified poll, When `SubmitPollResponseUseCase.execute()` is called, Then a `ValidationError` is raised
- Given a `poll_id` that does not exist, When `SubmitPollResponseUseCase.execute()` is called, Then an `EntityNotFoundError` is raised
- Given successful submission, When the use case executes, Then the returned `SubmitPollResponseResult` contains: `poll_id`, `option_id`, `fingerprint_id`
- Given the use case constructor, When I inspect it, Then it accepts `PollRepository` and `PollResponseRepository` via dependency injection

### FR-3.8: GetPollResultsUseCase

**Description**: Implement the application use case for retrieving aggregated vote counts per option.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a poll with responses, When `GetPollResultsUseCase.execute(poll_id)` is called, Then the result contains: `poll_id`, `question`, `total_responses` (int), and `options` — a list of `{option_id, text, count, percentage}`
- Given an option with zero votes, When results are retrieved, Then that option appears in the list with `count=0` and `percentage=0.0`
- Given a poll with zero total responses, When results are retrieved, Then all option percentages are `0.0` (no division by zero)
- Given a `poll_id` that does not exist, When `GetPollResultsUseCase.execute()` is called, Then an `EntityNotFoundError` is raised
- Given the use case constructor, When I inspect it, Then it accepts `PollRepository` and `PollResponseRepository` via dependency injection

### FR-3.9: PostgreSQL Repository Implementations

**Description**: Implement `SQLAlchemyPollRepository` and `SQLAlchemyPollResponseRepository` in the infrastructure layer, including the ORM models.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a `PollOrmModel`, When I inspect it, Then it maps to a `polls` table with columns: `id` (UUID PK), `event_id` (UUID FK to `events`), `question` (VARCHAR 500), `poll_type` (VARCHAR 50), `options` (JSONB), `is_active` (BOOLEAN default False), `created_at` (TIMESTAMP WITH TIMEZONE)
- Given a `PollResponseOrmModel`, When I inspect it, Then it maps to a `poll_responses` table with columns: `id` (UUID PK), `poll_id` (UUID FK to `polls`), `option_id` (UUID), `fingerprint_id` (VARCHAR 255), `created_at` (TIMESTAMP WITH TIMEZONE)
- Given the `poll_responses` table, When I inspect its constraints, Then a unique constraint exists on `(poll_id, fingerprint_id)`
- Given `SQLAlchemyPollRepository.create()`, When called with a valid `Poll`, Then a row is inserted and the entity is returned
- Given `SQLAlchemyPollRepository.find_active_by_event(event_id)`, When called, Then it returns the single active poll for that event or `None`
- Given `SQLAlchemyPollResponseRepository.find_by_poll_and_fingerprint()`, When called, Then it returns the matching response or `None`
- Given `SQLAlchemyPollResponseRepository.count_by_option()`, When called, Then it returns the correct count for that option within a poll
- Given the ORM models, When I inspect them, Then they are separate from the domain entities (no domain imports in ORM models)

### FR-3.10: Alembic Migrations

**Description**: Create Alembic migrations for the `polls` and `poll_responses` tables.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given the migration for `polls`, When applied, Then the `polls` table exists with all columns, indexes, and the FK to `events`
- Given the migration for `poll_responses`, When applied, Then the `poll_responses` table exists with all columns, the FK to `polls`, and the unique constraint on `(poll_id, fingerprint_id)`
- Given both migrations, When rolled back, Then both tables are dropped in foreign-key-safe order (`poll_responses` before `polls`)
- Given the existing migration chain, When the new migrations are applied on top, Then `alembic upgrade head` completes without errors

### FR-3.11: Poll REST API Endpoints

**Description**: Create four REST API endpoints for poll management in the presentation layer, with Pydantic request/response schemas.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a valid JSON body with `question` and `options`, When `POST /api/events/{event_id}/polls` is called, Then a `201` response is returned with the created poll shape
- Given an `event_id` that does not exist, When `POST /api/events/{event_id}/polls` is called, Then a `404` response is returned
- Given `{"activate": true}`, When `PATCH /api/polls/{poll_id}/activate` is called, Then a `200` response with the updated poll is returned and any previously active poll in the same event is deactivated
- Given `{"activate": false}`, When `PATCH /api/polls/{poll_id}/activate` is called, Then the poll's `is_active` is set to `False` and a `200` response is returned
- Given a valid `fingerprint_id` and `option_id` for an active poll, When `POST /api/polls/{poll_id}/respond` is called, Then a `201` response is returned
- Given a duplicate submission (same fingerprint and poll), When `POST /api/polls/{poll_id}/respond` is called, Then a `409 Conflict` response is returned
- Given a response attempt to an inactive poll, When `POST /api/polls/{poll_id}/respond` is called, Then a `422` response is returned with an appropriate error message
- Given any poll ID, When `GET /api/polls/{poll_id}/results` is called, Then a `200` response is returned with aggregated vote counts and percentages per option
- Given all four endpoints, When I inspect `/docs`, Then all endpoints are documented with request/response schemas

### FR-3.12: WebSocket Poll Events

**Description**: Extend `ConnectionManager` and `EventPublisher` port to broadcast poll lifecycle and results events to all connected clients.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given a poll is activated, When `ActivatePollUseCase` completes successfully, Then a `poll_activated` WebSocket event is broadcast containing: `type`, `poll_id`, `event_id`, `question`, `options` (list of `{id, text}`)
- Given a poll is deactivated, When `ActivatePollUseCase` sets `is_active=False`, Then a `poll_deactivated` WebSocket event is broadcast containing: `type`, `poll_id`, `event_id`
- Given a new poll response is submitted, When `SubmitPollResponseUseCase` succeeds, Then a `poll_results_updated` WebSocket event is broadcast containing: `type`, `poll_id`, `total_responses`, `options` (list of `{option_id, count, percentage}`)
- Given the `EventPublisher` port, When I inspect it, Then it defines three new abstract methods: `publish_poll_activated`, `publish_poll_deactivated`, `publish_poll_results_updated`
- Given the `ConnectionManager`, When I inspect it, Then it implements all three new `EventPublisher` methods and serialises payloads to JSON via `broadcast()`

### FR-3.13: PollCreationForm Component and ViewModel

**Description**: Implement the `PollCreationForm` React component backed by a `PollCreationViewModel` (MobX). The form allows an organizer to enter a question and dynamically add or remove answer options.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given the `PollCreationForm`, When rendered, Then it displays a question input field and a list of at least 2 option inputs
- Given the form, When the "Add Option" button is clicked and fewer than 10 options exist, Then a new empty option input is appended
- Given the form, When the "Add Option" button is clicked and 10 options already exist, Then the button is disabled and no new input appears
- Given an option row, When the remove button is clicked and more than 2 options exist, Then that option is removed from the list
- Given an option row, When only 2 options remain, Then the remove buttons are disabled
- Given the question field is empty or all whitespace, When I inspect the submit button, Then it is disabled
- Given any option field is empty or all whitespace, When I inspect the submit button, Then it is disabled
- Given a valid question and options, When I click "Create Poll", Then `PollCreationViewModel.submit()` is called with the current form data
- Given the form, When I inspect it, Then it carries the following `id` attributes: `id="poll-creation-form"`, `id="poll-question-input"`, `id="poll-option-input-{index}"`, `id="poll-option-remove-{index}"`, `id="poll-add-option-btn"`, `id="poll-submit-btn"`
- Given `PollCreationViewModel`, When I inspect it, Then it has observable properties: `question` (string), `options` (observable array of `{id, text}`), `isSubmitting` (boolean), `error` (string | null)
- Given `PollCreationViewModel`, When I inspect its actions, Then it has: `setQuestion()`, `addOption()`, `removeOption()`, `setOptionText()`, `submit()`
- Given `PollCreationViewModel`, When I inspect computed properties, Then it has `isValid` (true when question is non-empty and all options are non-empty and count is 2-10) and `canAddOption` (true when option count is below 10)
- Given the React component, When I inspect it, Then it is wrapped with `observer()` and reads state only from the ViewModel

### FR-3.14: PollParticipationView Component and ViewModel

**Description**: Implement the `PollParticipationView` React component backed by a `PollParticipationViewModel` (MobX). The participant sees a question with radio buttons for each option and a submit button.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given an active poll, When `PollParticipationView` renders, Then it displays the poll question and one radio button per option
- Given the participant has not yet voted, When rendered, Then all radio buttons are unselected and the submit button is disabled
- Given the participant selects an option, When rendered, Then the submit button becomes enabled
- Given the submit button is clicked, When `PollParticipationViewModel.submitResponse()` is called, Then a `POST /api/polls/{poll_id}/respond` request is made with `fingerprint_id` and `option_id`
- Given a successful submission, When complete, Then the participation view transitions to a "Your vote has been recorded" state and all inputs are disabled
- Given a duplicate-response `409` from the server, When received, Then an error message "You have already voted in this poll" is displayed
- Given an inactive poll (received via WebSocket `poll_deactivated`), When the event arrives, Then a "This poll has closed" message is displayed
- Given the component, When I inspect it, Then it carries `id` attributes: `id="poll-participation-view"`, `id="poll-option-radio-{option_id}"`, `id="poll-submit-response-btn"`
- Given `PollParticipationViewModel`, When I inspect it, Then it has observable properties: `poll` (Poll entity or null), `selectedOptionId` (string | null), `isSubmitting` (boolean), `hasVoted` (boolean), `error` (string | null)
- Given `PollParticipationViewModel`, When I inspect computed properties, Then it has `canSubmit` (true when `selectedOptionId` is non-null, `!hasVoted`, `!isSubmitting`, and the poll is active)

### FR-3.15: PollResultsDisplay Component and ViewModel

**Description**: Implement the `PollResultsDisplay` React component backed by a `PollResultsViewModel` (MobX). The results view shows a horizontal bar for each option with vote count and percentage, updating in real-time via WebSocket.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given poll results data, When `PollResultsDisplay` renders, Then it shows one horizontal bar per option with the option text, vote count, and percentage
- Given total responses is zero, When rendered, Then all bars show 0% without any rendering error
- Given the leading option (highest vote count), When rendered, Then its bar is visually distinguished (e.g., a different color or bold label)
- Given a `poll_results_updated` WebSocket message arrives, When `PollResultsViewModel` handles it, Then `options` and `totalResponses` update reactively and the component re-renders without a page reload
- Given the component, When I inspect it, Then it carries `id` attributes: `id="poll-results-display"`, `id="poll-results-option-{option_id}"`, `id="poll-results-bar-{option_id}"`
- Given `PollResultsViewModel`, When I inspect it, Then it has observable properties: `pollId` (string), `question` (string), `totalResponses` (number), `options` (observable array of `{optionId, text, count, percentage}`)
- Given `PollResultsViewModel`, When it is instantiated, Then it calls `GET /api/polls/{poll_id}/results` to load initial state
- Given `PollResultsViewModel`, When a `poll_results_updated` WebSocket message is received for the matching `poll_id`, Then it calls `runInAction` to update observable state
- Given `PollResultsViewModel`, When a `poll_deactivated` WebSocket message is received, Then it sets an `isClosed` observable to `true`
- Given the React component, When I inspect it, Then it is wrapped with `observer()` and reads state only from the ViewModel

### FR-3.16: Poll Integration into Event Board View

**Description**: Wire all poll components into the existing event board view so that organizers and participants see polls in context.

**Status**: [ ] TODO

**Acceptance Criteria**:

- Given an authenticated organizer on an event board, When the board renders, Then a "Create Poll" button is visible
- Given the "Create Poll" button is clicked, When rendered, Then the `PollCreationForm` appears (as a modal or inline panel)
- Given a poll exists for the event, When the organizer view renders, Then each poll row shows the poll question, its active/inactive status, an "Activate" / "Deactivate" toggle button, and a "View Results" link
- Given the "Activate" button is clicked, When the `PATCH /api/polls/{poll_id}/activate` call succeeds, Then the poll row updates to active state and the previously active poll (if any) shows as inactive
- Given a poll is active, When a participant loads the event board, Then the `PollParticipationView` is displayed prominently
- Given a participant submits a vote, When the submission succeeds, Then the `PollParticipationView` transitions to a voted state and the `PollResultsDisplay` is shown to the participant
- Given the organizer activates a poll, When the WebSocket `poll_activated` event is received by connected participants, Then the `PollParticipationView` appears automatically without a page reload

## Non-Goals for This Phase

- No rating polls (numeric scale 1-5) — Phase 5
- No open text polls (free-form responses) — Phase 5
- No word cloud polls (visual aggregation of short text) — Phase 6
- No ranking polls (ordered priority selection) — future
- No quiz mode (timed questions with scoring and leaderboard) — future
- No poll editing after creation
- No poll deletion
- No image or GIF attachments on poll options
- No multiple active polls simultaneously within one event
- No survey mode (chained multi-question forms)
- No data export for poll results
- No present mode (separate display window) — separate phase

## Testing Requirements

### Unit Tests — Backend

**Poll entity validation** (`tests/unit/pulse_board/domain/entities/test_poll.py`):

- `TestPollCreate` — question required, question max 500 chars, minimum 2 options, maximum 10 options, option text required, valid creation returns correct defaults (`is_active=False`, new UUID, UTC timestamp)
- `TestPollOptionValueObject` — empty text raises `ValidationError`

**PollResponse entity** (`tests/unit/pulse_board/domain/entities/test_poll_response.py`):

- `TestPollResponseCreate` — `create()` sets `id`, `created_at`; direct constructor skips validation

**CreatePollUseCase** (`tests/unit/pulse_board/application/use_cases/test_create_poll.py`):

- Happy path: valid inputs produce a persisted poll result
- Event not found: `EntityNotFoundError` raised, repository not touched
- Whitespace-only option: `ValidationError` raised, repository not touched
- Repository receives exactly one `create()` call on success

**ActivatePollUseCase** (`tests/unit/pulse_board/application/use_cases/test_activate_poll.py`):

- Activating inactive poll sets `is_active=True`
- Activating a second poll deactivates the first
- Deactivating active poll sets `is_active=False`
- Poll not found raises `EntityNotFoundError`
- `save()` called exactly once on the newly activated poll and once on the deactivated poll

**SubmitPollResponseUseCase** (`tests/unit/pulse_board/application/use_cases/test_submit_poll_response.py`):

- Happy path: active poll, valid option, new fingerprint — creates response
- Duplicate fingerprint raises `DuplicateResponseError`, no record written
- Inactive poll raises `PollNotActiveError`
- Invalid `option_id` (not in poll) raises `ValidationError`
- Poll not found raises `EntityNotFoundError`

**GetPollResultsUseCase** (`tests/unit/pulse_board/application/use_cases/test_get_poll_results.py`):

- Returns correct counts and percentages with votes
- Zero-vote option included with `count=0` and `percentage=0.0`
- Zero total responses — all percentages are `0.0`
- Poll not found raises `EntityNotFoundError`

### Unit Tests — Frontend

**PollCreationViewModel** (`frontend/src/presentation/view-models/__tests__/PollCreationViewModel.test.ts`):

- `isValid` is `false` when question is empty
- `isValid` is `false` when any option text is empty
- `isValid` is `true` when question and all 2+ options are non-empty
- `canAddOption` is `false` at 10 options, `true` at 9
- `addOption()` appends a new empty option entry up to 10
- `removeOption()` removes the correct option by index; no-op when only 2 remain
- `submit()` calls the API port with question and option texts; sets `isSubmitting` during request; clears on success

**PollParticipationViewModel** (`frontend/src/presentation/view-models/__tests__/PollParticipationViewModel.test.ts`):

- `canSubmit` is `false` when `selectedOptionId` is null
- `canSubmit` is `false` after `hasVoted` is `true`
- `submitResponse()` calls the API port; sets `hasVoted=true` on success
- `submitResponse()` sets `error` message on `409` response
- Handling `poll_deactivated` WebSocket message sets `poll.is_active=false`

**PollResultsViewModel** (`frontend/src/presentation/view-models/__tests__/PollResultsViewModel.test.ts`):

- Constructor fetches initial results from API port
- `poll_results_updated` WebSocket message for matching `poll_id` updates `options` and `totalResponses`
- `poll_results_updated` for a different `poll_id` is ignored
- `poll_deactivated` sets `isClosed=true`
- Zero total responses — renders without division-by-zero error

### Integration Tests — Backend

**Poll API endpoints** (`tests/integration/pulse_board/presentation/api/routes/test_polls.py`):

- `POST /api/events/{event_id}/polls` — 201 with valid body; 404 for unknown event; 422 for fewer than 2 options or more than 10 options
- `PATCH /api/polls/{poll_id}/activate` — 200 activates the poll; activating poll B deactivates poll A in same event; 404 for unknown poll
- `POST /api/polls/{poll_id}/respond` — 201 for first response; 409 for duplicate fingerprint; 422 for inactive poll; 422 for invalid `option_id`
- `GET /api/polls/{poll_id}/results` — 200 with correct counts after submissions; zero-vote options appear; 404 for unknown poll

**PollRepository** (`tests/integration/pulse_board/infrastructure/repositories/test_poll_repository.py`):

- `create()` persists and returns the poll
- `get_by_id()` returns the poll or `None`
- `list_by_event()` returns only polls for the specified event
- `find_active_by_event()` returns the active poll or `None`
- `save()` persists `is_active` changes

**PollResponseRepository** (`tests/integration/pulse_board/infrastructure/repositories/test_poll_response_repository.py`):

- `create()` persists the response
- `find_by_poll_and_fingerprint()` returns the existing response or `None`
- `count_by_option()` returns the correct count
- `count_all_by_poll()` returns the total response count
- Duplicate `(poll_id, fingerprint_id)` insert raises a DB-level integrity error

**WebSocket poll events** (`tests/integration/pulse_board/infrastructure/websocket/test_poll_websocket_events.py`):

- `publish_poll_activated` broadcasts a message with `type="poll_activated"` and correct fields
- `publish_poll_deactivated` broadcasts a message with `type="poll_deactivated"` and correct fields
- `publish_poll_results_updated` broadcasts a message with `type="poll_results_updated"` and correct aggregated fields

### E2E Test

**Full poll lifecycle** (`tests/e2e/poll-lifecycle.spec.ts`):

- `beforeEach`: call `resetDatabase()` and create a test event via `api.helper.ts`
- Step 1: Organizer (pageA) creates a multiple choice poll via the `PollCreationForm`; assert the poll appears in the event board poll list
- Step 2: Organizer activates the poll; assert `PollParticipationView` appears on participant view (pageB) without a page reload
- Step 3: Participant (pageB) selects an option and clicks submit; assert the `PollParticipationView` transitions to voted state
- Step 4: A second participant context (pageC or reusing pageA with a different fingerprint) votes for a different option
- Step 5: Assert that `PollResultsDisplay` on both pageA and pageB shows updated counts and percentages in real-time without reload
- Step 6: Organizer deactivates the poll; assert `PollParticipationView` shows "This poll has closed" on participant view

**Element ID selectors used**:

| Selector | Element |
|---|---|
| `#poll-creation-form` | Poll creation form container |
| `#poll-question-input` | Question text input |
| `#poll-option-input-{index}` | Option text input at given index |
| `#poll-add-option-btn` | Add option button |
| `#poll-submit-btn` | Create poll submit button |
| `#poll-participation-view` | Participant voting view |
| `#poll-option-radio-{option_id}` | Radio button for a specific option |
| `#poll-submit-response-btn` | Submit vote button |
| `#poll-results-display` | Results display container |
| `#poll-results-option-{option_id}` | Individual result row |

## Documentation Deliverables

### API Documentation

Inline OpenAPI descriptions MUST be added to all four poll endpoints via FastAPI's `summary`, `description`, and `response_description` parameters:

| Endpoint | Summary |
|---|---|
| `POST /api/events/{event_id}/polls` | Create a multiple choice poll for an event |
| `PATCH /api/polls/{poll_id}/activate` | Activate or deactivate a poll |
| `POST /api/polls/{poll_id}/respond` | Submit a participant's vote |
| `GET /api/polls/{poll_id}/results` | Retrieve aggregated poll results |

Each schema defined in the presentation layer MUST include `description` fields on all Pydantic model fields.

### WebSocket Event Documentation

The WebSocket events introduced in this phase MUST be documented in `docs/websocket-events.md` (create if it does not exist) with the following entries:

**`poll_activated`**
```json
{
  "type": "poll_activated",
  "poll_id": "<uuid>",
  "event_id": "<uuid>",
  "question": "string",
  "options": [{"id": "<uuid>", "text": "string"}]
}
```

**`poll_deactivated`**
```json
{
  "type": "poll_deactivated",
  "poll_id": "<uuid>",
  "event_id": "<uuid>"
}
```

**`poll_results_updated`**
```json
{
  "type": "poll_results_updated",
  "poll_id": "<uuid>",
  "total_responses": 42,
  "options": [
    {"option_id": "<uuid>", "count": 30, "percentage": 71.4}
  ]
}
```

### Docstrings

All new public Python classes, methods, and module-level functions MUST have Google-style docstrings. This includes:

- `Poll`, `PollResponse`, `PollOption` domain classes
- All port ABC methods
- All use case `execute()` methods
- All repository implementation methods
- All FastAPI route functions

### Frontend Component README

Add a `poll/README.md` in `frontend/src/presentation/components/poll/` describing the three components (`PollCreationForm`, `PollParticipationView`, `PollResultsDisplay`), their ViewModels, and the WebSocket message types each ViewModel handles.

## Technical Notes

### Architecture Placement

New files follow the established onion architecture layout:

```
src/pulse_board/
  domain/
    entities/
      poll.py                    # Poll + PollOption entities
      poll_response.py           # PollResponse entity
    ports/
      poll_repository_port.py    # PollRepository ABC
      poll_response_repository_port.py  # PollResponseRepository ABC
  application/
    use_cases/
      create_poll.py
      activate_poll.py
      submit_poll_response.py
      get_poll_results.py
    dtos/
      poll_dtos.py               # CreatePollResult, SubmitPollResponseResult, PollResultsResult
  infrastructure/
    database/
      models/
        poll_model.py            # PollOrmModel, PollResponseOrmModel
    repositories/
      poll_repository.py         # SQLAlchemyPollRepository
      poll_response_repository.py # SQLAlchemyPollResponseRepository
  presentation/
    api/
      routes/
        polls.py                 # FastAPI router for poll endpoints
      schemas/
        poll_schemas.py          # Pydantic request/response schemas

frontend/src/
  domain/
    entities/
      Poll.ts                    # Poll, PollOption types
      PollResponse.ts            # PollResults type (aggregated)
    ports/
      PollApiPort.ts             # Interface for poll HTTP calls
  infrastructure/
    api/
      pollApiClient.ts           # Implements PollApiPort
  presentation/
    view-models/
      PollCreationViewModel.ts
      PollParticipationViewModel.ts
      PollResultsViewModel.ts
    components/
      poll/
        poll-creation-form/
          PollCreationForm.tsx
          PollOptionInput.tsx
          index.ts
        poll-participation-view/
          PollParticipationView.tsx
          PollOptionRadio.tsx
          index.ts
        poll-results-display/
          PollResultsDisplay.tsx
          PollResultsBar.tsx
          index.ts
        README.md
```

### Domain Exception Types

Add the following new exception classes to `src/pulse_board/domain/exceptions.py`:

- `DuplicateResponseError` — raised when a fingerprint submits a second response to the same poll
- `PollNotActiveError` — raised when a response is submitted to an inactive poll

These follow the existing `ValidationError` and `EntityNotFoundError` pattern (plain Python classes with no framework dependency).

### JSONB for Poll Options

`options` is stored as JSONB in PostgreSQL (a list of `{id: uuid, text: string}` objects). This avoids a separate `poll_options` join table for this phase while keeping the data structured. If option-level analytics are needed in a future phase, a migration can extract options to a dedicated table.

### One Active Poll Invariant

The "one active poll per event" invariant is enforced at the application layer by `ActivatePollUseCase`, not at the database level. A database-level partial unique index (`WHERE is_active = TRUE`) MAY be added as a belt-and-suspenders constraint in the same migration; this is optional for this phase but SHOULD be done if the implementation is straightforward.

### WebSocket Message Routing on the Frontend

All three new WebSocket message types (`poll_activated`, `poll_deactivated`, `poll_results_updated`) are dispatched from the existing WebSocket client. The `TopicsViewModel` currently owns the WebSocket message handler. For this phase, a shared WebSocket dispatcher or a per-ViewModel subscription pattern MUST be introduced so that `PollResultsViewModel` and `PollParticipationViewModel` can each subscribe to the messages they need without duplicating WebSocket connections.

The recommended approach is a shared `WebSocketMessageBus` class (infrastructure layer) that fans out messages to registered handlers by message type. Each ViewModel registers itself on instantiation and deregisters on `dispose()`.

### Performance Target

The implementation MUST support 100 concurrent voters casting responses within a 30-second window without degraded WebSocket broadcast latency. The `count_by_option` and `count_all_by_poll` queries MUST use indexed columns to remain fast under load.

### Fingerprint Enforcement vs. IP-Based Rate Limiting

One response per fingerprint per poll is the primary enforcement mechanism, consistent with existing vote enforcement. There is no additional IP-based rate limiting in this phase. `MUST` enforce the unique constraint at both the application layer (`SubmitPollResponseUseCase`) and the database layer (unique index on `poll_responses(poll_id, fingerprint_id)`).

## Validation Checklist

### Before Marking Phase Complete

**Domain layer**:
- [ ] `Poll.create()` raises `ValidationError` for all invalid inputs (empty question, wrong option count, empty option text)
- [ ] `PollResponse.create()` sets UUID and timestamp
- [ ] `PollRepository` and `PollResponseRepository` are ABCs with no infrastructure imports
- [ ] New domain exception classes added to `domain/exceptions.py`

**Application layer**:
- [ ] `CreatePollUseCase` validates event existence before persisting
- [ ] `ActivatePollUseCase` deactivates any currently active poll before activating the new one
- [ ] `SubmitPollResponseUseCase` enforces active poll, valid option, and duplicate fingerprint rules
- [ ] `GetPollResultsUseCase` handles zero-response case without arithmetic errors
- [ ] All use cases accept ports via constructor injection only

**Infrastructure layer**:
- [ ] ORM models are separate from domain entities; no domain imports in ORM models
- [ ] `polls` and `poll_responses` tables exist with correct columns and constraints
- [ ] Unique constraint on `(poll_id, fingerprint_id)` in `poll_responses`
- [ ] `find_active_by_event()` returns `None` when no active poll exists
- [ ] Alembic migrations apply cleanly with `alembic upgrade head` and roll back cleanly with `alembic downgrade`

**Presentation layer**:
- [ ] All four endpoints return the correct HTTP status codes documented in FR-3.11
- [ ] `409` is returned (not `422`) for duplicate poll responses
- [ ] All endpoints appear in `/docs` with schemas
- [ ] `EventPublisher` port extended with three new publish methods
- [ ] `ConnectionManager` implements all three new publish methods

**Frontend**:
- [ ] `PollCreationViewModel.isValid` computed property correctly reflects form state
- [ ] `PollParticipationViewModel.canSubmit` becomes `false` after `hasVoted=true`
- [ ] `PollResultsViewModel` updates reactively on `poll_results_updated` WebSocket events
- [ ] All components are wrapped with `observer()`; no local React state for business logic
- [ ] All required `id` attributes are present on interactive elements

**Testing**:
- [ ] All unit tests pass with `make test-unit`
- [ ] All integration tests pass with `make test-integration`
- [ ] E2E poll lifecycle test passes with `make test-e2e`
- [ ] No test runs longer than 2 seconds in the unit suite
- [ ] No test produces database records, queue messages, or network calls in the unit suite

**Documentation**:
- [ ] All four endpoints have OpenAPI `summary` and `description`
- [ ] `docs/websocket-events.md` created with all three new event payloads documented
- [ ] All new public Python classes and methods have Google-style docstrings
- [ ] `frontend/src/presentation/components/poll/README.md` created
