# Phase 7 -- Host/Admin Mode

> See [`docs/prd/slido-parity/00-config.md`](./00-config.md) for project variables,
> stack constraints, and status.
>
> Slice type: **Vertical slice**
> Prerequisites: Phase 4 (Present Mode) completed, Phase 6 (Word Cloud Polls) completed

---

## Context

This phase delivers a dedicated management interface for event organizers and a
first-class question status system for participants. Before this phase, Pulse Board has
no separation between the organizer experience and the participant experience: anyone who
knows the event code can see and interact with everything on the same view.

After this phase:

- The event creator holds a `host_token` (issued at event creation in Phase 2 and stored
  in `localStorage`) that unlocks a protected admin route at `/events/:code/host`.
- The host dashboard shows all polls, all topics (including archived ones hidden from
  participants), participant count, and lifecycle controls.
- The host can mark any topic as `ANSWERED`, `HIGHLIGHTED`, or `ARCHIVED`. Status changes
  propagate in real-time via WebSocket to all connected participants.
- The participant view gains status badges (answered, highlighted) and sorts highlighted
  topics to the top, above score-sorted entries. Archived topics are hidden from the
  participant view.
- The host can close the event, preventing new topic submissions and poll responses.

This phase covers gap analysis items **#8 (Host/admin mode)** and
**#10 (Question status tracking)** from `docs/feature-gap-slido.md`.

---

## Prerequisites

The following phases MUST be complete before implementing this phase:

| Phase | Deliverable Required |
|-------|----------------------|
| Phase 1 | DB migrations for `events`, `polls`, `poll_responses`; `event_id` + `status` columns on `topics`; base domain entities and port interfaces |
| Phase 2 | Event creation with `host_token` issuance; event join flow; scoped topic board |
| Phase 3 | Poll creation, activation, WebSocket broadcast infrastructure |
| Phase 4 | Present mode route and QR code |
| Phase 6 | Word cloud poll type (completes poll type set used in host poll manager) |

The `host_token` field on the `Event` entity MUST already exist in the database as
established in Phase 2. If Phase 2 stored it in the domain entity but did not expose it
in the creation response payload, that response MUST be updated as part of this phase's
backend work.

---

## Functional Requirements

### FR-7.1 -- Host Token Validation Middleware

**Priority**: P0
**Status**: [ ] TODO

The backend MUST validate the `X-Host-Token` request header on all host-only endpoints.
A missing or incorrect token MUST return `403 Forbidden`. The token MUST be compared
against the `host_token` stored on the `Event` record for the target event. Comparison
MUST be constant-time to prevent timing attacks.

**Acceptance Criteria**

```
Given a request to a host-only endpoint with no X-Host-Token header
When the endpoint handler is invoked
Then the response status is 403
And the response body contains {"detail": "Forbidden"}

Given a request to a host-only endpoint with an incorrect X-Host-Token value
When the endpoint handler is invoked
Then the response status is 403
And the response body contains {"detail": "Forbidden"}

Given a request to a host-only endpoint with the correct X-Host-Token for the event
When the endpoint handler is invoked
Then the request proceeds to the handler and returns the expected response

Given a correct host token for event A used on an endpoint for event B
When the endpoint handler is invoked
Then the response status is 403
```

---

### FR-7.2 -- Topic Status Domain Model

**Priority**: P0
**Status**: [ ] TODO

The `Topic` domain entity MUST include a `status` field typed as the enum
`TopicStatus` with values `ACTIVE`, `ANSWERED`, `HIGHLIGHTED`, `ARCHIVED`. The default
value MUST be `ACTIVE`. This field MUST be persisted in the `topics` table. If Phase 1
migrations created a `status` column with only `OPEN` / `ANSWERED` / `ARCHIVED`, a
follow-up Alembic migration MUST add `HIGHLIGHTED` and rename `OPEN` to `ACTIVE` with a
safe default migration preserving existing rows.

**Acceptance Criteria**

```
Given an existing topic with no status set
When the topic is loaded from the database
Then topic.status equals ACTIVE

Given a topic in the database with status OPEN (legacy value)
When the migration runs
Then topic.status equals ACTIVE after migration

Given the TopicStatus enum
When any value other than ACTIVE, ANSWERED, HIGHLIGHTED, or ARCHIVED is provided
Then a validation error is raised before the record is persisted
```

---

### FR-7.3 -- UpdateTopicStatusUseCase

**Priority**: P0
**Status**: [ ] TODO

The application layer MUST expose `UpdateTopicStatusUseCase` which accepts
`(topic_id: UUID, new_status: TopicStatus, event_id: UUID)` and returns the updated
`Topic`. The use case MUST verify the topic belongs to the specified event before
updating. After persisting the change, the use case MUST publish a
`topic.status_changed` domain event for the WebSocket broadcaster to pick up.

**Acceptance Criteria**

```
Given a topic that belongs to event A
When UpdateTopicStatusUseCase is called with topic_id, new_status=ANSWERED, event_id=A
Then the topic's status is updated to ANSWERED in the repository
And a topic.status_changed event is published with topic_id, new_status, and event_id

Given a topic that belongs to event A
When UpdateTopicStatusUseCase is called with event_id=B (wrong event)
Then a TopicNotFoundError is raised
And no status change is persisted
And no WebSocket event is published

Given a topic_id that does not exist
When UpdateTopicStatusUseCase is called
Then a TopicNotFoundError is raised
```

---

### FR-7.4 -- PATCH /api/topics/{topic_id}/status Endpoint

**Priority**: P0
**Status**: [ ] TODO

A new host-only endpoint MUST be implemented:

```
PATCH /api/topics/{topic_id}/status
Header: X-Host-Token: <token>
Body:   {"status": "answered" | "highlighted" | "archived" | "active"}
```

The endpoint MUST resolve the event from the topic, then validate the host token against
that event. On success it MUST return the updated topic representation with HTTP 200. The
endpoint MUST be registered under the existing topics router and tagged `topics` in
OpenAPI.

**Acceptance Criteria**

```
Given a valid host token and a topic_id belonging to that host's event
When PATCH /api/topics/{topic_id}/status is called with body {"status": "answered"}
Then HTTP 200 is returned
And the response body contains the topic with status "answered"
And a WebSocket topic.status_changed message is broadcast to all event subscribers

Given a valid host token
When PATCH is called with an invalid status value (e.g., {"status": "deleted"})
Then HTTP 422 is returned with a validation error

Given no X-Host-Token header
When PATCH /api/topics/{topic_id}/status is called
Then HTTP 403 is returned
```

---

### FR-7.5 -- GetEventStatsUseCase and GET /api/events/{event_id}/stats Endpoint

**Priority**: P0
**Status**: [ ] TODO

The application layer MUST expose `GetEventStatsUseCase` returning a stats DTO:

```python
@dataclass
class EventStatsDTO:
    participant_count: int   # distinct fingerprints that submitted or voted
    topic_count: int         # total topics in the event (all statuses)
    active_topic_count: int  # topics with status ACTIVE
    poll_count: int          # total polls (all states)
    active_poll: PollSummaryDTO | None  # currently active poll if any
    vote_count: int          # total votes cast across all topics in the event
```

A host-only endpoint MUST expose this:

```
GET /api/events/{event_id}/stats
Header: X-Host-Token: <token>
```

Returns HTTP 200 with the stats DTO. `participant_count` is computed from the union of
distinct fingerprints across `topics` + `poll_responses` for the event.

**Acceptance Criteria**

```
Given an event with 5 unique fingerprints across topics and poll responses
When GET /api/events/{event_id}/stats is called with a valid host token
Then HTTP 200 is returned
And response.participant_count equals 5

Given an event with 3 polls (1 active, 2 inactive) and 12 topics (10 ACTIVE, 2 ARCHIVED)
When the stats endpoint is called
Then poll_count equals 3
And active_topic_count equals 10
And active_poll contains the definition of the currently active poll

Given an event with no active poll
When the stats endpoint is called
Then active_poll is null

Given a request with no X-Host-Token
When GET /api/events/{event_id}/stats is called
Then HTTP 403 is returned
```

---

### FR-7.6 -- CloseEventUseCase and PATCH /api/events/{event_id}/close Endpoint

**Priority**: P0
**Status**: [ ] TODO

The application layer MUST expose `CloseEventUseCase` which transitions the event status
from `ACTIVE` to `CLOSED`. Once closed:
- `CreateTopicUseCase` MUST reject new topic submissions for the event with a 409 error.
- `SubmitPollResponseUseCase` MUST reject new poll responses for the event with a 409 error.
- A `event.closed` WebSocket message MUST be broadcast to all subscribers.

A host-only endpoint MUST expose this:

```
PATCH /api/events/{event_id}/close
Header: X-Host-Token: <token>
```

Returns HTTP 200 with the updated event representation. Calling close on an already-closed
event MUST be idempotent (return 200, no error).

**Acceptance Criteria**

```
Given an ACTIVE event
When PATCH /api/events/{event_id}/close is called with a valid host token
Then HTTP 200 is returned
And event.status equals "closed" in the response
And a WebSocket event.closed message is broadcast to all subscribers

Given a CLOSED event
When PATCH /api/events/{event_id}/close is called again
Then HTTP 200 is returned (idempotent)
And no duplicate WebSocket event is broadcast

Given a CLOSED event
When a participant attempts to submit a new topic to that event
Then HTTP 409 is returned with {"detail": "Event is closed"}

Given a CLOSED event
When a participant attempts to submit a poll response
Then HTTP 409 is returned with {"detail": "Event is closed"}

Given a request with no X-Host-Token
When PATCH /api/events/{event_id}/close is called
Then HTTP 403 is returned
```

---

### FR-7.7 -- WebSocket: topic_status_changed and event_closed Messages

**Priority**: P0
**Status**: [ ] TODO

The WebSocket broadcaster MUST handle two new outbound message types and broadcast them
to all clients subscribed to the relevant event channel.

`topic.status_changed` payload:
```json
{
  "type": "topic.status_changed",
  "topic_id": "<uuid>",
  "status": "answered" | "highlighted" | "archived" | "active",
  "event_id": "<uuid>"
}
```

`event.closed` payload:
```json
{
  "type": "event.closed",
  "event_id": "<uuid>"
}
```

Both message types MUST be broadcast within 500 ms of the triggering action (per NFR-2).

**Acceptance Criteria**

```
Given a topic status change persisted by UpdateTopicStatusUseCase
When the WebSocket broadcaster processes the domain event
Then all clients subscribed to the event channel receive a topic.status_changed message
And the message payload contains the correct topic_id, new status, and event_id

Given CloseEventUseCase completing successfully
When the WebSocket broadcaster processes the event.closed domain event
Then all clients subscribed to the event channel receive an event.closed message
And the message payload contains the event_id

Given a WebSocket client that connects after a topic status change
When the client fetches the topic list
Then the topic status is already reflected in the initial payload (status is persisted, not ephemeral)
```

---

### FR-7.8 -- HostDashboardViewModel (MobX)

**Priority**: P0
**Status**: [ ] TODO

A MobX ViewModel MUST be created at
`frontend/src/presentation/pages/host-dashboard/HostDashboardViewModel.ts` with the
following observable state and actions:

**Observable state:**
- `topics: Topic[]` -- all topics for the event (all statuses)
- `polls: Poll[]` -- all polls (all states)
- `stats: EventStatsDTO | null`
- `isLoading: boolean`
- `isClosed: boolean`
- `error: string | null`

**Computed properties:**
- `activeTopics: Topic[]` -- topics with status ACTIVE, sorted by score DESC then createdAt DESC
- `highlightedTopics: Topic[]` -- topics with status HIGHLIGHTED (appear above activeTopics in UI)
- `answeredTopics: Topic[]` -- topics with status ANSWERED
- `archivedTopics: Topic[]` -- topics with status ARCHIVED
- `activePoll: Poll | null` -- the currently active poll if any

**Actions:**
- `loadDashboard(eventCode: string, hostToken: string): Promise<void>`
- `updateTopicStatus(topicId: string, newStatus: TopicStatus): Promise<void>`
- `closeEvent(): Promise<void>`
- `handleWebSocketMessage(message: WebSocketMessage): void`

The ViewModel MUST store the `hostToken` internally and attach it as the
`X-Host-Token` header on all requests that require it.

**Acceptance Criteria**

```
Given the HostDashboardViewModel is initialized
When loadDashboard is called with a valid event code and host token
Then topics, polls, and stats are populated from the API
And isLoading transitions from true to false on completion

Given a topic is present in topics[]
When updateTopicStatus is called for that topic with status ANSWERED
Then topics[] optimistically updates the topic's status to ANSWERED before the API response
And if the API call fails, the topic's status reverts to its previous value

Given a topic.status_changed WebSocket message arrives
When handleWebSocketMessage processes it
Then the matching topic in topics[] has its status updated reactively

Given an event.closed WebSocket message arrives
When handleWebSocketMessage processes it
Then isClosed is set to true

Given highlightedTopics and activeTopics are both populated
Then the computed activeTopics list does not include highlighted topics
```

---

### FR-7.9 -- HostDashboard Page and Route

**Priority**: P0
**Status**: [ ] TODO

A protected React page MUST be created at
`frontend/src/presentation/pages/host-dashboard/HostDashboard.tsx` and registered at
the route `/events/:code/host`. On mount, the page MUST read the `host_token` from
`localStorage` (key: `host_token_{eventCode}`). If no token is found, the page MUST
redirect to `/events/:code` with a visible error toast ("Host access required"). If a
token is found, the ViewModel's `loadDashboard` MUST be called.

The page layout MUST include the following sub-components (each in its own file within
the `host-dashboard/` folder):

| Component | Responsibility |
|-----------|---------------|
| `HostEventStats` | Real-time participant count, topic count, vote count, active poll summary |
| `HostTopicList` | All topics with status badges and action buttons per topic |
| `HostPollManager` | Poll list with activate/deactivate controls and result summaries |
| `HostEventControls` | Close event button, copy join code button, open present mode link |

**Acceptance Criteria**

```
Given a user navigates to /events/:code/host with no host_token in localStorage
When the page mounts
Then the user is redirected to /events/:code
And an error toast "Host access required" is displayed

Given a user navigates to /events/:code/host with a valid host_token in localStorage
When the page mounts
Then HostDashboardViewModel.loadDashboard is called
And all four sub-components render with data from the ViewModel

Given the ViewModel's isClosed is true
When the HostEventControls component renders
Then the Close Event button is disabled and labelled "Event Closed"
```

---

### FR-7.10 -- HostTopicList Component

**Priority**: P0
**Status**: [ ] TODO

`HostTopicList` MUST render all topics from `HostDashboardViewModel.topics` grouped into
four sections: Highlighted, Active, Answered, Archived. Each topic row MUST include:
- Topic text and score
- Status badge (colour-coded: highlighted = yellow, answered = green, archived = grey)
- Action buttons: "Mark Answered", "Highlight", "Archive", "Restore to Active"
  (only actions that change the status should be shown; the current status action is omitted)

All status transitions MUST call `HostDashboardViewModel.updateTopicStatus`.
Archived topics MUST be visually de-emphasised (opacity-50 or similar) but remain visible
to the host in the Archived section.

**Acceptance Criteria**

```
Given a topic with status ACTIVE
When HostTopicList renders that topic
Then three action buttons appear: "Mark Answered", "Highlight", "Archive"
And no "Restore to Active" button appears

Given a topic with status HIGHLIGHTED
When HostTopicList renders that topic
Then the topic appears in the Highlighted section at the top of the list
And action buttons include "Mark Answered", "Archive", "Restore to Active"
And no "Highlight" button appears

Given a topic with status ARCHIVED
When HostTopicList renders that topic
Then the topic appears in the Archived section
And the row is visually de-emphasised
And the only available action button is "Restore to Active"

Given updateTopicStatus is called
When the optimistic update runs in the ViewModel
Then the topic row moves to the appropriate section immediately without a loading delay
```

---

### FR-7.11 -- HostPollManager Component

**Priority**: P0
**Status**: [ ] TODO

`HostPollManager` MUST render all polls from `HostDashboardViewModel.polls`. For each
poll:
- Poll question text, poll type badge (MC, Rating, Word Cloud, Open Text)
- Status: Active (highlighted) or Inactive
- Activate / Deactivate button (calling the existing Phase 3 activate/deactivate endpoints)
- Response count and a condensed result summary (percentage bars for MC, average for
  Rating, top-3 words for Word Cloud, response count for Open Text)

The component MUST include a "Create New Poll" button that opens the existing poll
creation flow from Phase 3 (reuse that component rather than duplicating it).

**Acceptance Criteria**

```
Given an event with two polls (one active, one inactive)
When HostPollManager renders
Then the active poll row is visually highlighted (e.g., border or background accent)
And the active poll shows a "Deactivate" button
And the inactive poll shows an "Activate" button

Given the host clicks "Activate" on an inactive poll
When the Phase 3 activate endpoint returns success
Then HostDashboardViewModel.polls updates the activated poll's is_active to true
And all other polls' is_active become false (only one active at a time)
And a poll.activated WebSocket message is received and the ViewModel reflects it

Given the "Create New Poll" button is clicked
When the poll creation modal opens
Then it reuses the existing PollCreationForm component from Phase 3 without duplication
```

---

### FR-7.12 -- HostEventStats Component

**Priority**: P0
**Status**: [ ] TODO

`HostEventStats` MUST display real-time statistics sourced from
`HostDashboardViewModel.stats`. It MUST refresh stats every 30 seconds by re-calling
`GET /api/events/{event_id}/stats`, and MUST also update `participant_count` optimistically
when a new `topic.submitted` WebSocket message arrives from a previously unseen fingerprint.

Display layout:
- Participant count (large, prominent)
- Total topics submitted
- Total votes cast
- Active poll name (or "No active poll")

**Acceptance Criteria**

```
Given the HostEventStats component is mounted
When 30 seconds elapse
Then GET /api/events/{event_id}/stats is called again and stats update

Given a new topic.submitted WebSocket message arrives with a fingerprint not seen before
When handleWebSocketMessage processes the message
Then participant_count in HostDashboardViewModel.stats increments by 1

Given there is no active poll
When HostEventStats renders
Then the active poll field displays "No active poll"
```

---

### FR-7.13 -- HostEventControls Component

**Priority**: P0
**Status**: [ ] TODO

`HostEventControls` MUST render a control bar with:

1. **Close Event button** -- calls `HostDashboardViewModel.closeEvent()`. Shows a
   confirmation dialog ("Close event? Participants will no longer be able to submit topics
   or respond to polls.") before proceeding. After close, button is replaced with
   "Event Closed" (disabled) text.

2. **Copy Join Code button** -- copies the 6-character event code to the clipboard and
   shows a success toast ("Join code copied").

3. **Open Present Mode link** -- opens `/events/:code/present` in a new browser tab.

**Acceptance Criteria**

```
Given the Close Event button is clicked
When the confirmation dialog is displayed
Then clicking "Cancel" dismisses the dialog and does not call closeEvent()
And clicking "Confirm" calls HostDashboardViewModel.closeEvent()

Given closeEvent() succeeds
When the ViewModel's isClosed becomes true
Then the Close Event button is replaced with disabled "Event Closed" text

Given the Copy Join Code button is clicked
When the clipboard write succeeds
Then a success toast "Join code copied" is shown

Given the Open Present Mode link is clicked
When the new tab opens
Then the URL is /events/{code}/present
```

---

### FR-7.14 -- Participant View: Topic Status Badges and Sorting

**Priority**: P0
**Status**: [ ] TODO

The existing participant topic list (from Phase 2) MUST be updated:

1. **Highlighted topics** MUST appear at the top of the list, above all score-sorted
   topics, in their own "Highlighted" section with a visual indicator (e.g., yellow
   background or star icon). There is no score-based ordering within the highlighted
   section; the order is insertion order.

2. **Answered topics** MUST display a green "Answered" badge next to the topic text.
   They MUST remain in their position within the score-sorted list.

3. **Archived topics** MUST be hidden from the participant view entirely.

4. The participant-view ViewModel (from Phase 2) MUST handle the `topic.status_changed`
   WebSocket message and reactively update the topic list.

**Acceptance Criteria**

```
Given an event with topics: [T1 score=10, T2 highlighted, T3 score=5, T4 archived]
When the participant view renders the topic list
Then T2 appears at the very top in the highlighted section
Then T1 and T3 appear below T2, sorted by score
And T4 does not appear anywhere in the participant view

Given a topic.status_changed WebSocket message with status=highlighted arrives
When the participant-view ViewModel processes it
Then the topic moves to the highlighted section at the top without a page reload

Given a topic.status_changed WebSocket message with status=answered arrives
When the participant-view ViewModel processes it
Then a green "Answered" badge appears on the topic row reactively

Given a topic.status_changed WebSocket message with status=archived arrives
When the participant-view ViewModel processes it
Then the topic disappears from the participant list reactively
```

---

### FR-7.15 -- Host Token Persistence and Admin Link

**Priority**: P1
**Status**: [ ] TODO

When a new event is created (Phase 2 `CreateEvent` flow), the API response MUST include
the `host_token`. The frontend `CreateEventViewModel` (Phase 2) MUST store the token in
`localStorage` under the key `host_token_{eventCode}` immediately after successful
event creation. An "Admin" link MUST be rendered in the event page header for the
creator. The link MUST only render if `localStorage.getItem("host_token_{eventCode}")`
returns a non-null value.

**Acceptance Criteria**

```
Given a user creates an event
When the creation API response is received
Then host_token is written to localStorage with key host_token_{eventCode}

Given the user navigates to /events/:code
When the event page header renders
And localStorage contains host_token_{eventCode}
Then an "Admin" link is visible in the header pointing to /events/:code/host

Given a different user (no host_token in localStorage) visits /events/:code
When the event page header renders
Then no "Admin" link is visible

Given the host_token is present in localStorage
When the user clicks the Admin link
Then the user is navigated to /events/:code/host without prompting for a token
```

---

## Non-Goals for This Phase

The following are explicitly out of scope and MUST NOT be implemented as part of Phase 7:

- **No co-host access**: Only the original event creator (holder of `host_token`) can
  access admin endpoints. Multi-user event management is a future feature.
- **No question moderation queue**: Pre-display review of participant submissions (where
  a topic is held in a pending state until the host approves) is a Slido Professional
  feature and is not built here.
- **No event editing**: The host cannot change the event title, join code, or scheduled
  dates from the admin interface. These fields are set at creation time and are immutable.
- **No host account system**: `host_token` is a per-event opaque token stored in the
  browser. There is no persistent user account or session management.
- **No host token regeneration**: Generating a replacement token after accidental sharing
  is deferred (see Open Question [?]-3 in `01-overview.md`). The token issued at creation
  is permanent for the event's lifetime.
- **No poll creation from host dashboard**: The `HostPollManager` reuses the existing
  Phase 3 poll creation flow. The host dashboard does not introduce a new poll creation
  UI.
- **No analytics view**: Engagement metrics and post-event analytics are Phase 9.
- **No display themes**: Visual customisation of the host or participant views is not in scope.
- **No present mode changes**: Present mode is completed in Phase 4. This phase does not
  modify it (though the present mode should respect HIGHLIGHTED topic ordering as part of
  its read-only consumption of the same WebSocket stream).

---

## Technical Notes

### Host Token Security Model

The `host_token` is a randomly generated UUID (128-bit entropy) stored alongside the
event record. It is NOT a signed JWT. Validation is a constant-time equality check
against the stored value. This is intentionally simple -- the threat model is accidental
exposure within a trusted group, not adversarial brute-force attacks. The token MUST be
transmitted exclusively over HTTPS in production (enforced by the existing infrastructure
configuration).

Constant-time comparison MUST use `hmac.compare_digest` (Python standard library) to
prevent timing oracle attacks.

```python
import hmac

def validate_host_token(provided: str, stored: str) -> bool:
    return hmac.compare_digest(provided.encode(), stored.encode())
```

### FastAPI Dependency Injection for Host Auth

Create a reusable FastAPI dependency `require_host_token` that:
1. Extracts `X-Host-Token` from the request header.
2. Resolves the event by `event_id` (path parameter).
3. Calls `validate_host_token`.
4. Raises `HTTPException(403)` on failure.

```python
# src/presentation/api/dependencies/host_auth.py
async def require_host_token(
    event_id: UUID,
    x_host_token: str | None = Header(default=None),
    event_repo: EventRepository = Depends(get_event_repo),
) -> Event:
    if not x_host_token:
        raise HTTPException(status_code=403, detail="Forbidden")
    event = await event_repo.get_by_id(event_id)
    if not event or not validate_host_token(x_host_token, event.host_token):
        raise HTTPException(status_code=403, detail="Forbidden")
    return event
```

This dependency MUST be used on all three new endpoints (FR-7.4, FR-7.5, FR-7.6) and
any future host-only endpoints.

### `PATCH /api/topics/{topic_id}/status` Token Resolution

This endpoint cannot use `event_id` directly from the path -- the path only has
`topic_id`. The dependency MUST first resolve the topic by `topic_id` to find its
`event_id`, then perform the host token validation against that event. This is two
repository lookups but avoids exposing `event_id` in the topic status URL.

### Alembic Migration for TopicStatus Enum

If the `status` column on `topics` was created in Phase 1 with values `OPEN`,
`ANSWERED`, `ARCHIVED`, this phase requires:

```sql
-- Add HIGHLIGHTED value to the enum
ALTER TYPE topicstatus ADD VALUE IF NOT EXISTS 'HIGHLIGHTED';
ALTER TYPE topicstatus ADD VALUE IF NOT EXISTS 'ACTIVE';

-- Rename OPEN -> ACTIVE for existing rows
UPDATE topics SET status = 'ACTIVE' WHERE status = 'OPEN';
```

Because PostgreSQL enum renames require a multi-step migration (add new value, migrate
rows, optionally remove old value), the `OPEN` literal MAY remain in the database type
but MUST no longer be used by application code. A follow-up cleanup migration can remove
it in a future phase.

### MobX Optimistic Updates Pattern

For `updateTopicStatus`, follow the established MobX pattern in the codebase:

```typescript
// Optimistic update pattern
async updateTopicStatus(topicId: string, newStatus: TopicStatus): Promise<void> {
  const topic = this.topics.find(t => t.id === topicId);
  if (!topic) return;

  const previousStatus = topic.status;
  // Optimistic: update immediately
  runInAction(() => { topic.status = newStatus; });

  try {
    await topicsApi.updateStatus(topicId, newStatus, this.hostToken);
  } catch (error) {
    // Rollback on failure
    runInAction(() => {
      topic.status = previousStatus;
      this.error = "Failed to update topic status";
    });
  }
}
```

### WebSocket Message Handling in Participant ViewModel

The existing Phase 2 participant-view ViewModel MUST be extended (not replaced) to handle
the two new message types. The `handleWebSocketMessage` method MUST be updated:

```typescript
case "topic.status_changed": {
  const topic = this.topics.find(t => t.id === msg.topic_id);
  if (topic) {
    runInAction(() => { topic.status = msg.status; });
  }
  break;
}
case "event.closed": {
  runInAction(() => { this.isClosed = true; });
  break;
}
```

When `isClosed` becomes `true`, the participant topic submission form MUST be disabled
and a banner MUST be shown: "This event has ended. New submissions are no longer
accepted."

### Frontend Route Registration

The new route MUST be registered in the React Router configuration (established in Phase
2). The route does NOT use a React Router `loader` for auth -- auth is handled inside the
page component on mount (localStorage read + redirect), keeping the route definition
simple.

```tsx
<Route path="/events/:code/host" element={<HostDashboard />} />
```

### ID Attributes for E2E Testing

The following `id` attributes MUST be present on interactive elements (per CLAUDE.md
conventions):

| Element | id |
|---|---|
| Host dashboard page root | `host-dashboard` |
| Host topic list container | `host-topic-list` |
| Topic row (dynamic) | `host-topic-row-{topicId}` |
| Status badge on topic row | `host-topic-status-{topicId}` |
| Mark Answered button (dynamic) | `host-topic-answered-btn-{topicId}` |
| Highlight button (dynamic) | `host-topic-highlight-btn-{topicId}` |
| Archive button (dynamic) | `host-topic-archive-btn-{topicId}` |
| Restore to Active button (dynamic) | `host-topic-restore-btn-{topicId}` |
| Poll manager container | `host-poll-manager` |
| Event stats container | `host-event-stats` |
| Participant count display | `host-stats-participant-count` |
| Event controls container | `host-event-controls` |
| Close event button | `host-close-event-btn` |
| Copy join code button | `host-copy-code-btn` |
| Open present mode link | `host-open-present-link` |
| Confirmation dialog | `host-close-event-dialog` |
| Confirm close button (in dialog) | `host-close-event-confirm-btn` |
| Cancel close button (in dialog) | `host-close-event-cancel-btn` |
| Admin link in event header | `event-header-admin-link` |
| Participant highlighted section | `participant-highlighted-topics` |
| Answered badge on topic (dynamic) | `participant-topic-answered-badge-{topicId}` |

---

## Testing Requirements

### Unit Tests

All unit tests MUST live in `tests/unit/` and MUST mirror the source structure. No test
MUST take longer than 2 seconds. No test MUST create database records or publish messages.

**FR-7.1 -- Host Token Validation**
- `tests/unit/presentation/api/dependencies/test_host_auth.py`
  - [ ] Returns the event when token matches (valid)
  - [ ] Raises HTTPException(403) when header is missing
  - [ ] Raises HTTPException(403) when token is incorrect
  - [ ] Raises HTTPException(403) when token belongs to a different event
  - [ ] Uses constant-time comparison (verify `hmac.compare_digest` is called)

**FR-7.2 -- TopicStatus Enum**
- `tests/unit/domain/entities/test_topic.py`
  - [ ] Default status is ACTIVE
  - [ ] All four enum values (ACTIVE, ANSWERED, HIGHLIGHTED, ARCHIVED) are valid
  - [ ] An invalid status string raises a validation error

**FR-7.3 -- UpdateTopicStatusUseCase**
- `tests/unit/application/use_cases/test_update_topic_status.py`
  - [ ] Updates status and publishes domain event when topic belongs to event
  - [ ] Raises TopicNotFoundError when topic does not belong to the event
  - [ ] Raises TopicNotFoundError when topic_id does not exist
  - [ ] Does not publish domain event on failure paths

**FR-7.5 -- GetEventStatsUseCase**
- `tests/unit/application/use_cases/test_get_event_stats.py`
  - [ ] Returns correct participant_count from union of fingerprints
  - [ ] Returns correct topic_count including all statuses
  - [ ] Returns active_poll as None when no poll is active
  - [ ] Returns active_poll populated when a poll is active

**FR-7.6 -- CloseEventUseCase**
- `tests/unit/application/use_cases/test_close_event.py`
  - [ ] Transitions event status from ACTIVE to CLOSED
  - [ ] Publishes event.closed domain event on success
  - [ ] Is idempotent: calling on CLOSED event returns the event without error
  - [ ] Does not publish a duplicate domain event when already closed

**FR-7.8 -- HostDashboardViewModel**
- `frontend/src/presentation/pages/host-dashboard/__tests__/HostDashboardViewModel.test.ts`
  - [ ] `activeTopics` excludes highlighted and non-active topics
  - [ ] `highlightedTopics` contains only highlighted topics
  - [ ] Optimistic update changes topic status immediately
  - [ ] Rollback restores previous status when API call fails
  - [ ] `handleWebSocketMessage` with `topic.status_changed` updates the matching topic
  - [ ] `handleWebSocketMessage` with `event.closed` sets `isClosed = true`
  - [ ] `isLoading` transitions correctly during `loadDashboard`

### Integration Tests

All integration tests MUST live in `tests/integration/` and MAY use a real PostgreSQL
instance (via Docker Compose test setup).

**FR-7.4 -- PATCH /api/topics/{topic_id}/status**
- `tests/integration/presentation/api/routes/test_topics_status.py`
  - [ ] Returns 200 and updated topic for valid host token + valid status value
  - [ ] Returns 403 when X-Host-Token header is absent
  - [ ] Returns 403 when X-Host-Token is incorrect
  - [ ] Returns 422 when status value is not a valid enum member
  - [ ] Returns 404 when topic_id does not exist
  - [ ] Persists the new status in the database after successful call

**FR-7.5 -- GET /api/events/{event_id}/stats**
- `tests/integration/presentation/api/routes/test_event_stats.py`
  - [ ] Returns 200 with correct stats structure for a valid host token
  - [ ] Returns 403 when token is absent or incorrect
  - [ ] `participant_count` reflects union of distinct fingerprints

**FR-7.6 -- PATCH /api/events/{event_id}/close**
- `tests/integration/presentation/api/routes/test_event_close.py`
  - [ ] Returns 200 and closed event for valid host token
  - [ ] Returns 403 when token is absent
  - [ ] Subsequent topic creation returns 409 after event is closed
  - [ ] Subsequent poll response submission returns 409 after event is closed
  - [ ] Second call to close is idempotent (200, no error)

**Topic Status WebSocket Propagation**
- `tests/integration/websocket/test_topic_status_websocket.py`
  - [ ] `topic.status_changed` is broadcast to all subscribed clients after PATCH /status
  - [ ] `event.closed` is broadcast to all subscribed clients after PATCH /close
  - [ ] Clients that connect after status change receive the persisted status in initial topic list

### End-to-End Tests

E2E tests MUST use Playwright and follow the existing `tests/e2e/` structure.

**E2E-7.1 -- Host marks topic answered; participant sees badge**
```
1. Create event (save host_token to localStorage)
2. As participant: join event, submit a topic "When is the demo?"
3. As host: navigate to /events/:code/host (Admin link in header)
4. In HostTopicList: click "Mark Answered" on the topic
5. As participant: verify "Answered" badge appears on the topic without page reload
```

**E2E-7.2 -- Host highlights topic; participant sees it at top**
```
1. Create event with host_token
2. As participant: submit two topics (T1 higher score, T2 lower score)
3. As host: click "Highlight" on T2
4. As participant: verify T2 appears above T1 in the highlighted section
```

**E2E-7.3 -- Host archives topic; participant cannot see it**
```
1. Create event with host_token
2. As participant: submit a topic "Off-topic comment"
3. As host: click "Archive" on the topic
4. As participant: verify the topic is no longer visible
```

**E2E-7.4 -- Host closes event; participant cannot submit**
```
1. Create event with host_token
2. As participant: join event and verify topic submission form is enabled
3. As host: click "Close Event" and confirm in the dialog
4. As participant: verify topic submission form is disabled
5. As participant: verify banner "This event has ended" is visible
6. As participant: attempt direct API call to POST /api/topics with event_id; verify 409
```

**E2E-7.5 -- Non-host cannot access admin route**
```
1. Create event
2. As a different browser (no host_token in localStorage): navigate to /events/:code/host
3. Verify redirect to /events/:code
4. Verify error toast "Host access required" is visible
```

---

## Documentation Deliverables

| Deliverable | Location | Description |
|---|---|---|
| Host admin guide | `docs/host-admin-guide.md` | End-user guide for organizers: how to access the admin view, mark questions, manage polls, and close the event |
| OpenAPI docs | Auto-generated by FastAPI | All three new endpoints MUST have `summary`, `description`, and `response_model` annotations so they appear correctly in `/docs` |
| WebSocket event reference | `docs/websocket-events.md` (create or update) | Document `topic.status_changed` and `event.closed` message shapes alongside the existing WebSocket event documentation |
| ViewModel docstrings | `HostDashboardViewModel.ts` | JSDoc on all public actions and computed properties |
| Backend docstrings | `UpdateTopicStatusUseCase`, `CloseEventUseCase`, `GetEventStatsUseCase` | Python docstrings on `__init__` and `execute` methods |
| ADR: Host token security model | `docs/adr/007-host-token-security.md` | Document the decision to use opaque UUID tokens over JWT, the threat model, and the constant-time comparison requirement |

---

## Validation Checklist

Complete all items before marking this phase DONE.

### Backend

- [ ] `TopicStatus` enum includes `ACTIVE`, `ANSWERED`, `HIGHLIGHTED`, `ARCHIVED`
- [ ] Alembic migration adds `HIGHLIGHTED` to the enum and renames `OPEN` rows to `ACTIVE`
- [ ] `host_token` is returned in the event creation API response (Phase 2 endpoint updated if needed)
- [ ] `require_host_token` FastAPI dependency uses `hmac.compare_digest`
- [ ] `UpdateTopicStatusUseCase` validates topic belongs to the event before updating
- [ ] `UpdateTopicStatusUseCase` publishes `topic.status_changed` domain event
- [ ] `CloseEventUseCase` is idempotent
- [ ] `CloseEventUseCase` publishes `event.closed` domain event
- [ ] `CreateTopicUseCase` rejects topics for CLOSED events with 409
- [ ] `SubmitPollResponseUseCase` rejects responses for CLOSED events with 409
- [ ] `GetEventStatsUseCase` counts distinct fingerprints from both topics and poll_responses
- [ ] All three new endpoints return 403 (not 401) for missing/invalid host token
- [ ] All three new endpoints are tagged and documented in OpenAPI
- [ ] All unit tests pass with no warnings
- [ ] All integration tests pass

### Frontend

- [ ] `host_token_{eventCode}` is written to `localStorage` immediately after event creation
- [ ] Admin link renders only when `localStorage` contains the token
- [ ] `/events/:code/host` redirects to participant view when no token is in localStorage
- [ ] `HostDashboardViewModel` attaches `X-Host-Token` header to all admin API calls
- [ ] Optimistic topic status update rolls back correctly on API failure
- [ ] `handleWebSocketMessage` handles both `topic.status_changed` and `event.closed`
- [ ] Highlighted topics appear above score-sorted topics in participant view
- [ ] Archived topics are hidden from participant view
- [ ] Participant view shows event-closed banner when `isClosed` is true
- [ ] All required `id` attributes are present for E2E test selectors
- [ ] All components use Tailwind CSS only (no inline styles, no custom CSS)
- [ ] No component exceeds 100 lines (decompose if needed)
- [ ] All frontend unit tests pass

### End-to-End

- [ ] E2E-7.1 passes (mark answered, participant sees badge)
- [ ] E2E-7.2 passes (highlight, participant sees at top)
- [ ] E2E-7.3 passes (archive, participant cannot see)
- [ ] E2E-7.4 passes (close event, participant cannot submit)
- [ ] E2E-7.5 passes (non-host redirected from admin route)

### Quality Gates

- [ ] `uv run ruff check .` passes with no errors
- [ ] `uv run ruff format .` produces no diffs
- [ ] `uv run pyright` passes with no errors
- [ ] Backend test coverage for new domain + application code >= 80% (NFR-3)
- [ ] All existing E2E tests from prior phases continue to pass (NFR-8)
- [ ] Mobile layout (375px) tested for participant view status badges (NFR-5)
- [ ] ADR `docs/adr/007-host-token-security.md` written and committed
