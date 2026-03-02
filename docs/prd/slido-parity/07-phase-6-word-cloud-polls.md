# Phase 6: Word Cloud Polls

## Overview

Deliver word cloud polls end-to-end: creation, participation, real-time aggregation, and animated visualization. Participants submit 1-3 word responses to a prompt; results render as an animated word cloud where more frequent words appear larger. This is one of Slido's most recognizable features and the most visually distinctive poll type in the slido-parity feature set.

**Slice type**: Vertical slice — one business capability delivered across domain, application, infrastructure, API, and frontend layers.

## Prerequisites

- Phase 5 (Rating and Open Text Polls) MUST be complete.
- The poll domain entity, `CreatePollUseCase`, `SubmitPollResponseUseCase`, and `GetPollResultsUseCase` scaffolding MUST exist.
- The WebSocket infrastructure and `word_cloud_updated` event slot MUST be available.
- Browser fingerprinting infrastructure MUST be in place (one response per fingerprint per poll).

---

## Functional Requirements

### FR-6.1: Word Cloud Poll Type Registration

**Priority**: P0

**Description**: The system MUST recognize `word_cloud` as a valid poll type and enforce its creation rules. A word cloud poll has a question/prompt but no predefined answer options.

**Acceptance Criteria**:

- Given a host submits a `CreatePollUseCase` request with `poll_type = "word_cloud"` and a non-empty question, When the use case executes, Then a poll entity with `poll_type = "word_cloud"` and an empty options list is persisted.
- Given a host submits a request with `poll_type = "word_cloud"` and an empty question, When the use case executes, Then a `ValidationError` is raised and no record is persisted.
- Given a host submits a `CreatePollUseCase` request with `poll_type = "word_cloud"` and any predefined `options` in the payload, When the use case executes, Then a `ValidationError` is raised stating that word cloud polls do not accept predefined options.

**Technical notes**:

- Extend the existing poll type enum or string validation in the domain layer.
- The `options` field on the `Poll` entity MUST be an empty list (or `None`) for `word_cloud` polls.
- No infrastructure changes are required beyond the migration already introduced in Phase 1 of slido-parity (the polls table).

---

### FR-6.2: Word Cloud Response Submission with Validation

**Priority**: P0

**Description**: The system MUST accept 1-3 word text responses from participants and enforce length and word-count constraints before persisting.

**Acceptance Criteria**:

- Given an active word cloud poll, When a participant submits a response of 1 word (e.g., "innovation"), Then the response is accepted and stored in `response_data` as a normalized string.
- Given an active word cloud poll, When a participant submits a response of 3 words (e.g., "real time collaboration"), Then the response is accepted and stored.
- Given an active word cloud poll, When a participant submits a response of 4 or more words (e.g., "this is too long"), Then a `ValidationError` is raised with message "Responses must be 1 to 3 words." and nothing is persisted.
- Given an active word cloud poll, When a participant submits an empty string or whitespace-only string, Then a `ValidationError` is raised with message "Response must not be empty."
- Given an active word cloud poll, When a participant submits a response of more than 30 characters (after trimming), Then a `ValidationError` is raised with message "Response must not exceed 30 characters."
- Given a participant has already submitted a response to this poll, When they attempt to submit again, Then a `DuplicateResponseError` is raised and no record is persisted.

**Technical notes**:

- Word count is determined by splitting the normalized (trimmed, lowercased) string on whitespace.
- The 30-character limit applies after normalization (trim + lowercase), not to the raw input.
- Duplicate detection uses the browser fingerprint stored in `response_data` alongside the text content — matching the existing per-fingerprint enforcement pattern.

---

### FR-6.3: Text Normalization

**Priority**: P0

**Description**: All submitted word cloud responses MUST be normalized before persistence and before frequency aggregation. Normalization ensures that "AI", "Ai", and "ai" are counted as the same word.

**Acceptance Criteria**:

- Given a participant submits " Machine Learning ", When the response is processed, Then the stored value is "machine learning" (trimmed and lowercased).
- Given participants submit "Remote Work", "remote work", "REMOTE WORK", and "  remote work  ", When results are aggregated, Then all four are counted as a single entry with frequency 4.
- Given a participant submits a response with internal multiple spaces (e.g., "real  time"), When the response is processed, Then internal whitespace is collapsed to single spaces, yielding "real time".

**Technical notes**:

- Normalization MUST occur inside the domain layer (a pure function on the `WordCloudResponse` value object or inside the domain service), not in the infrastructure layer.
- Normalization order: strip leading/trailing whitespace, lowercase, collapse internal runs of whitespace to a single space.
- Apply normalization before the word-count and character-length validation checks in FR-6.2 so that validation operates on the canonical form.

---

### FR-6.4: Word Cloud Frequency Aggregation

**Priority**: P0

**Description**: `GetPollResultsUseCase` for a word cloud poll MUST aggregate response text into frequency counts and return the top 50 entries sorted by frequency descending.

**Acceptance Criteria**:

- Given a word cloud poll with 200 responses containing 60 distinct normalized phrases, When `GetPollResultsUseCase` is called, Then the result contains exactly 50 entries.
- Given responses with frequencies: "agile" × 10, "remote work" × 8, "innovation" × 3, When results are returned, Then entries appear in descending frequency order: agile (10), remote work (8), innovation (3).
- Given a word cloud poll with 0 responses, When `GetPollResultsUseCase` is called, Then an empty list is returned (no error).
- Given a word cloud poll with 10 distinct responses and no ties beyond 50 entries, When results are returned, Then all 10 entries are included.

**Technical notes**:

- Aggregation MUST be performed at the database layer (SQL `GROUP BY` + `COUNT` + `ORDER BY count DESC LIMIT 50`) to avoid loading all response rows into Python memory.
- The `GetPollResultsUseCase` return DTO for word cloud polls MUST include `word_frequencies: list[WordFrequencyDTO]` where each entry has `text: str` and `count: int`.
- The use case MUST dispatch to the word cloud aggregation path based on `poll.poll_type`.

---

### FR-6.5: WebSocket `word_cloud_updated` Event

**Priority**: P0

**Description**: When a new word cloud response is submitted, the system MUST broadcast a `word_cloud_updated` WebSocket event containing the updated top-50 frequency list so all connected clients can refresh their visualization without polling.

**Acceptance Criteria**:

- Given a connected client is viewing a word cloud poll, When any participant submits a new response, Then the client receives a WebSocket message with `{"type": "word_cloud_updated", "poll_id": "<id>", "frequencies": [{"text": "...", "count": N}, ...]}` within 200ms of submission.
- Given 100 participants submit responses concurrently within a 1-second window, When all responses are processed, Then all connected clients receive the final `word_cloud_updated` event with correct frequency counts (no corruption, no missed counts).
- Given a client that is not viewing any word cloud poll, When a `word_cloud_updated` event fires for a different poll, Then the client either ignores it or is not sent the event (poll-scoped broadcast).

**Technical notes**:

- Publish the event inside `SubmitPollResponseUseCase` after successful persistence, following the existing `EventPublisher` port pattern (see `FakeEventPublisher` in the test fakes).
- The `word_cloud_updated` payload carries the full top-50 list rather than a delta to simplify client-side reconciliation.
- If concurrent submissions cause a brief read-after-write delay, the subsequent submission's event will carry the corrected aggregate — eventual consistency is acceptable at the 200ms scale.
- Broadcast MUST be scoped to the `poll_id` to avoid sending irrelevant updates to unrelated poll views.

---

### FR-6.6: Word Cloud Poll Creation UI

**Priority**: P0

**Description**: Hosts MUST be able to create a word cloud poll through the frontend. The creation form captures the question/prompt and communicates the 1-3 word response constraint to the host.

**Acceptance Criteria**:

- Given a host is on the poll creation screen, When they select "Word Cloud" as the poll type, Then a `WordCloudPollCreation` component renders with a question/prompt input field and no options-management section.
- Given a host enters a question and submits, When the API call succeeds, Then the new word cloud poll appears in the poll list with type indicator "Word Cloud."
- Given a host leaves the question field empty and submits, When client-side validation runs, Then an inline error message "Question is required." appears and the form is not submitted.
- Given the `WordCloudPollCreation` component, When it renders, Then a helper text note reading "Participants will respond with 1-3 words" is visible.

**Technical notes**:

- The component follows the `WordCloudPollCreation` naming convention and lives under `frontend/src/presentation/components/polls/word-cloud-poll-creation/`.
- State and submit logic live in the `WordCloudPollViewModel` (MobX), not in the component.
- The component MUST have `id="word-cloud-poll-creation-form"` on the form element and `id="word-cloud-question-input"` on the question field.

---

### FR-6.7: Word Cloud Poll Participation UI

**Priority**: P0

**Description**: Participants MUST be able to submit short text responses to an active word cloud poll through a focused input component. The component MUST enforce the word limit visually before submission.

**Acceptance Criteria**:

- Given an active word cloud poll, When a participant views it, Then a `WordCloudPollParticipation` component renders with a single text input and a word counter indicator (e.g., "0 / 3 words").
- Given a participant types "machine learning", When they view the word counter, Then it reads "2 / 3 words."
- Given a participant types a 4-word phrase, When the counter updates, Then the counter displays "4 / 3 words" in a warning color (Tailwind `text-red-500`) and the submit button is disabled.
- Given a participant submits a valid response, When the API call succeeds, Then the input field is cleared, a success toast is shown, and the submit button becomes disabled (preventing duplicate submission).
- Given a participant has already submitted, When they reload the page or revisit the poll, Then the participation component shows a "You've already responded" state and the input is hidden.

**Technical notes**:

- Word count for the visual indicator is computed on the client by splitting on whitespace — this is a UX hint; final validation still occurs on the backend (FR-6.2).
- The input element MUST have `id="word-cloud-response-input"` and the submit button `id="word-cloud-submit-button"`.
- The component lives under `frontend/src/presentation/components/polls/word-cloud-poll-participation/`.

---

### FR-6.8: Word Cloud Visualization Component

**Priority**: P0

**Description**: The system MUST display poll results as an animated word cloud where word size is proportional to frequency, and the visualization updates smoothly as new responses arrive via WebSocket.

**Acceptance Criteria**:

- Given a word cloud poll with responses, When the `WordCloudVisualization` component renders, Then words are displayed at sizes proportional to their frequency (higher frequency = larger font).
- Given the top-50 frequency list, When the visualization renders, Then all entries up to 50 are displayed; entries beyond 50 are not shown.
- Given a `word_cloud_updated` WebSocket event arrives, When the ViewModel applies the new frequency data, Then words smoothly transition to their new sizes and positions (CSS transition or library animation, not an instant jump).
- Given a container with width 600px, When the component renders, Then no words overflow the container boundary.
- Given a container that is resized (e.g., browser window resize), When the resize event fires, Then the word cloud re-layouts to fit the new dimensions within 300ms.
- Given a poll with 0 responses, When the component renders, Then an empty-state message "No responses yet. Be the first!" is displayed instead of an empty canvas.

**Technical notes**:

- Use `d3-cloud` (the `d3-cloud` npm package, also known as `wordcloud2` layout) or `react-wordcloud` (the `react-wordcloud` npm package). Evaluate bundle size and animation capability at implementation time. Document the final selection in the visualization library ADR (see Documentation Deliverables).
- Word sizes MUST be computed using a linear or logarithmic scale mapping `count` to a font-size range of 12px (minimum) to 72px (maximum).
- Apply a consistent color palette using the Tailwind CSS color tokens (e.g., a set of 5-8 distinct hues from the Tailwind palette) assigned round-robin or by hash of the word text to ensure color consistency on re-renders.
- The component MUST accept props: `frequencies: WordFrequency[]`, `width: number`, `height: number`.
- The component lives under `frontend/src/presentation/components/polls/word-cloud-visualization/`.
- The container element MUST have `id="word-cloud-visualization"`.

---

### FR-6.9: Word Cloud Poll Results Component

**Priority**: P0

**Description**: A `WordCloudPollResults` component MUST wrap the visualization with response count metadata so hosts can monitor engagement at a glance.

**Acceptance Criteria**:

- Given a word cloud poll with 47 responses, When the results component renders, Then it displays "47 responses" as a subtitle below the poll question.
- Given results update via WebSocket, When the response count changes from 47 to 48, Then the subtitle updates reactively without page reload.
- Given the results component, When it renders, Then it displays the `WordCloudVisualization` component filling the available width.

**Technical notes**:

- The component lives under `frontend/src/presentation/components/polls/word-cloud-poll-results/`.
- Response count MUST be derived from `sum(frequencies[i].count)` in the ViewModel to stay consistent with the aggregated data returned from the backend.
- The response count element MUST have `id="word-cloud-response-count"`.

---

### FR-6.10: Word Cloud ViewModel (MobX)

**Priority**: P0

**Description**: A `WordCloudViewModel` MUST manage all state for the word cloud poll feature: loading, submission, real-time frequency updates, and animation triggers — keeping all React components purely presentational.

**Acceptance Criteria**:

- Given the ViewModel is constructed with a poll ID, When it initializes, Then it fetches the initial frequency data via `GetPollResultsUseCase` and populates the `frequencies` observable.
- Given a `word_cloud_updated` WebSocket event is received, When the event `poll_id` matches this ViewModel's poll, Then `frequencies` is updated to the new list and `totalResponses` is recomputed.
- Given the `submitResponse(text)` action is called with a valid string, When the API call succeeds, Then `hasSubmitted` is set to `true` and `submittedText` stores the normalized value.
- Given the `submitResponse(text)` action is called and the API returns a validation error, When the error is received, Then `submissionError` is populated with the error message and `hasSubmitted` remains `false`.
- Given the ViewModel is disposed (e.g., component unmounts), When `dispose()` is called, Then the WebSocket event listener is removed and no further state updates occur.

**Technical notes**:

- Follow the existing `TopicsViewModel` pattern: observables declared with MobX `@observable`, actions with `@action`, computed values with `@computed`.
- The ViewModel lives under `frontend/src/presentation/view-models/WordCloudViewModel.ts`.
- `totalResponses: number` is a `@computed` property that sums all `count` values in `frequencies`.
- `wordCountForInput(text: string): number` is a pure helper (not observable) that splits on whitespace and returns the word count for the participation UI counter.

---

### FR-6.11: Present Mode — Word Cloud View

**Priority**: P1

**Description**: Present mode MUST include a large-format word cloud optimized for projection on a large screen or shared display, displaying only the visualization and poll question without participant controls.

**Acceptance Criteria**:

- Given a host activates present mode for a word cloud poll, When the `WordCloudPresentView` renders, Then the poll question is displayed in large text (min 28px) and the word cloud fills at least 80% of the viewport height.
- Given present mode is active, When a `word_cloud_updated` event arrives, Then the visualization updates in real-time without any action from the host.
- Given present mode renders, Then no participation input, submit button, or host-control elements are visible.
- Given present mode renders on a 1920×1080 viewport, When the word cloud renders, Then no words are clipped or overflow the viewport.

**Technical notes**:

- The component lives under `frontend/src/presentation/components/polls/word-cloud-present-view/`.
- Reuse `WordCloudVisualization` with width/height props set to viewport dimensions obtained via a `ResizeObserver` hook.
- The present view container MUST have `id="word-cloud-present-view"`.

---

## Non-Goals for This Phase

- No emoji-only responses (emoji characters count toward the word limit but are not excluded; a full emoji-only "word" is accepted — emoji-specific validation is a future enhancement).
- No word filtering or blocklist (profanity filtering, topic-specific stopwords).
- No custom word cloud color themes or branded palettes (colors use the fixed Tailwind-based palette defined in FR-6.8).
- No multi-submission per participant (strictly one response per fingerprint per poll).
- No sentiment analysis or categorization of word cloud responses.
- No export of word cloud results as an image or file.
- No edit or retraction of a submitted response.
- No host-controlled response moderation before words appear in the cloud.
- No ranking polls, quiz mode, or survey types (separate phases).

---

## Testing Requirements

### Unit Tests — Backend

| Test file | Tests |
|---|---|
| `tests/unit/pulse_board/domain/services/test_word_cloud_normalization.py` | `test_lowercase_applied`, `test_leading_trailing_whitespace_trimmed`, `test_internal_whitespace_collapsed`, `test_all_normalizations_combined` |
| `tests/unit/pulse_board/domain/entities/test_word_cloud_response.py` | `test_valid_one_word_response`, `test_valid_three_word_response`, `test_four_words_raises_validation_error`, `test_empty_string_raises_validation_error`, `test_exceeds_30_chars_raises_validation_error`, `test_normalization_applied_before_word_count` |
| `tests/unit/pulse_board/application/use_cases/test_create_poll_word_cloud.py` | `test_creates_word_cloud_poll_without_options`, `test_rejects_options_for_word_cloud_poll`, `test_rejects_empty_question` |
| `tests/unit/pulse_board/application/use_cases/test_submit_word_cloud_response.py` | `test_persists_normalized_response`, `test_publishes_word_cloud_updated_event`, `test_duplicate_fingerprint_raises_error`, `test_inactive_poll_raises_error` |
| `tests/unit/pulse_board/application/use_cases/test_get_word_cloud_results.py` | `test_returns_top_50_only`, `test_results_sorted_by_frequency_descending`, `test_empty_poll_returns_empty_list`, `test_aggregates_identical_normalized_responses` |

All backend unit tests MUST use `FakePollRepository`, `FakePollResponseRepository`, and `FakeEventPublisher` from `tests/unit/pulse_board/fakes.py`. No database or network access. Each test MUST complete in under 2 seconds.

### Unit Tests — Frontend

| Test file | Tests |
|---|---|
| `frontend/src/presentation/view-models/__tests__/WordCloudViewModel.test.ts` | `initializes with empty frequencies`, `fetches initial results on construction`, `updates frequencies on word_cloud_updated event`, `recomputes totalResponses on frequency update`, `sets hasSubmitted on successful submission`, `sets submissionError on API error`, `ignores word_cloud_updated for different poll_id`, `disposes WebSocket listener on dispose()` |

Use factory functions `makeWordFrequency(overrides?)` and `createMockWordCloudApi()` following the patterns in `test-conventions.md`. Use `flushMicrotasks()` after ViewModel construction for async initialization.

### Integration Tests — Backend

| Test file | Tests |
|---|---|
| `tests/integration/pulse_board/infrastructure/repositories/test_poll_response_repository_word_cloud.py` | `test_aggregate_frequency_counts`, `test_top_50_limit_enforced`, `test_frequency_order_descending`, `test_empty_poll_returns_empty_list` |
| `tests/integration/pulse_board/presentation/api/routes/test_word_cloud_poll_routes.py` | `test_create_word_cloud_poll_endpoint`, `test_submit_word_cloud_response_endpoint`, `test_get_word_cloud_results_endpoint`, `test_submit_duplicate_response_returns_409`, `test_submit_four_word_response_returns_422`, `test_submit_response_over_30_chars_returns_422` |
| `tests/integration/pulse_board/infrastructure/websocket/test_word_cloud_websocket.py` | `test_word_cloud_updated_event_broadcast_on_submission`, `test_event_contains_correct_poll_id`, `test_event_contains_updated_frequencies` |

Integration tests use the `integration_session_factory` fixture and a `cleanup_polls` fixture that deletes in foreign-key order (responses before polls).

### E2E Tests

| Test file | Tests |
|---|---|
| `tests/e2e/word-cloud-poll.spec.ts` | `create word cloud poll and verify it appears in poll list`, `submit response and verify word appears in visualization`, `submit from three separate browser sessions and verify all words visible`, `duplicate submission from same session shows error state`, `word cloud visualization updates in real-time when second session submits` |

E2E tests MUST:
- Call `resetDatabase()` in `beforeEach`.
- Use `api.helper.ts` to create the word cloud poll and seed initial responses where applicable.
- Use `pageA` / `pageB` / `pageC` Playwright contexts for multi-session submission tests.
- Wait for visualization updates using a new `waitForWordCloudWord(page, word)` polling helper added to `wait.helper.ts`.
- Select elements using the `id` convention: `#word-cloud-visualization`, `#word-cloud-response-input`, `#word-cloud-submit-button`, `#word-cloud-response-count`.

### Visual / Snapshot Test

Add a Vitest snapshot test for `WordCloudVisualization` using a fixed frequency dataset (10 entries, deterministic counts) to detect unexpected layout regressions. Store the snapshot in `frontend/src/presentation/components/polls/word-cloud-visualization/__tests__/`.

---

## Documentation Deliverables

1. **API documentation** — The `POST /api/polls/{poll_id}/responses` and `GET /api/polls/{poll_id}/results` FastAPI route docstrings MUST be updated to describe the word cloud poll variant, including the `word_cloud` type tag, `response_data` shape (`{"text": "...", "fingerprint": "..."}`), and the `word_frequencies` result DTO.

2. **ADR: Word Cloud Visualization Library** — Create `docs/adr/006-word-cloud-visualization-library.md` recording the evaluation of `d3-cloud` vs. `react-wordcloud` (bundle size, animation capability, TypeScript support, maintenance status) and the rationale for the chosen library. Use the ADR format established in `docs/adr/001-frontend-technology-stack.md`.

3. **Technical note: Text normalization** — Add a section titled "Word Cloud Text Normalization" to the API docs (or an inline comment block in the domain service) describing the three-step normalization pipeline (trim, lowercase, collapse internal whitespace) and stating that it is applied before validation. This is the authoritative reference for backend and frontend engineers to align their client-side preview logic with server behavior.

4. **README update** — Add `d3-cloud` or `react-wordcloud` (whichever is chosen) to the frontend dependencies section of the top-level `README.md` or `frontend/README.md` if one exists.

---

## Technical Notes

### Onion Architecture Placement

| Artifact | Layer | Location |
|---|---|---|
| `WordCloudResponse` value object | Domain | `src/pulse_board/domain/value_objects/word_cloud_response.py` |
| `normalize_word_cloud_text(text)` pure function | Domain service | `src/pulse_board/domain/services/word_cloud_normalization.py` |
| `WordFrequencyDTO` | Application | `src/pulse_board/application/dtos/word_cloud_dtos.py` |
| `GetWordCloudResultsUseCase` | Application | `src/pulse_board/application/use_cases/get_word_cloud_results.py` |
| SQL aggregation query | Infrastructure | `src/pulse_board/infrastructure/repositories/poll_response_repository.py` |
| `POST /api/polls/{poll_id}/responses` route update | Presentation | `src/pulse_board/presentation/api/routes/polls.py` |
| `WordCloudViewModel` | Frontend presentation | `frontend/src/presentation/view-models/WordCloudViewModel.ts` |

### Performance — 100 Concurrent Response Submissions

The `word_cloud_updated` event payload carries the full recomputed top-50 list. Under high concurrency this means the SQL aggregation query runs once per submission. To avoid a thundering-herd problem at 100 concurrent submissions:

- Debounce WebSocket broadcast: if multiple responses arrive within a 50ms window, emit a single `word_cloud_updated` event with the latest aggregate (not one per submission). Implement this with a short-lived asyncio task that cancels and reschedules on each arrival.
- This is an implementation optimization the agent SHOULD apply; it does not change the observable behavior from the client's perspective.

### Word Frequency Scale

Font size calculation MUST use a linear scale: `font_size = min_size + (count - min_count) / (max_count - min_count) * (max_size - min_size)` where `min_size = 12`, `max_size = 72`. If all words have the same count (e.g., a single response each), render all at `(min_size + max_size) / 2 = 42px`.

### Database Migration

A new Alembic migration is NOT required if `response_data` (JSONB) is already the storage column for `PollResponse`. Word cloud responses use `response_data = {"text": "<normalized>", "fingerprint": "<fp>"}` — the same column used by open text and rating poll responses in Phase 5.

---

## Validation Checklist

- [ ] `FR-6.1`: Word cloud poll type accepted by `CreatePollUseCase`; predefined options rejected
- [ ] `FR-6.2`: 1-3 word constraint enforced in domain; 4+ words, empty, and >30 char responses rejected with correct error messages
- [ ] `FR-6.3`: Normalization (trim, lowercase, collapse whitespace) applied before validation; identical variants aggregate to one entry
- [ ] `FR-6.4`: `GetPollResultsUseCase` returns top 50 frequency entries sorted descending; SQL aggregation used (not in-memory)
- [ ] `FR-6.5`: `word_cloud_updated` WebSocket event fires on each submission and carries the updated top-50 list; broadcast scoped to `poll_id`; 100 concurrent submissions produce correct counts
- [ ] `FR-6.6`: `WordCloudPollCreation` component renders for `word_cloud` type; no options section; helper text visible; correct IDs on form and input
- [ ] `FR-6.7`: `WordCloudPollParticipation` shows live word counter; blocks submit at 4+ words; disables after successful submission; shows "already responded" state on revisit
- [ ] `FR-6.8`: `WordCloudVisualization` sizes words proportionally; updates smoothly on new data; handles empty state; responsive to container resize; no overflow
- [ ] `FR-6.9`: `WordCloudPollResults` shows accurate response count derived from frequency sum; updates reactively
- [ ] `FR-6.10`: `WordCloudViewModel` initializes from API; updates on WebSocket event; sets `hasSubmitted`; handles errors; disposes listener
- [ ] `FR-6.11`: Present mode renders large-format word cloud; updates in real-time; no participant controls visible
- [ ] All backend unit tests pass with no mocks (fakes only), each under 2 seconds
- [ ] All frontend unit tests pass; `WordCloudViewModel` tests cover WebSocket event routing and disposal
- [ ] Integration tests verify SQL aggregation returns correct counts and the 50-entry limit
- [ ] E2E test confirms multi-session submission flow and real-time visualization update
- [ ] Visual snapshot test stored for `WordCloudVisualization`
- [ ] ADR `006-word-cloud-visualization-library.md` created and library choice documented
- [ ] API docstrings updated for word cloud poll type
- [ ] Text normalization documented in domain service
- [ ] `ruff format .` and `uv run ruff check .` pass with zero errors
- [ ] `uv run pyright` passes with zero type errors
- [ ] All tests pass: `make test-all`
