# Phase 5: Rating Polls and Open Text Polls

## Overview

This phase is a **vertical slice** delivering two additional poll types: rating polls and open text polls. Both types build on the poll infrastructure established in Phase 3 (Multiple Choice Polls). After this phase, organizers can create rating polls (1-5 star scale) for numeric feedback and open text polls for free-form text responses. Participants can respond in real time, and results update live via WebSocket.

This phase closes gap items #6 (Rating Polls) and #12 (Open Text Polls) from the Slido feature gap analysis.

## Status

`[ ]` TODO

## Prerequisites

- Phase 3 (Multiple Choice Polls) MUST be complete.
- The `Poll` domain entity, `PollResponse` entity, `CreatePollUseCase`, `ActivatePollUseCase`, `SubmitPollResponseUseCase`, and `GetPollResultsUseCase` MUST exist.
- The `poll_results_updated` WebSocket event infrastructure MUST exist.
- Browser fingerprinting MUST be available for one-response-per-fingerprint enforcement.

---

## Functional Requirements

### FR-5.1: Rating Poll Domain Entity Extension

**Priority**: P0

**Description**: Extend the `Poll` domain entity to support `poll_type = 'rating'`. Rating polls auto-generate five options representing values 1 through 5. No caller-supplied options are accepted for rating polls.

**Acceptance Criteria**:

- Given a `Poll` entity is constructed with `poll_type = 'rating'`, When it is inspected, Then its `options` field contains exactly five entries with values `[1, 2, 3, 4, 5]` regardless of any caller-supplied options.
- Given a `Poll` entity with `poll_type = 'rating'`, When a `PollResponse` is created for it, Then `response_data` MUST be a single integer in the range `[1, 5]`.
- Given a `PollResponse` for a rating poll with `response_data` outside `[1, 5]`, When the entity is validated, Then a domain validation error is raised.
- Given a `Poll` entity file, When imports are inspected, Then there are NO framework imports (no FastAPI, no SQLAlchemy, no Pydantic).

### FR-5.2: Open Text Poll Domain Entity Extension

**Priority**: P0

**Description**: Extend the `Poll` domain entity to support `poll_type = 'open_text'`. Open text polls have no predefined options. Responses store a free-form string capped at 500 characters.

**Acceptance Criteria**:

- Given a `Poll` entity is constructed with `poll_type = 'open_text'`, When it is inspected, Then its `options` field is an empty list.
- Given a `PollResponse` for an open text poll, When `response_data` is set, Then it MUST be a non-empty string of at most 500 characters.
- Given a `PollResponse` for an open text poll with an empty string in `response_data`, When the entity is validated, Then a domain validation error is raised.
- Given a `PollResponse` for an open text poll with `response_data` exceeding 500 characters, When the entity is validated, Then a domain validation error is raised with a message indicating the 500-character limit.
- Given a `Poll` entity file, When imports are inspected, Then there are NO framework imports.

### FR-5.3: CreatePollUseCase Extended for Rating and Open Text

**Priority**: P0

**Description**: Extend `CreatePollUseCase` to accept `poll_type` values of `'rating'` and `'open_text'` in addition to the existing `'multiple_choice'`. Rating polls ignore any caller-supplied options. Open text polls reject any caller-supplied options.

**Acceptance Criteria**:

- Given a request with `poll_type = 'rating'` and no options, When `CreatePollUseCase` executes, Then a rating poll is persisted with auto-generated options `[1, 2, 3, 4, 5]` and a 201 response is returned.
- Given a request with `poll_type = 'rating'` and caller-supplied options, When `CreatePollUseCase` executes, Then the caller-supplied options are silently ignored and the auto-generated `[1, 2, 3, 4, 5]` options are used.
- Given a request with `poll_type = 'open_text'` and no options, When `CreatePollUseCase` executes, Then an open text poll is persisted with an empty options list.
- Given a request with `poll_type = 'open_text'` and caller-supplied options, When `CreatePollUseCase` executes, Then a validation error is raised indicating open text polls do not accept predefined options.
- Given a request with an unrecognized `poll_type`, When `CreatePollUseCase` executes, Then a validation error is raised.

### FR-5.4: GetPollResultsUseCase Extended for Rating Results

**Priority**: P0

**Description**: Extend `GetPollResultsUseCase` to compute and return rating-specific result data: the average rating (rounded to two decimal places) and a distribution map showing the response count for each star value (1 through 5).

**Acceptance Criteria**:

- Given a rating poll with zero responses, When `GetPollResultsUseCase` executes, Then the response contains `{"average_rating": null, "distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}, "total_responses": 0}`.
- Given a rating poll with responses `[5, 4, 5, 3]`, When `GetPollResultsUseCase` executes, Then the response contains `{"average_rating": 4.25, "distribution": {"1": 0, "2": 0, "3": 1, "4": 1, "5": 2}, "total_responses": 4}`.
- Given a rating poll, When the result payload is inspected, Then it does NOT include raw individual response values (only aggregate distribution and average).

### FR-5.5: GetPollResultsUseCase Extended for Open Text Results

**Priority**: P0

**Description**: Extend `GetPollResultsUseCase` to return paginated open text responses, ordered newest first, with a total response count.

**Acceptance Criteria**:

- Given an open text poll with zero responses, When `GetPollResultsUseCase` executes, Then the response contains `{"responses": [], "total_responses": 0, "page": 1, "page_size": 20}`.
- Given an open text poll with 25 responses, When `GetPollResultsUseCase` executes with `page=1, page_size=20`, Then the response contains the 20 most recent responses and `"total_responses": 25`.
- Given an open text poll with 25 responses, When `GetPollResultsUseCase` executes with `page=2, page_size=20`, Then the response contains the remaining 5 responses.
- Given an open text poll, When responses are returned, Then each response object contains `{"id": "...", "text": "...", "submitted_at": "..."}` and does NOT expose the fingerprint ID.

### FR-5.6: SubmitPollResponseUseCase Unchanged — Polymorphic Handling

**Priority**: P0

**Description**: Confirm that the existing `SubmitPollResponseUseCase` works with rating and open text poll types without modification, delegating response-data validation to the domain entity. One response per fingerprint per poll MUST be enforced for both types.

**Acceptance Criteria**:

- Given a rating poll and a valid fingerprint with no prior response, When `SubmitPollResponseUseCase` executes with `response_data = 4`, Then the response is persisted and a success result is returned.
- Given an open text poll and a valid fingerprint with no prior response, When `SubmitPollResponseUseCase` executes with `response_data = "Great session!"`, Then the response is persisted and a success result is returned.
- Given a rating poll and a fingerprint that has already responded, When `SubmitPollResponseUseCase` executes again, Then a conflict error is returned (one response per fingerprint per poll).
- Given an open text poll and a fingerprint that has already responded, When `SubmitPollResponseUseCase` executes again, Then a conflict error is returned.
- Given a rating poll and `response_data = 0` (out of range), When `SubmitPollResponseUseCase` executes, Then a domain validation error is raised and no response is persisted.
- Given an open text poll and `response_data` of 501 characters, When `SubmitPollResponseUseCase` executes, Then a domain validation error is raised and no response is persisted.

### FR-5.7: REST API Endpoints for Rating and Open Text Polls

**Priority**: P0

**Description**: Expose poll creation and results retrieval through the existing poll REST API. No new routes are required; existing routes handle rating and open text via the `poll_type` discriminator. Add query parameters for open text result pagination.

**Acceptance Criteria**:

- Given `POST /api/events/{event_id}/polls` with body `{"question": "How was the session?", "poll_type": "rating"}`, When the request is made, Then a 201 response is returned with the created rating poll.
- Given `POST /api/events/{event_id}/polls` with body `{"question": "Any other thoughts?", "poll_type": "open_text"}`, When the request is made, Then a 201 response is returned with the created open text poll.
- Given `GET /api/events/{event_id}/polls/{poll_id}/results` for a rating poll, When the request is made, Then a 200 response is returned with `average_rating`, `distribution`, and `total_responses`.
- Given `GET /api/events/{event_id}/polls/{poll_id}/results?page=1&page_size=20` for an open text poll, When the request is made, Then a 200 response is returned with paginated responses and `total_responses`.
- Given `GET /api/events/{event_id}/polls/{poll_id}/results` for an open text poll without pagination parameters, When the request is made, Then `page=1` and `page_size=20` defaults are applied.
- Given an invalid `page` or `page_size` (e.g., `page=0`, `page_size=200`), When the request is made, Then a 422 validation error is returned.

### FR-5.8: WebSocket poll_results_updated Event for Rating and Open Text

**Priority**: P0

**Description**: Reuse the existing `poll_results_updated` WebSocket event to broadcast updated results when a rating or open text response is submitted. The payload shape differs by poll type.

**Acceptance Criteria**:

- Given a response is submitted to an active rating poll, When the response is persisted, Then a `poll_results_updated` event is broadcast to all connected clients with payload `{"type": "poll_results_updated", "poll_id": "...", "poll_type": "rating", "average_rating": N, "distribution": {...}, "total_responses": N}`.
- Given a response is submitted to an active open text poll, When the response is persisted, Then a `poll_results_updated` event is broadcast with payload `{"type": "poll_results_updated", "poll_id": "...", "poll_type": "open_text", "latest_response": {"id": "...", "text": "...", "submitted_at": "..."}, "total_responses": N}`.
- Given the open text broadcast payload, When it is inspected, Then it contains only the single latest response (not the full paginated list) to keep the broadcast payload small.
- Given a client receives a `poll_results_updated` event, When the `poll_type` is `'open_text'`, Then the client prepends the `latest_response` to its local response list rather than replacing the full list.

### FR-5.9: PollCreationForm Updated with Poll Type Selector

**Priority**: P0

**Description**: Update the `PollCreationForm` frontend component to include a poll type selector with three options: Multiple Choice, Rating, and Open Text. The form fields shown MUST change based on the selected poll type.

**Acceptance Criteria**:

- Given the `PollCreationForm` is rendered, When displayed, Then a poll type selector is visible with options: "Multiple Choice", "Rating", "Open Text".
- Given the user selects "Multiple Choice", When the form re-renders, Then the options input fields are shown (same as existing behavior).
- Given the user selects "Rating", When the form re-renders, Then the options input fields are hidden and a static label "Participants will rate 1–5 stars" is shown.
- Given the user selects "Open Text", When the form re-renders, Then the options input fields are hidden and no additional configuration is shown.
- Given the user submits the form with type "Rating", When the API call is made, Then the request body contains `"poll_type": "rating"` and no `options` field.
- Given the user submits the form with type "Open Text", When the API call is made, Then the request body contains `"poll_type": "open_text"` and no `options` field.
- Given the form, When I inspect its element IDs, Then they follow the convention: `id="poll-type-selector"`, `id="poll-type-option-multiple-choice"`, `id="poll-type-option-rating"`, `id="poll-type-option-open-text"`, `id="poll-creation-submit"`.

### FR-5.10: RatingPollParticipation Component

**Priority**: P0

**Description**: Create a `RatingPollParticipation` component that renders an interactive 1-5 star selector for rating poll participation. The component MUST display the poll question and a 5-star input. It receives all state and callbacks from its ViewModel.

**Acceptance Criteria**:

- Given an active rating poll, When `RatingPollParticipation` is rendered, Then five star icons are displayed, all in an unselected state by default.
- Given the user hovers over star 3, When hovering, Then stars 1, 2, and 3 are visually highlighted (preview state).
- Given the user clicks star 4, When the click occurs, Then stars 1 through 4 are selected (filled), star 5 is unselected, and the selected rating is stored in the ViewModel.
- Given the user has selected a rating, When the "Submit" button is clicked, Then `submitRating(rating)` is called on the ViewModel.
- Given the poll is inactive or the user has already submitted a response, When the component is rendered, Then all star inputs are disabled and the user's prior rating is shown (if available).
- Given the component, When I inspect its element IDs, Then they follow: `id="rating-poll-question"`, `id={`rating-star-${n}`}` for each star (n = 1 to 5), `id="rating-poll-submit"`.

### FR-5.11: RatingPollResults Component

**Priority**: P0

**Description**: Create a `RatingPollResults` component that displays the average rating with a star visualization and a distribution bar chart showing response counts per star value (1 through 5). All display data comes from the ViewModel.

**Acceptance Criteria**:

- Given a rating poll with `average_rating = 4.25` and `total_responses = 4`, When `RatingPollResults` is rendered, Then the average "4.25 / 5" (or equivalent visual) and "4 responses" are both visible.
- Given the distribution `{"1": 0, "2": 0, "3": 1, "4": 1, "5": 2}`, When the component is rendered, Then five horizontal bars are shown; the bar for "5 stars" is the longest (50%), followed by "4 stars" and "3 stars" (25% each), and "1 star" and "2 stars" have zero-width bars.
- Given a rating poll with zero responses, When the component is rendered, Then "No responses yet" is shown and all bars are at zero width.
- Given the component receives a `poll_results_updated` WebSocket event, When the ViewModel processes it, Then the average and distribution update without a full page reload.
- Given the component, When I inspect its element IDs, Then they follow: `id="rating-results-average"`, `id="rating-results-total"`, `id={`rating-distribution-bar-${n}`}` for each bar.

### FR-5.12: OpenTextPollParticipation Component

**Priority**: P0

**Description**: Create an `OpenTextPollParticipation` component that renders a textarea for submitting a free-form text response. A live character counter MUST be visible. The component receives all state and callbacks from its ViewModel.

**Acceptance Criteria**:

- Given an active open text poll, When `OpenTextPollParticipation` is rendered, Then the poll question and an empty textarea are visible along with a character counter showing "0 / 500".
- Given the user types 120 characters, When the component re-renders, Then the character counter shows "120 / 500".
- Given the user types text that reaches 500 characters, When the 501st character would be entered, Then additional input is prevented and the counter shows "500 / 500".
- Given the user has typed at least 1 character, When the "Submit" button is clicked, Then `submitOpenTextResponse(text)` is called on the ViewModel.
- Given the textarea is empty, When the "Submit" button is rendered, Then it is disabled.
- Given the poll is inactive or the user has already submitted a response, When the component is rendered, Then the textarea is disabled.
- Given the component, When I inspect its element IDs, Then they follow: `id="open-text-poll-question"`, `id="open-text-poll-textarea"`, `id="open-text-poll-char-counter"`, `id="open-text-poll-submit"`.

### FR-5.13: OpenTextPollResults Component

**Priority**: P0

**Description**: Create an `OpenTextPollResults` component that renders a scrolling list of text responses, newest first, with a total response count. The component MUST handle real-time prepending of new responses as they arrive via WebSocket.

**Acceptance Criteria**:

- Given an open text poll with 5 responses, When `OpenTextPollResults` is rendered, Then 5 response items are listed, ordered newest first.
- Given the component is displaying 20 responses and there are 25 total, When the user clicks "Load more" (or scrolls to the bottom), Then the next page of responses is fetched and appended below the current list.
- Given a `poll_results_updated` WebSocket event with a `latest_response`, When the ViewModel processes it, Then the new response is prepended to the top of the list without a full refetch.
- Given the total response count is 0, When the component is rendered, Then "No responses yet" is displayed.
- Given the component, When I inspect its element IDs, Then they follow: `id="open-text-results-count"`, `id="open-text-results-list"`, `id={`open-text-response-${id}`}` for each item, `id="open-text-results-load-more"`.

### FR-5.14: Rating Poll ViewModel

**Priority**: P0

**Description**: Create a `RatingPollViewModel` following the MVVM pattern with MobX. This ViewModel manages the selected rating, submission state, hover preview state, and result data. It MUST consume the `PollApiPort` and the WebSocket message stream.

**Acceptance Criteria**:

- Given `RatingPollViewModel` is instantiated, When inspected, Then it has observable fields: `selectedRating: number | null`, `hoveredRating: number | null`, `isSubmitting: boolean`, `hasSubmitted: boolean`, `results: RatingPollResults | null`.
- Given `setHoveredRating(n)` is called, When the ViewModel updates, Then `hoveredRating` is set to `n` and all computed star-state values reflect the preview.
- Given `selectRating(n)` is called, When the ViewModel updates, Then `selectedRating` is set to `n`.
- Given `submitRating()` is called with a valid `selectedRating`, When the API call succeeds, Then `hasSubmitted` is set to `true` and `isSubmitting` returns to `false`.
- Given a `poll_results_updated` WebSocket message for this poll, When the message is received, Then `results` is updated reactively.
- Given the ViewModel, When inspected for imports, Then it uses MobX `makeObservable`, `observable`, `action`, and `computed` decorators.

### FR-5.15: Open Text Poll ViewModel

**Priority**: P0

**Description**: Create an `OpenTextPollViewModel` following the MVVM pattern with MobX. This ViewModel manages the current input text, character count, submission state, the paginated response list, and real-time response prepending.

**Acceptance Criteria**:

- Given `OpenTextPollViewModel` is instantiated, When inspected, Then it has observable fields: `inputText: string`, `isSubmitting: boolean`, `hasSubmitted: boolean`, `responses: OpenTextResponse[]`, `totalResponses: number`, `currentPage: number`, `isLoadingMore: boolean`.
- Given `computed charCount`, When `inputText` changes, Then `charCount` equals `inputText.length`.
- Given `computed isSubmitDisabled`, When `inputText` is empty or `hasSubmitted` is true, Then `isSubmitDisabled` is `true`.
- Given `setInputText(text)` is called with a string exceeding 500 characters, When the ViewModel processes it, Then `inputText` is truncated to 500 characters.
- Given `submitResponse()` is called, When the API call succeeds, Then `hasSubmitted` is `true`, `inputText` is cleared, and `isSubmitting` is `false`.
- Given `loadMoreResponses()` is called, When the API call succeeds, Then returned responses are appended to `responses` and `currentPage` is incremented.
- Given a `poll_results_updated` WebSocket message for this poll, When the message is received, Then `latest_response` is prepended to `responses` and `totalResponses` is incremented by 1.

---

## Non-Goals for This Phase

- **Custom rating scales** (e.g., 1-10, 1-7, Net Promoter Score) — the scale is fixed at 1-5 stars.
- **Word cloud visualization** for open text responses — that is covered in a later phase.
- **Response editing or deletion** after submission — responses are immutable once submitted.
- **Response moderation or filtering** — all responses are displayed as submitted.
- **Named attribution** on open text responses — all responses remain anonymous.
- **Export of open text responses** to CSV or Excel — that is a separate analytics phase.
- **Database migrations** for new tables — rating and open text responses reuse the existing `poll_responses` table via polymorphic `response_data` (JSONB).
- **Multiple choice poll changes** — existing multiple choice behavior is unchanged.

---

## Testing Requirements

### Unit Tests — Domain

- [ ] `tests/unit/domain/entities/poll_tests.py` — rating poll auto-generates options `[1, 2, 3, 4, 5]`; open text poll has empty options; `PollResponse` with `response_data = 0` raises validation error; `PollResponse` with 501-char text raises validation error; valid rating (1-5) passes; non-empty text up to 500 chars passes.
- [ ] All domain unit tests MUST execute in under 1 second with zero external dependencies and zero side effects.

### Unit Tests — Application

- [ ] `tests/unit/application/use_cases/create_poll_tests.py` — rating poll creation ignores caller options and auto-generates; open text poll creation rejects caller options; unrecognized poll type raises error.
- [ ] `tests/unit/application/use_cases/get_poll_results_tests.py` — rating results with zero responses returns `null` average; rating results with `[5, 4, 5, 3]` returns `average_rating = 4.25` and correct distribution; open text results paginate correctly; open text results order is newest first.
- [ ] `tests/unit/application/use_cases/submit_poll_response_tests.py` — duplicate fingerprint on rating poll raises conflict; duplicate fingerprint on open text poll raises conflict; out-of-range rating raises domain error; over-limit text raises domain error.
- [ ] All application unit tests use mocked ports and MUST execute in under 2 seconds.

### Unit Tests — Frontend ViewModels

- [ ] `frontend/src/application/use-cases/__tests__/RatingPollViewModel.test.ts` — `setHoveredRating` updates hover state; `selectRating` sets selected rating; `submitRating` calls API port and sets `hasSubmitted`; `poll_results_updated` message updates `results`; invalid rating is rejected.
- [ ] `frontend/src/application/use-cases/__tests__/OpenTextPollViewModel.test.ts` — `charCount` computed is correct; `isSubmitDisabled` is true for empty text; `setInputText` truncates at 500 chars; `submitResponse` calls API port and clears input; `loadMoreResponses` appends to list; WebSocket message prepends latest response.

### Integration Tests — Backend

- [ ] `tests/integration/infrastructure/repositories/poll_repository_tests.py` — create and retrieve a rating poll; create and retrieve an open text poll; verify `response_data` is stored as JSONB.
- [ ] `tests/integration/presentation/api/routes/polls_tests.py` — `POST /api/events/{id}/polls` with `poll_type = 'rating'` returns 201; `GET /api/events/{id}/polls/{id}/results` for rating poll returns `average_rating` and `distribution`; `GET` with pagination for open text poll returns correct page; duplicate submission returns 409.

### End-to-End Tests

- [ ] `tests/e2e/rating_poll_lifecycle_test.spec.ts` — organizer creates rating poll; organizer activates it; participant submits a 4-star rating; results page shows updated average; second participant submits 2-star; average and distribution update in real time.
- [ ] `tests/e2e/open_text_poll_lifecycle_test.spec.ts` — organizer creates open text poll; organizer activates it; participant types response (character counter updates); participant submits; response appears in results list; second participant's response prepends in real time.

---

## Documentation Deliverables

- [ ] **API docs**: Update `POST /api/events/{event_id}/polls` to document `poll_type: "rating"` and `poll_type: "open_text"` request bodies with examples.
- [ ] **API docs**: Update `GET /api/events/{event_id}/polls/{poll_id}/results` to document the two response shapes (rating result vs. open text paginated result), including all fields.
- [ ] **API docs**: Document the `page` and `page_size` query parameters and their valid ranges and defaults.
- [ ] **Docstrings**: All new use case methods (`CreatePollUseCase` extensions, `GetPollResultsUseCase` extensions) MUST have docstrings describing parameters, return values, and raised exceptions.
- [ ] **Docstrings**: All new ViewModel public methods and computed properties MUST have JSDoc comments.
- [ ] **WebSocket payload examples**: Add inline code examples in the WebSocket documentation showing the `poll_results_updated` payload shape for both rating and open text poll types.

---

## Technical Notes

### Backend

- The `Poll.poll_type` field is an enum or string discriminator already defined in Phase 3. This phase extends it to accept `'rating'` and `'open_text'` values.
- The `poll_responses` table stores `response_data` as JSONB. For rating polls, `response_data = {"rating": 4}`. For open text polls, `response_data = {"text": "Great session!"}`. No schema migration is required.
- Average rating calculation MUST use a single SQL aggregate query (`AVG`) rather than loading all rows into Python. Distribution counts MUST use a `GROUP BY` query.
- Open text pagination MUST use `OFFSET`/`LIMIT` with `ORDER BY submitted_at DESC`. Page size is capped at 50 to prevent abuse.
- The `SubmitPollResponseUseCase` unique-per-fingerprint constraint is enforced at the database level via the existing `UNIQUE(poll_id, fingerprint_id)` index on `poll_responses`.

### Frontend

- `RatingPollViewModel` and `OpenTextPollViewModel` are distinct classes; they MUST NOT inherit from a common poll ViewModel because their state shapes are too different.
- Star hover preview state (`hoveredRating`) is a separate observable from `selectedRating` so the two do not interfere.
- The open text response list is append-only from the client's perspective: new WebSocket messages prepend to the top and "load more" appends to the bottom. The list MUST NOT be replaced wholesale on each WebSocket event.
- Tailwind CSS utility classes MUST be used for all star and distribution bar styling. No custom CSS files are permitted.
- Character counter color MUST change to a warning color (e.g., `text-amber-500`) when `charCount > 450` and to a danger color (e.g., `text-red-600`) when `charCount >= 490`.

### Architecture

- All new code follows the onion architecture: domain entities contain no framework code, use cases depend on port abstractions, infrastructure implements ports, presentation is thin I/O only.
- `RatingPollViewModel` and `OpenTextPollViewModel` live in `frontend/src/application/use-cases/` (or a `polls/` subfolder thereof).
- New React components live under `frontend/src/presentation/components/polls/` following the existing component folder structure with barrel exports.

---

## Validation Checklist

- [ ] `Poll` entity accepts `poll_type = 'rating'` and auto-generates options `[1, 2, 3, 4, 5]`
- [ ] `Poll` entity accepts `poll_type = 'open_text'` and stores empty options list
- [ ] `PollResponse` validates rating in range 1-5; rejects 0 and 6
- [ ] `PollResponse` validates open text is non-empty and at most 500 characters
- [ ] `CreatePollUseCase` ignores caller options for rating polls
- [ ] `CreatePollUseCase` rejects caller options for open text polls
- [ ] `GetPollResultsUseCase` returns `average_rating` and `distribution` for rating polls using SQL aggregates
- [ ] `GetPollResultsUseCase` returns paginated responses newest-first for open text polls
- [ ] Duplicate fingerprint submission returns 409 for both new poll types
- [ ] `POST /api/events/{id}/polls` with `poll_type = 'rating'` returns 201
- [ ] `POST /api/events/{id}/polls` with `poll_type = 'open_text'` returns 201
- [ ] `GET /api/events/{id}/polls/{id}/results` returns correct payload shape per poll type
- [ ] `poll_results_updated` WebSocket event broadcasts after each rating poll response
- [ ] `poll_results_updated` WebSocket event broadcasts after each open text poll response, carrying `latest_response`
- [ ] `PollCreationForm` shows poll type selector with three options
- [ ] Rating options input is hidden when poll type is "Rating" or "Open Text"
- [ ] `RatingPollParticipation` renders 5 interactive star icons with hover preview
- [ ] `RatingPollParticipation` disables input after submission
- [ ] `RatingPollResults` shows average rating and distribution bars with correct proportions
- [ ] `OpenTextPollParticipation` enforces 500-character limit with live counter
- [ ] Character counter changes color at 450 and 490 characters
- [ ] `OpenTextPollParticipation` disables submit button when textarea is empty
- [ ] `OpenTextPollResults` prepends new responses on WebSocket event
- [ ] `OpenTextPollResults` paginates correctly via "Load more"
- [ ] `RatingPollViewModel` observable fields present and reactive
- [ ] `OpenTextPollViewModel` truncates input at 500 chars; `charCount` and `isSubmitDisabled` computed correctly
- [ ] All new element IDs follow the `{component}-{element}-{identifier}` convention
- [ ] All domain unit tests pass with zero external dependencies
- [ ] All application unit tests pass using mocked ports
- [ ] All backend integration tests pass against a real PostgreSQL instance
- [ ] All ViewModel unit tests pass
- [ ] Rating poll E2E lifecycle test passes end-to-end
- [ ] Open text poll E2E lifecycle test passes end-to-end
- [ ] `uv run ruff format . --check` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run pyright` passes with no type errors
- [ ] `npm run lint` passes with no errors
- [ ] API documentation updated with rating and open text request/response examples
