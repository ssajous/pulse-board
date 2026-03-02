# Slido Parity -- Overview

> See [`docs/prd/slido-parity/00-config.md`](./00-config.md) for project variables,
> stack constraints, and status.

---

## Problem Statement

Pulse Board is a real-time community engagement platform with anonymous topic submission,
up/down voting, and live score updates via WebSocket. It is strong at surfacing what a
group cares about most, but it operates as a single persistent board. It has no concept
of a time-bound event, no structured polling, and no presentation mode.

Slido's free tier sets the industry baseline for live audience interaction in meetings:
event join codes, multiple poll types (multiple choice, word cloud, rating, open text),
a projector-ready present mode with QR code, and a host management interface. Teams
evaluating Pulse Board for meeting or conference use hit these gaps immediately.

This PRD captures the work required to close the 12 highest-impact feature gaps (Tier 1
and Tier 2 from `docs/feature-gap-slido.md`) without breaking the existing single-board
experience that current users depend on.

---

## Goals

- **G-1**: Introduce a first-class `Event` entity so organizers can create time-bound
  sessions with unique join codes, scoping all topics and polls to that session.
- **G-2**: Add four poll types (multiple choice, rating, word cloud, open text) with
  real-time result broadcasting over the existing WebSocket infrastructure.
- **G-3**: Deliver a presentation-optimized present mode with QR code so organizers can
  project the board during live meetings.
- **G-4**: Provide a host/admin interface that gives organizers control over polls and
  question status without exposing management controls to participants.
- **G-5**: Enable optional named submissions so participants can choose to identify
  themselves when asking a question or submitting feedback.
- **G-6**: Surface per-event analytics so organizers can review engagement after a
  session ends.
- **G-7**: Preserve the existing single-board mode as a zero-configuration quick start
  (topics with a null `event_id` continue to work exactly as before).

---

## Non-Goals

- **NG-1**: Slido Tier 3+ features -- quizzes with leaderboards, ranking polls, surveys,
  question moderation queues, and data export are explicitly out of scope for this PRD.
- **NG-2**: Platform integrations -- PowerPoint add-in, Google Slides, Teams, Zoom, and
  Webex integrations are not included.
- **NG-3**: Custom branding -- logo upload, custom color schemes, and background images
  are not included.
- **NG-4**: Multi-room events -- parallel breakout tracks within a single event are not
  in scope.
- **NG-5**: SSO or account-based authentication for organizers -- host/admin mode uses
  browser-session elevation, not a user account system.
- **NG-6**: Passcode protection for events -- optional passcode layer is deferred to a
  future PRD.
- **NG-7**: Removal of downvote functionality -- Pulse Board's up/down voting model is a
  deliberate differentiator from Slido and MUST be preserved.
- **NG-8**: Replacement of browser fingerprinting -- anonymous identity via FingerprintJS
  v5 continues unchanged.

---

## User Stories

| ID  | Role        | Story                                                                                          | Priority |
|-----|-------------|-----------------------------------------------------------------------------------------------|----------|
| US-01 | Organizer | I want to create a time-bound event so participants can interact during my meeting.           | P0 |
| US-02 | Participant | I want to join an event by entering a short code so I can start participating quickly.        | P0 |
| US-03 | Organizer | I want to create multiple choice polls so I can gather structured feedback from my audience.  | P0 |
| US-04 | Organizer | I want to display event content on a projector so my audience can follow along.               | P0 |
| US-05 | Participant | I want to scan a QR code to join an event instantly from my phone.                           | P0 |
| US-06 | Organizer | I want rating polls to collect quick numeric feedback on sessions or proposals.               | P1 |
| US-07 | Participant | I want to see a word cloud forming in real-time from everyone's short text responses.         | P1 |
| US-08 | Organizer | I want a host management view to activate polls, manage questions, and see participant count. | P1 |
| US-09 | Organizer | I want to mark questions as answered so the audience knows they were addressed.               | P1 |
| US-10 | Participant | I want to optionally share my name when submitting a question.                                | P1 |
| US-11 | Organizer | I want open text polls to collect free-form feedback without voting mechanics.                | P1 |
| US-12 | Organizer | I want to see engagement analytics after my event ends so I can improve future sessions.      | P2 |

---

## Architecture Notes

### Domain Model Changes

The following new domain entities are introduced. Existing entities (`Topic`, `Vote`) are
extended, not replaced.

```
Event
  id            UUID, primary key
  title         string (1-100 chars)
  code          string (6 chars, unique, alphanumeric)
  status        enum: SCHEDULED | ACTIVE | CLOSED
  starts_at     datetime (optional)
  ends_at       datetime (optional)
  created_at    datetime

Poll
  id            UUID, primary key
  event_id      UUID, FK -> Event
  poll_type     enum: MULTIPLE_CHOICE | RATING | WORD_CLOUD | OPEN_TEXT
  question      string (1-255 chars)
  options       JSONB (for MULTIPLE_CHOICE only; null for other types)
  is_active     boolean (only one poll active per event at a time)
  created_at    datetime

PollResponse
  id            UUID, primary key
  poll_id       UUID, FK -> Poll
  fingerprint   string (browser fingerprint for dedup)
  value         string (selected option, numeric rating, or free text)
  author_name   string (optional; null when anonymous)
  created_at    datetime

Topic (extended)
  event_id      UUID, FK -> Event, nullable
    -- null means single-board mode (existing behaviour preserved)
  status        enum: OPEN | ANSWERED | ARCHIVED
    -- new field; default OPEN
  author_name   string, nullable
    -- new field; null means anonymous (existing behaviour preserved)
```

### Backward Compatibility

Topics with `event_id = null` continue to render on the root `/` board exactly as they
do today. No existing API contract changes. The `status` and `author_name` columns are
additive with safe defaults (`OPEN` and `null` respectively).

### Frontend Routing

```
/                        -- existing single-board mode (unchanged)
/events/new              -- event creation form (organizer)
/events/join             -- code-entry landing page (participant)
/events/:code            -- participant view for a specific event
/events/:code/host       -- host/admin management view
/events/:code/present    -- projection-optimized present mode
/events/:code/analytics  -- post-event analytics dashboard
```

### WebSocket Event Extensions

New WebSocket message types are broadcast alongside existing vote/topic events:

- `poll.activated` -- a poll has been made active; payload contains poll definition
- `poll.deactivated` -- a poll has been closed
- `poll.result_update` -- updated aggregate results for an active poll
- `topic.status_changed` -- topic marked answered or archived
- `event.closed` -- the event has ended

### Present Mode

Present mode is a frontend-only route (`/events/:code/present`) that consumes the same
WebSocket event stream as the participant view. It requires no new backend API endpoints.
It renders in a full-screen layout suitable for projection, with large typography, the
current poll results or active topic list, and a QR code linking to the join page.

### Host/Admin Mode

Host mode (`/events/:code/host`) is a protected route gated by a host token set in
`localStorage` at event creation. The backend MUST validate a `X-Host-Token` header on
all write operations that require elevated access (poll create/activate, topic status
update). The token is a randomly generated UUID stored with the event record. This is a
lightweight approach that avoids introducing a full user account system while still
preventing participants from performing host actions.

---

## Phase Summary

| Phase | Name                    | Features                   | Slice Type      | Dependencies       |
|-------|-------------------------|----------------------------|-----------------|--------------------|
| 1     | Scaffolding             | Infrastructure setup       | Scaffolding     | None               |
| 2     | Event Management        | #1 Event creation, #2 Join codes | Vertical slice | Phase 1       |
| 3     | Multiple Choice Polls   | #3 Multiple choice polls   | Vertical slice  | Phase 2            |
| 4     | Present Mode            | #4 Present mode, #5 QR code | Vertical slice | Phase 3            |
| 5     | Rating & Open Text Polls | #6 Rating polls, #12 Open text polls | Vertical slice | Phase 3  |
| 6     | Word Cloud Polls        | #7 Word cloud polls        | Vertical slice  | Phase 3            |
| 7     | Host/Admin Mode         | #8 Host mode, #10 Question status | Vertical slice | Phase 2, 3  |
| 8     | Named/Anonymous Toggle  | #11 Named vs. anonymous    | Vertical slice  | Phase 2            |
| 9     | Event Analytics         | #9 Analytics dashboard     | Vertical slice  | Phases 2, 3, 5, 6  |

### Phase Descriptions

**Phase 1 -- Scaffolding** sets up the shared technical foundation: new database
migrations for `events`, `polls`, and `poll_responses` tables; the `event_id` and
`status` columns on `topics`; base domain entities and port interfaces; and frontend
route scaffolding. Delivers no end-user business value but unblocks all subsequent
phases.

**Phase 2 -- Event Management** delivers the complete event lifecycle: an organizer can
create a named event and receive a join code; a participant can enter the code on a
landing page and see the event's topic board. Topics submitted inside an event are
scoped to that event. All real-time topic and voting behaviour from the existing app
continues to work within the event scope.

**Phase 3 -- Multiple Choice Polls** delivers the full poll lifecycle for the most common
poll type: an organizer creates a poll with options, activates it, participants see the
poll and submit their choice, and real-time result bars update as responses arrive. This
phase establishes the poll infrastructure (entities, use cases, WebSocket events, and
frontend ViewModel) that Phases 5 and 6 extend.

**Phase 4 -- Present Mode** delivers the projection-optimized display route and the QR
code join mechanism. An organizer can open `/events/:code/present` in a second window,
share their screen, and the audience can scan the QR code to join. The present mode
shows the active poll results or the topic list, auto-updating in real-time.

**Phase 5 -- Rating & Open Text Polls** extends the Phase 3 poll infrastructure with two
additional poll types. Rating polls let participants submit a 1-5 numeric score; the
display shows the average and distribution. Open text polls collect free-form responses
displayed as a scrollable list.

**Phase 6 -- Word Cloud Polls** adds the visually distinctive word cloud poll type.
Participants submit a short text response (1-40 chars); the frontend renders a dynamic
word cloud where more frequent responses appear larger. Updates arrive via the existing
`poll.result_update` WebSocket event.

**Phase 7 -- Host/Admin Mode** delivers the organizer management interface: a dedicated
route showing all polls (active and inactive), all event topics, participant count, and
controls to activate/deactivate polls and change topic status. Question status tracking
(mark a topic as ANSWERED or ARCHIVED) is built here, with real-time status propagation
to the participant view.

**Phase 8 -- Named/Anonymous Toggle** allows participants to optionally enter their name
when submitting a topic or poll response. The toggle is per-submission. Existing
anonymous submissions are unaffected. The organizer sees names in the host view when
provided.

**Phase 9 -- Event Analytics** delivers a post-event dashboard at
`/events/:code/analytics` showing: total participants (unique fingerprints), total
questions submitted, total votes cast, poll participation rates per poll, and a timeline
of activity. Data is read-only and computed from existing records with no new tracking
infrastructure.

---

## Non-Functional Requirements

| ID    | Requirement                                                           | Threshold          | Rationale |
|-------|-----------------------------------------------------------------------|--------------------|-----------|
| NFR-1 | API p95 response time under 100 concurrent users                      | < 200ms            | Matches existing SLA; new endpoints must not regress it |
| NFR-2 | WebSocket message delivery latency (vote or poll result to all clients) | < 500ms          | Acceptable for live event use; stricter than 100ms target only where feasible |
| NFR-3 | Test coverage for all new backend code (domain + application layers)  | >= 80%             | Maintains existing quality bar |
| NFR-4 | All new REST endpoints documented in OpenAPI                          | 100%               | FastAPI generates this automatically; MUST not be disabled |
| NFR-5 | Mobile-responsive UI for all new views                                | WCAG breakpoints   | Participants join from phones; participant and join views MUST work on 375px width |
| NFR-6 | WCAG 2.1 AA compliance for all new interactive elements               | AA level           | Required for accessibility parity with Slido free tier |
| NFR-7 | Graceful degradation when WebSocket disconnects                       | Reconnect <= 5s    | Inherited from existing behaviour; present mode MUST not freeze on disconnect |
| NFR-8 | Single-board mode backward compatibility                              | Zero regressions   | All existing E2E tests MUST continue to pass unmodified |
| NFR-9 | Event join code collision probability                                 | < 0.1% at 1000 active events | Code generation MUST use a retry-on-collision strategy |

---

## Open Questions

| ID  | Question                                                                                         | Impact if Unresolved                            | Status |
|-----|--------------------------------------------------------------------------------------------------|-------------------------------------------------|--------|
| [?]-1 | Should events have a maximum duration enforced by the server, or should the host close them manually? | Affects event entity design and lifecycle state machine | **RESOLVED**: Host closes events manually. No server-enforced max duration. |
| [?]-2 | Should poll results be visible to participants in real-time while the poll is active, or only after the host closes the poll? | Affects Phase 3 WebSocket broadcast logic and UI | **RESOLVED**: Results visible only after the poll is closed by the host. |
| [?]-3 | Should the host token be regenerable after creation (in case of accidental sharing), or is it single-use at creation time? | Affects host mode security model in Phase 7 | **RESOLVED**: Single-use at creation time. Not regenerable. |
| [?]-4 | For word cloud polls, should text normalization (lowercase, punctuation strip) be applied server-side or client-side? | Affects aggregate quality and Phase 6 backend design | **RESOLVED**: Server-side text normalization. |
| [?]-5 | Should event analytics (Phase 9) be visible only to the host, or also to participants after the event closes? | Affects access control on analytics route | **RESOLVED**: Host-only. Analytics not visible to participants. |

---

## Feature-to-Phase Mapping

| Feature # | Feature Name             | Phase | Priority |
|-----------|--------------------------|-------|----------|
| 1         | Event/session creation   | 2     | P0 |
| 2         | Event join codes         | 2     | P0 |
| 3         | Multiple choice polls    | 3     | P0 |
| 4         | Present mode             | 4     | P0 |
| 5         | QR code display          | 4     | P0 |
| 6         | Rating polls             | 5     | P1 |
| 7         | Word cloud polls         | 6     | P1 |
| 8         | Host/admin mode          | 7     | P1 |
| 9         | Event analytics          | 9     | P2 |
| 10        | Question status tracking | 7     | P1 |
| 11        | Named vs. anonymous      | 8     | P1 |
| 12        | Open text polls          | 5     | P1 |
