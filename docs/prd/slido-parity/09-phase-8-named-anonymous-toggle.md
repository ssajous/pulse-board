# Phase 8 -- Named/Anonymous Toggle

> See [`docs/prd/slido-parity/00-config.md`](./00-config.md) for project variables,
> stack constraints, and status.

---

## Phase Context

**Slice type**: Vertical slice
**Depends on**: Phase 2 (Event Management), Phase 7 (Host/Admin Mode)
**Delivers**: Participants can optionally attach a display name when submitting a topic or a
poll response. Anonymous submission remains the default. Organizers see the name (or
"Anonymous") in the host view for all submissions. No accounts, no verification, no
enforcement -- name is cosmetic metadata.

**After this phase a user can**:
1. Toggle "Share my name" when submitting a topic, type a display name, and see their
   name appear on the topic card.
2. Toggle "Share my name" when submitting a poll response, and have that name stored
   alongside the response.
3. Return to the page and find their preferred name pre-filled from localStorage.
4. Leave the toggle off (default) and remain fully anonymous -- identical to pre-phase
   behavior.
5. Open the host view and see the display name (or "Anonymous") next to every topic and
   poll response.

---

## Prerequisites

- [ ] Phase 7 (Host/Admin Mode) completed and all acceptance criteria passing.
- [ ] `Topic` entity has `event_id` (nullable) and `status` fields from Phase 2.
- [ ] `PollResponse` entity exists with `poll_id` and `fingerprint` from Phase 3.
- [ ] Host token validation middleware in place (Phase 7).
- [ ] WebSocket `topic.status_changed` events operational (Phase 7).

---

## Functional Requirements

### Backend

#### FR-8.1 -- `display_name` field on Topic entity

**Priority**: P1 -- MUST
**Description**: The `Topic` domain entity MUST accept an optional `display_name`
attribute (max 50 characters, nullable). The field MUST be persisted to the database.
Existing topics with no `display_name` remain valid; the field defaults to `null`.

**Acceptance Criteria**:

```
Given an existing Topic record with no display_name column in the database
When the Phase 8 migration is applied
Then the topics table has a nullable varchar(50) column named display_name
 And all existing rows have display_name = null
 And no existing topic records are altered in any other way
```

```
Given a valid CreateTopicRequest payload with display_name omitted
When the CreateTopicUseCase executes
Then the Topic is persisted with display_name = null
 And the topic appears in all responses with display_name = null
```

```
Given a valid CreateTopicRequest payload with display_name = "Ada Lovelace"
When the CreateTopicUseCase executes
Then the Topic is persisted with display_name = "Ada Lovelace"
 And GET /api/events/:code/topics returns display_name = "Ada Lovelace" for that topic
```

**Technical notes**:
- `display_name` is validated at the presentation layer (Pydantic schema): max 50 chars,
  strip leading/trailing whitespace, reject strings that are only whitespace.
- The domain entity stores it as `Optional[str]`.
- Alembic migration: `ALTER TABLE topics ADD COLUMN display_name VARCHAR(50) NULL`.

---

#### FR-8.2 -- `display_name` field on PollResponse entity

**Priority**: P1 -- MUST
**Description**: The `PollResponse` domain entity MUST accept an optional `display_name`
attribute (max 50 characters, nullable). The field MUST be persisted. Existing poll
responses are unaffected.

**Acceptance Criteria**:

```
Given an existing PollResponse record with no display_name column
When the Phase 8 migration is applied
Then the poll_responses table has a nullable varchar(50) column named display_name
 And all existing rows have display_name = null
```

```
Given a SubmitPollResponseRequest with display_name = "Grace Hopper"
When SubmitPollResponseUseCase executes
Then the PollResponse is stored with display_name = "Grace Hopper"
 And GET /api/polls/:id/results returns display_name = "Grace Hopper" for that response
```

**Technical notes**:
- Same validation rules as FR-8.1.
- Alembic migration: `ALTER TABLE poll_responses ADD COLUMN display_name VARCHAR(50) NULL`.

---

#### FR-8.3 -- CreateTopicUseCase accepts optional display_name

**Priority**: P1 -- MUST
**Description**: The `CreateTopicUseCase` input DTO MUST include an optional
`display_name` field. The use case MUST pass the value to the repository without
transforming it. Fingerprint deduplication logic MUST NOT be altered.

**Acceptance Criteria**:

```
Given CreateTopicUseCase is called with display_name = "Nikola Tesla"
When the use case completes successfully
Then the returned Topic DTO contains display_name = "Nikola Tesla"
 And the fingerprint field is unchanged
 And vote enforcement continues to operate on fingerprint, not display_name
```

```
Given CreateTopicUseCase is called without display_name
When the use case completes successfully
Then the returned Topic DTO contains display_name = null
```

---

#### FR-8.4 -- SubmitPollResponseUseCase accepts optional display_name

**Priority**: P1 -- MUST
**Description**: The `SubmitPollResponseUseCase` input DTO MUST include an optional
`display_name` field. The use case MUST pass the value through to persistence. The
one-response-per-fingerprint enforcement MUST NOT be altered.

**Acceptance Criteria**:

```
Given SubmitPollResponseUseCase is called with display_name = "Marie Curie"
When the use case completes successfully
Then the stored PollResponse has display_name = "Marie Curie"
 And submitting a second response with the same fingerprint is still rejected (FR-3.x unchanged)
```

---

#### FR-8.5 -- Topic response payload includes display_name

**Priority**: P1 -- MUST
**Description**: All API endpoints that return topic data (list, single, WebSocket
broadcast) MUST include `display_name` in the response payload. The value is `null`
when the participant did not provide a name.

**Acceptance Criteria**:

```
Given two topics: one with display_name = "Alan Turing", one submitted anonymously
When GET /api/events/:code/topics is called
Then the response for the named topic contains display_name = "Alan Turing"
 And the response for the anonymous topic contains display_name = null
```

```
Given a new topic is submitted with display_name = "Tim Berners-Lee"
When the WebSocket broadcast fires for topic.created
Then the broadcast payload contains display_name = "Tim Berners-Lee"
```

---

#### FR-8.6 -- Poll results response payload includes display_name per response

**Priority**: P1 -- MUST
**Description**: The poll results endpoint MUST include `display_name` on each individual
response object (applicable to OPEN_TEXT and RATING response lists where individual
responses are shown). For aggregate results (MULTIPLE_CHOICE, WORD_CLOUD), `display_name`
is irrelevant to counts and MUST NOT be included in aggregate rows.

**Acceptance Criteria**:

```
Given an OPEN_TEXT poll with two responses: one named "Linus Torvalds", one anonymous
When GET /api/polls/:id/results is called
Then the named response object contains display_name = "Linus Torvalds"
 And the anonymous response object contains display_name = null
```

---

### Frontend

#### FR-8.7 -- NameToggle component

**Priority**: P1 -- MUST
**Description**: A `NameToggle` component MUST be rendered below the topic submission
text area and below each poll response input. The component consists of a labelled
toggle switch. When toggled ON, a text input field MUST appear. The text input MUST
accept max 50 characters.

**Acceptance Criteria**:

```
Given the topic submission form is open
When the page renders
Then the NameToggle is visible with label "Share my name" and toggle defaulting to OFF
 And no name input field is visible
```

```
Given the NameToggle toggle is OFF
When the user clicks the toggle
Then the toggle switches to ON
 And a text input with placeholder "Your name (optional)" appears
 And the input is focused automatically
```

```
Given the NameToggle toggle is ON and the user clears the input
When the user submits the form
Then display_name is sent as null (treated the same as anonymous)
```

**Technical notes**:
- Component ID convention: `id="name-toggle-switch"`, `id="name-toggle-input"`.
- The toggle state is local component state managed in the ViewModel; it is reset
  after a successful submission (form clears, but localStorage retains the last name).

---

#### FR-8.8 -- Name persistence in localStorage

**Priority**: P1 -- SHOULD
**Description**: When a participant enters a display name and submits successfully, that
name MUST be saved to `localStorage` under the key `pulse_board_display_name`. On
subsequent page loads, if the key exists, the NameToggle MUST initialize with toggle ON
and the saved name pre-filled.

**Acceptance Criteria**:

```
Given the user submits a topic with display_name = "Vint Cerf"
When the submission succeeds
Then localStorage["pulse_board_display_name"] = "Vint Cerf"
```

```
Given localStorage["pulse_board_display_name"] = "Vint Cerf"
When the participant view loads
Then the NameToggle renders with toggle ON and input pre-filled with "Vint Cerf"
```

```
Given the user toggles the switch OFF and submits anonymously
When the next page load occurs
Then the NameToggle still shows the saved name (toggle ON) because the name was not cleared
```

**Technical notes**:
- Name is only written to localStorage on successful submission, not on every keystroke.
- Clearing the input does not delete the localStorage value; only overwriting with a new
  successful submission updates it.
- This behavior keeps re-entry friction minimal while allowing the participant to submit
  anonymously for one submission without losing their preferred name.

---

#### FR-8.9 -- TopicCard shows display name or "Anonymous"

**Priority**: P1 -- MUST
**Description**: The `TopicCard` component MUST display the author attribution line below
the topic text. When `display_name` is non-null, show the name. When `display_name` is
null, show "Anonymous".

**Acceptance Criteria**:

```
Given a topic with display_name = "Donald Knuth"
When the TopicCard renders
Then the attribution line reads "Donald Knuth"
 And the text is visually distinct from the topic body (e.g., smaller, muted color)
```

```
Given a topic with display_name = null
When the TopicCard renders
Then the attribution line reads "Anonymous"
```

**Technical notes**:
- Attribution text element ID: `id="topic-card-author-{topicId}"`.
- The attribution line MUST NOT be omitted even when anonymous -- it is always rendered.

---

#### FR-8.10 -- Poll response display shows name when present

**Priority**: P1 -- MUST
**Description**: In poll result views where individual responses are listed (OPEN_TEXT and
RATING distribution), each response item MUST show the `display_name` when non-null, or
"Anonymous" when null.

**Acceptance Criteria**:

```
Given an OPEN_TEXT poll result list with a response from "Brendan Eich"
When the results list renders
Then each response item shows the author name
 And the item for "Brendan Eich" reads "Brendan Eich" in the attribution area
 And anonymous responses read "Anonymous"
```

---

#### FR-8.11 -- Host admin view shows names on all submissions

**Priority**: P1 -- MUST
**Description**: The host/admin topic list and poll response lists MUST show the
`display_name` value (or "Anonymous") for every submission. This gives the organizer full
visibility into who submitted what, when names were provided.

**Acceptance Criteria**:

```
Given an event with three topics: two named, one anonymous
When the host opens /events/:code/host
Then the topic list shows the name next to each named topic
 And the anonymous topic shows "Anonymous"
```

```
Given an OPEN_TEXT poll with named and anonymous responses
When the host views poll responses in the admin view
Then each response row shows the display_name or "Anonymous"
```

---

## Non-Goals for This Phase

- **No user accounts or profile pages** -- display name is per-submission metadata only.
- **No name verification or uniqueness enforcement** -- any string up to 50 chars is
  accepted without validation beyond length and whitespace.
- **No organizer ability to require names** -- the toggle is always optional for
  participants; there is no event-level "require name" setting.
- **No retroactive name editing** -- once submitted, a display name cannot be changed.
- **No name display in word cloud aggregation** -- word cloud results are aggregate
  frequency data; individual attribution is not shown.
- **No name display in multiple-choice aggregate counts** -- aggregate bar/chart views
  do not attribute individual votes.
- **No moderation or filtering of display names** -- content moderation is out of scope
  for this PRD.

---

## Testing Requirements

### Unit Tests

| ID | Target | Scenario |
|----|--------|----------|
| UT-8.1 | `Topic` entity | Construct with `display_name = "Ada Lovelace"` -- field stored correctly |
| UT-8.2 | `Topic` entity | Construct with `display_name = None` -- field is null |
| UT-8.3 | `Topic` entity | `display_name` exceeding 50 chars raises `ValueError` at domain validation |
| UT-8.4 | `PollResponse` entity | Construct with `display_name = "Grace Hopper"` -- field stored correctly |
| UT-8.5 | `PollResponse` entity | Construct with `display_name = None` -- field is null |
| UT-8.6 | `CreateTopicUseCase` | Pass `display_name` through to repository DTO unchanged |
| UT-8.7 | `CreateTopicUseCase` | Omit `display_name` -- repository receives `None` |
| UT-8.8 | `SubmitPollResponseUseCase` | Pass `display_name` through to repository unchanged |
| UT-8.9 | `SubmitPollResponseUseCase` | Fingerprint dedup still rejects second submission from same fingerprint |
| UT-8.10 | Pydantic `CreateTopicRequest` | Whitespace-only name rejected (validation error) |
| UT-8.11 | Pydantic `CreateTopicRequest` | Name stripped of leading/trailing whitespace |
| UT-8.12 | Pydantic `CreateTopicRequest` | Name of exactly 50 chars accepted |
| UT-8.13 | Pydantic `CreateTopicRequest` | Name of 51 chars rejected |
| UT-8.14 | `NameToggleViewModel` | Toggle defaults to OFF when no localStorage value present |
| UT-8.15 | `NameToggleViewModel` | Toggle initializes ON with saved name when localStorage has value |
| UT-8.16 | `NameToggleViewModel` | `displayName` computed value is null when toggle is OFF |
| UT-8.17 | `NameToggleViewModel` | `displayName` computed value is null when toggle is ON but input is empty |
| UT-8.18 | `NameToggleViewModel` | `persistName()` writes to localStorage only on successful submission |

### Integration Tests

| ID | Target | Scenario |
|----|--------|----------|
| IT-8.1 | `POST /api/events/:code/topics` | Submit topic with `display_name` -- verify persisted and returned |
| IT-8.2 | `POST /api/events/:code/topics` | Submit topic without `display_name` -- verify `null` returned |
| IT-8.3 | `GET /api/events/:code/topics` | Returns `display_name` field on all topics |
| IT-8.4 | `POST /api/polls/:id/responses` | Submit response with `display_name` -- verify persisted |
| IT-8.5 | `GET /api/polls/:id/results` | OPEN_TEXT results include `display_name` per response |
| IT-8.6 | `GET /api/polls/:id/results` | MULTIPLE_CHOICE aggregate counts do NOT include `display_name` |
| IT-8.7 | WebSocket broadcast | `topic.created` event payload contains `display_name` |
| IT-8.8 | Database migration | Phase 8 migration runs cleanly on a database populated by Phase 7 data |

### End-to-End Tests

| ID | Scenario |
|----|----------|
| E2E-8.1 | Participant opens topic form -- NameToggle visible with toggle OFF, no input shown |
| E2E-8.2 | Participant toggles ON -- name input appears and receives focus |
| E2E-8.3 | Participant enters "Richard Stallman", submits topic -- TopicCard shows "Richard Stallman" |
| E2E-8.4 | Participant reloads page -- NameToggle pre-fills "Richard Stallman" from localStorage |
| E2E-8.5 | Participant submits another topic with toggle OFF -- TopicCard shows "Anonymous" |
| E2E-8.6 | Host opens admin view -- sees "Richard Stallman" and "Anonymous" attributed correctly |
| E2E-8.7 | Participant enters 51-character name -- form shows validation error, submission blocked |
| E2E-8.8 | Participant submits poll response with name -- host admin view shows name on that response |

---

## Documentation Deliverables

| ID | Deliverable | Description |
|----|-------------|-------------|
| DOC-8.1 | OpenAPI schema update | `display_name` field documented as `string | null, maxLength: 50` on `CreateTopicRequest`, `TopicResponse`, `CreatePollResponseRequest`, `PollResponseItem` schemas |
| DOC-8.2 | Docstrings | All new/modified domain entities, use case input DTOs, and repository methods get updated docstrings describing `display_name` semantics |
| DOC-8.3 | Component docblock | `NameToggle` component file includes a JSDoc block describing props, localStorage key, and behavior when toggle is off |
| DOC-8.4 | CLAUDE.md note | No changes required; existing conventions cover the addition |

---

## Technical Notes

### Architecture placement

- `display_name` lives on the domain entity as `Optional[str]`.
- Validation (max 50 chars, strip whitespace, reject blank) MUST happen in the Pydantic
  schema at the presentation layer, not in the domain entity -- the domain trusts that
  validated data arrives from the application layer.
- The Alembic migration for Phase 8 produces two `ALTER TABLE` statements (topics and
  poll_responses). These MUST be reversible (downgrade drops the columns).

### Fingerprint independence

The `display_name` field has no interaction with the FingerprintJS fingerprint. The
fingerprint continues to be the identity used for deduplication. Two submissions from the
same fingerprint can have different `display_name` values; this is expected and not
flagged as a conflict.

### WebSocket broadcast

The `topic.created` and `topic.updated` WebSocket message schemas already forward the
full topic DTO. Adding `display_name` to the DTO is sufficient to propagate the name in
real-time without new message types.

### localStorage key

Use `pulse_board_display_name` as the key. This key MUST be namespaced to avoid
collisions if Pulse Board is hosted alongside other apps on the same origin.

### NameToggle ViewModel (MobX)

```
NameToggleViewModel {
  @observable isEnabled: boolean       // toggle state
  @observable inputValue: string       // controlled input
  @computed get displayName(): string | null
    // null if !isEnabled || inputValue.trim() === ''
    // inputValue.trim() otherwise
  persistName(name: string): void      // writes to localStorage
  loadSavedName(): void                // reads from localStorage on init
}
```

The ViewModel is instantiated once per form (topic form, poll response form) and
disposed when the form unmounts.

---

## Validation Checklist

Before marking Phase 8 complete, verify every item:

- [ ] Alembic migration adds `display_name VARCHAR(50) NULL` to both `topics` and
      `poll_responses`; migration is reversible
- [ ] `Topic` domain entity has `display_name: Optional[str]` with max-50 enforcement
- [ ] `PollResponse` domain entity has `display_name: Optional[str]` with max-50
      enforcement
- [ ] `CreateTopicUseCase` input DTO includes `display_name: Optional[str]`
- [ ] `SubmitPollResponseUseCase` input DTO includes `display_name: Optional[str]`
- [ ] Pydantic schemas validate max length and strip whitespace
- [ ] All `TopicResponse` payloads include `display_name` field
- [ ] `PollResponseItem` payloads for OPEN_TEXT and RATING include `display_name`
- [ ] MULTIPLE_CHOICE and WORD_CLOUD aggregate results do NOT expose per-response names
- [ ] WebSocket `topic.created` broadcast includes `display_name`
- [ ] `NameToggle` component renders correctly with toggle OFF (default)
- [ ] `NameToggle` toggles ON and shows focused input
- [ ] Name input enforces 50-character max in the UI
- [ ] Successful submission writes name to localStorage
- [ ] Page reload pre-fills name from localStorage
- [ ] `TopicCard` shows display name or "Anonymous" in attribution line
- [ ] Host admin topic list shows name or "Anonymous" per topic
- [ ] Host admin poll response list shows name or "Anonymous" per response (OPEN_TEXT)
- [ ] All unit tests pass (UT-8.1 through UT-8.18)
- [ ] All integration tests pass (IT-8.1 through IT-8.8)
- [ ] All E2E tests pass (E2E-8.1 through E2E-8.8)
- [ ] OpenAPI docs updated with `display_name` field on all affected schemas
- [ ] Ruff lint and format checks pass
- [ ] Pyright type checks pass with no new errors
- [ ] All existing Phase 1-7 E2E tests continue to pass (NFR-8 regression guard)
- [ ] NFR-1: API p95 response time for topic list endpoint unchanged (< 200ms)
