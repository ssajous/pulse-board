# Phase 9 -- Event Analytics Dashboard

> See [`docs/prd/slido-parity/00-config.md`](./00-config.md) for project variables,
> stack constraints, and status.

---

## Phase Context

**Slice type**: Vertical slice (capstone)
**Depends on**: Phase 2 (Event Management), Phase 3 (Multiple Choice Polls),
Phase 5 (Rating and Open Text Polls), Phase 6 (Word Cloud Polls),
Phase 7 (Host/Admin Mode)
**Delivers**: A host-only analytics dashboard at `/events/:code/admin/analytics` that
presents post-event engagement metrics. Hosts can review total participation, submission
volume, voting activity, poll engagement rates, and a timeline of activity across the
event. Data is read-only, computed from existing records, and requires no new tracking
infrastructure.

**After this phase a host can**:
1. Navigate to the analytics dashboard from the host admin interface.
2. See summary cards for: unique participants, total topics submitted, total votes cast,
   and total poll responses.
3. See a per-poll bar chart showing the participation rate (responses / unique
   participants) for each poll.
4. See a line/area chart of activity over time, bucketed into 5-minute intervals,
   showing topics submitted and votes cast per bucket.
5. See a ranked table of the top topics by net score.
6. See the average rating for any RATING-type polls.
7. Refresh the dashboard manually to get updated data (no auto-refresh).

---

## Prerequisites

- [ ] Phase 2 complete: `Event`, `Topic` with `event_id`, join code routing.
- [ ] Phase 3 complete: `Poll`, `PollResponse`, MULTIPLE_CHOICE poll lifecycle.
- [ ] Phase 5 complete: RATING and OPEN_TEXT poll types with responses.
- [ ] Phase 6 complete: WORD_CLOUD poll type with responses.
- [ ] Phase 7 complete: Host token validation middleware, `/events/:code/host` route,
      host admin navigation.
- [ ] `X-Host-Token` header validation working on all existing host-only endpoints.
- [ ] `Vote` records include `created_at` timestamp (required for timeline bucketing).

---

## Functional Requirements

### Backend

#### FR-9.1 -- GetEventAnalyticsUseCase

**Priority**: P2 -- MUST
**Description**: A new `GetEventAnalyticsUseCase` MUST compute and return an
`EventAnalyticsDTO` containing all metrics described in FR-9.2 through FR-9.7 for a
given event. The use case MUST accept an event code (or ID) and a host token; it MUST
reject requests with an invalid host token with a 403 response.

**Acceptance Criteria**:

```
Given a valid event code and matching host_token
When GetEventAnalyticsUseCase executes
Then it returns an EventAnalyticsDTO with all metric fields populated
 And no exception is raised
```

```
Given a valid event code and an incorrect host_token
When GetEventAnalyticsUseCase executes
Then it raises an UnauthorizedError
 And the caller receives a 403 HTTP response
```

```
Given a valid event code with zero participant activity
When GetEventAnalyticsUseCase executes
Then all counts are 0, all rates are 0.0, timeline is empty, top_topics is empty
 And no exception is raised
```

**Technical notes**:
- The use case is in `src/application/use_cases/get_event_analytics.py`.
- It depends on a new `AnalyticsRepository` port defined in `src/domain/ports/`.
- The concrete implementation lives in `src/infrastructure/repositories/`.

---

#### FR-9.2 -- Unique participant count

**Priority**: P2 -- MUST
**Description**: The analytics MUST include the count of distinct browser fingerprints
that submitted at least one topic, vote, or poll response within the event.

**Acceptance Criteria**:

```
Given 3 participants (fingerprints A, B, C) each submitted one topic
 And participant A also cast 2 votes
When analytics are computed
Then unique_participants = 3
```

```
Given one participant submitted 5 topics and 10 votes
When analytics are computed
Then unique_participants = 1
```

**Technical notes**:
- SQL: `COUNT(DISTINCT fingerprint)` across `topics`, `votes`, and `poll_responses`
  scoped to the event (via `event_id` on topics; via `poll_id -> poll.event_id` for
  poll_responses; via `topic_id -> topic.event_id` for votes).
- The result is a UNION of all three fingerprint sets before the COUNT DISTINCT.

---

#### FR-9.3 -- Submission volume metrics

**Priority**: P2 -- MUST
**Description**: The analytics MUST include:
- `total_topics`: count of all topics scoped to the event (all statuses).
- `total_votes`: count of all vote records for topics in the event.
- `total_poll_responses`: count of all poll response records for polls in the event.

**Acceptance Criteria**:

```
Given an event with 10 topics, 45 votes on those topics, and 30 poll responses across 2 polls
When analytics are computed
Then total_topics = 10
 And total_votes = 45
 And total_poll_responses = 30
```

---

#### FR-9.4 -- Poll participation rates

**Priority**: P2 -- MUST
**Description**: For each poll in the event, the analytics MUST include a participation
rate defined as:

```
participation_rate = distinct_responders / unique_participants
```

where `distinct_responders` is the count of distinct fingerprints that submitted a
response to that poll, and `unique_participants` is the event-level unique participant
count (FR-9.2).

If `unique_participants` is 0, the rate MUST be 0.0.

**Acceptance Criteria**:

```
Given an event with 10 unique participants
 And Poll A has 7 distinct responders
 And Poll B has 3 distinct responders
When analytics are computed
Then poll_participation[Poll A].rate = 0.70
 And poll_participation[Poll B].rate = 0.30
 And each entry includes poll_id, poll_question, poll_type, responder_count, and rate
```

```
Given unique_participants = 0
When analytics are computed
Then all poll participation rates = 0.0
```

---

#### FR-9.5 -- Engagement timeline

**Priority**: P2 -- MUST
**Description**: The analytics MUST include a time-series array of activity bucketed into
5-minute intervals. Each bucket covers a 5-minute window (UTC) and contains:
- `bucket_start`: ISO 8601 UTC timestamp marking the start of the interval.
- `topics_submitted`: count of topics created in that interval.
- `votes_cast`: count of votes cast in that interval.
- `poll_responses`: count of poll responses submitted in that interval.

Buckets with all-zero counts MUST be omitted from the array.

**Acceptance Criteria**:

```
Given topics were submitted at 14:02, 14:07, and 14:13 UTC
 And votes were cast at 14:03 and 14:08 UTC
When analytics are computed
Then the timeline contains 3 buckets:
  {bucket_start: "2026-03-02T14:00:00Z", topics_submitted: 1, votes_cast: 1, poll_responses: 0}
  {bucket_start: "2026-03-02T14:05:00Z", topics_submitted: 1, votes_cast: 1, poll_responses: 0}
  {bucket_start: "2026-03-02T14:10:00Z", topics_submitted: 1, votes_cast: 0, poll_responses: 0}
```

```
Given no activity was recorded between 14:15 and 14:30
When analytics are computed
Then no buckets are emitted for that range
```

**Technical notes**:
- Use `DATE_TRUNC('minute', created_at) - (EXTRACT(minute FROM created_at)::int % 5) * INTERVAL '1 minute'`
  or equivalent to floor timestamps to 5-minute boundaries in PostgreSQL.
- Query topics, votes, and poll_responses separately and merge buckets in Python.
- Return timeline sorted ascending by `bucket_start`.

---

#### FR-9.6 -- Top topics by score

**Priority**: P2 -- MUST
**Description**: The analytics MUST include a ranked list of the top 10 topics in the
event, ordered by net score (upvotes minus downvotes) descending. Each entry includes:
`topic_id`, `text`, `score`, `display_name` (or null), `status`.

**Acceptance Criteria**:

```
Given an event with 15 topics with varying scores
When analytics are computed
Then top_topics contains exactly 10 entries
 And they are ordered by score descending
 And entries at equal scores are ordered by created_at ascending (earliest first)
```

```
Given an event with 3 topics
When analytics are computed
Then top_topics contains 3 entries (fewer than 10 is fine)
```

---

#### FR-9.7 -- Average rating per RATING poll

**Priority**: P2 -- MUST
**Description**: For each RATING-type poll in the event, the analytics MUST include
the average rating (arithmetic mean of all numeric response values) rounded to two
decimal places. If a RATING poll has no responses, average_rating MUST be null.

**Acceptance Criteria**:

```
Given a RATING poll with responses [3, 4, 5, 4, 3]
When analytics are computed
Then the poll entry includes average_rating = 3.80
```

```
Given a RATING poll with no responses
When analytics are computed
Then the poll entry includes average_rating = null
```

---

#### FR-9.8 -- Analytics API endpoint

**Priority**: P2 -- MUST
**Description**: A new REST endpoint MUST be created:

```
GET /api/events/:code/analytics
Headers: X-Host-Token: <token>
```

The endpoint MUST return the `EventAnalyticsDTO` as JSON. It MUST require a valid
`X-Host-Token` header and return 403 if missing or invalid. It MUST return 404 if the
event code does not exist.

**Acceptance Criteria**:

```
Given a valid event code and correct X-Host-Token
When GET /api/events/:code/analytics is called
Then the response status is 200
 And the body is a valid EventAnalyticsDTO JSON object
 And the response time is under 2000ms for events with <= 100 participants (NFR-9.1)
```

```
Given a valid event code and missing X-Host-Token header
When GET /api/events/:code/analytics is called
Then the response status is 403
```

```
Given an event code that does not exist
When GET /api/events/:code/analytics is called
Then the response status is 404
```

---

#### FR-9.9 -- SQL query efficiency and indexing

**Priority**: P2 -- SHOULD
**Description**: The analytics queries MUST use efficient SQL. Required indexes:
- `topics.event_id` -- already expected from Phase 2.
- `topics.created_at` -- add if not present.
- `votes.created_at` -- add if not present.
- `poll_responses.poll_id` -- already expected from Phase 3.
- `poll_responses.created_at` -- add if not present.
- `polls.event_id` -- already expected from Phase 3.

**Acceptance Criteria**:

```
Given an event with 100 participants, 500 topics, 2000 votes, and 300 poll responses
When GET /api/events/:code/analytics is called
Then the response time is under 2000ms (NFR-9.1)
 And no full table scans are performed on large tables (verified by EXPLAIN ANALYZE)
```

---

### Frontend

#### FR-9.10 -- AnalyticsDashboard page and routing

**Priority**: P2 -- MUST
**Description**: A new page MUST be accessible at `/events/:code/admin/analytics`.
The route MUST be protected: if no host token is present in localStorage, redirect
to `/events/:code/host`. The page MUST include a "Refresh" button that re-fetches
analytics data on demand.

**Acceptance Criteria**:

```
Given a user with a valid host token navigates to /events/:code/admin/analytics
When the page loads
Then the dashboard renders with a loading state while the API call is in flight
 And on success, all metric sections are visible
```

```
Given a user without a host token navigates to /events/:code/admin/analytics
When the page loads
Then the user is redirected to /events/:code/host
```

```
Given the dashboard is loaded
When the user clicks "Refresh"
Then the AnalyticsDashboardViewModel re-fetches all analytics data
 And the loading state is shown during the fetch
 And the display updates with the new data upon success
```

---

#### FR-9.11 -- AnalyticsDashboardViewModel (MobX)

**Priority**: P2 -- MUST
**Description**: An `AnalyticsDashboardViewModel` MUST encapsulate all data-fetching
state, computed properties for chart data, and the refresh action. React components MUST
be observers only.

**Acceptance Criteria**:

```
Given the ViewModel is instantiated
When fetchAnalytics() is called
Then isLoading = true during the request
 And isLoading = false and analyticsData is populated on success
 And isLoading = false and error is set on failure
```

**Computed properties required**:
- `summaryCards`: derived from raw metrics (unique_participants, total_topics,
  total_votes, total_poll_responses).
- `timelineChartData`: array of `{ label: string, topics: number, votes: number,
  responses: number }` mapped from the engagement timeline buckets, formatted for the
  charting library.
- `pollParticipationChartData`: array of `{ pollQuestion: string, rate: number,
  responderCount: number }` for the participation bar chart.
- `topTopicsRows`: array of `{ rank: number, text: string, score: number, author: string,
  status: string }` for the table.
- `ratingPollSummaries`: array of `{ question: string, averageRating: number | null }`
  for rating poll cards.

---

#### FR-9.12 -- AnalyticsSummaryCards component

**Priority**: P2 -- MUST
**Description**: A `AnalyticsSummaryCards` component MUST render four metric cards:
- Unique Participants
- Topics Submitted
- Votes Cast
- Poll Responses

Each card shows the metric label, the numeric value, and a descriptive icon or color.

**Acceptance Criteria**:

```
Given analyticsData with unique_participants = 47, total_topics = 93,
total_votes = 312, total_poll_responses = 141
When AnalyticsSummaryCards renders
Then four cards are visible with those values
 And each card has an accessible label matching the metric name
```

**Technical notes**:
- Component IDs: `id="analytics-card-participants"`, `id="analytics-card-topics"`,
  `id="analytics-card-votes"`, `id="analytics-card-responses"`.

---

#### FR-9.13 -- EngagementTimeline component

**Priority**: P2 -- MUST
**Description**: An `EngagementTimeline` component MUST render a line or area chart
showing topics submitted, votes cast, and poll responses over time. The X-axis represents
5-minute time buckets formatted as `HH:mm`. The Y-axis represents count. The component
MUST use `recharts` (preferred) or `Chart.js` via a lightweight wrapper.

**Acceptance Criteria**:

```
Given timeline data with 6 buckets over a 30-minute event
When EngagementTimeline renders
Then a chart is visible with 6 data points on the X-axis
 And three data series are distinguishable (topics, votes, poll responses)
 And a legend identifies each series
```

```
Given an empty timeline (zero activity)
When EngagementTimeline renders
Then the component shows an empty-state message: "No activity recorded yet"
 And no chart axes are rendered
```

**Technical notes**:
- Chart MUST be responsive: `width="100%"` with `ResponsiveContainer` (recharts) or
  equivalent.
- Chart MUST be readable at 768px viewport width (tablet breakpoint per NFR-5).
- Component ID: `id="analytics-timeline-chart"`.
- If `recharts` is not already in `package.json`, add it: `npm install recharts`.

---

#### FR-9.14 -- PollParticipationChart component

**Priority**: P2 -- MUST
**Description**: A `PollParticipationChart` component MUST render a horizontal bar chart
where each bar represents one poll. The bar length represents participation rate (0-100%).
The poll question is the Y-axis label (truncated to 40 chars if needed). The bar shows
the percentage value as a label.

**Acceptance Criteria**:

```
Given two polls with participation rates 70% and 30%
When PollParticipationChart renders
Then two horizontal bars are shown
 And the longer bar corresponds to 70%
 And each bar is labelled with the percentage value
```

```
Given no polls in the event
When PollParticipationChart renders
Then an empty-state message reads "No polls were run for this event"
```

**Technical notes**:
- Component ID: `id="analytics-poll-participation-chart"`.
- Each bar ID: `id="analytics-poll-bar-{pollId}"`.

---

#### FR-9.15 -- TopTopicsTable component

**Priority**: P2 -- MUST
**Description**: A `TopTopicsTable` component MUST render a table of the top 10 topics
(or fewer) with columns: Rank, Topic, Author, Score, Status. Rank is derived from
position in the sorted list (1-indexed). Author shows `display_name` or "Anonymous".
Status shows the topic status (OPEN, ANSWERED, ARCHIVED).

**Acceptance Criteria**:

```
Given a top_topics list with 8 topics
When TopTopicsTable renders
Then a table with 8 rows is visible
 And columns Rank, Topic, Author, Score, Status are present
 And rows are ordered by rank ascending (rank 1 at top)
```

```
Given a topic with display_name = null in the top_topics list
When TopTopicsTable renders
Then that row shows "Anonymous" in the Author column
```

**Technical notes**:
- Table ID: `id="analytics-top-topics-table"`.
- Row IDs: `id="analytics-topic-row-{topicId}"`.

---

#### FR-9.16 -- Rating poll summary display

**Priority**: P2 -- MUST
**Description**: For each RATING-type poll, the dashboard MUST display a summary card
showing the poll question and the average rating value (e.g., "4.20 / 5"). If average
is null (no responses), show "No responses yet".

**Acceptance Criteria**:

```
Given a RATING poll "How would you rate this session?" with average_rating = 4.20
When the dashboard renders
Then a card appears with the question text and "4.20 / 5"
```

```
Given a RATING poll with no responses (average_rating = null)
When the dashboard renders
Then the card shows "No responses yet"
```

---

#### FR-9.17 -- Integration into host admin navigation

**Priority**: P2 -- MUST
**Description**: The host admin view (`/events/:code/host`) MUST include a navigation
link to the analytics dashboard. The link MUST be labelled "Analytics".

**Acceptance Criteria**:

```
Given the host is on the /events/:code/host page
When they click the "Analytics" navigation link
Then they are navigated to /events/:code/admin/analytics
```

**Technical notes**:
- Navigation link ID: `id="host-nav-analytics"`.

---

## Non-Goals for This Phase

- **No real-time auto-updating analytics** -- the dashboard is explicitly a snapshot
  view. A manual "Refresh" button is provided; auto-polling or WebSocket-driven updates
  are not implemented in this phase.
- **No data export** -- CSV, Excel, or PDF export of analytics data is deferred to a
  future phase.
- **No sentiment analysis** -- AI-driven classification of topic text is a Tier 4 feature
  outside this PRD.
- **No cross-event analytics** -- metrics are scoped to a single event; organization-
  level or multi-event trend comparisons are not in scope.
- **No historical trend comparisons** -- the dashboard shows only the current event's
  data; there is no baseline or period-over-period comparison.
- **No participant-facing analytics** -- the dashboard is host-only. Participants cannot
  access it, even after the event closes. (Open question [?]-5 is resolved as host-only
  for this phase.)
- **No quiz or ranking poll analytics** -- those poll types are not included in this PRD.
- **No word cloud analytics breakdown** -- word cloud response frequency data is already
  visible in the poll results view; a dedicated analytics breakdown is not added here.
- **No custom date range filtering** -- all metrics cover the full event lifetime.

---

## Testing Requirements

### Unit Tests

| ID | Target | Scenario |
|----|--------|----------|
| UT-9.1 | `GetEventAnalyticsUseCase` | Valid event + valid token -- returns populated DTO |
| UT-9.2 | `GetEventAnalyticsUseCase` | Invalid host token -- raises UnauthorizedError |
| UT-9.3 | `GetEventAnalyticsUseCase` | Zero-activity event -- all counts 0, empty collections |
| UT-9.4 | `GetEventAnalyticsUseCase` | Unique participant union logic -- same fingerprint in topics and votes counted once |
| UT-9.5 | `GetEventAnalyticsUseCase` | Poll participation rate calculation -- 0 participants yields 0.0 rate |
| UT-9.6 | `GetEventAnalyticsUseCase` | Timeline bucketing -- 14:02 UTC assigned to 14:00 bucket |
| UT-9.7 | `GetEventAnalyticsUseCase` | Timeline bucketing -- 14:07 UTC assigned to 14:05 bucket |
| UT-9.8 | `GetEventAnalyticsUseCase` | Timeline -- empty buckets omitted |
| UT-9.9 | `GetEventAnalyticsUseCase` | Top topics -- limited to 10, ordered by score desc |
| UT-9.10 | `GetEventAnalyticsUseCase` | Average rating -- correct mean for [3, 4, 5, 4, 3] = 3.80 |
| UT-9.11 | `GetEventAnalyticsUseCase` | Average rating -- null when no responses |
| UT-9.12 | `AnalyticsDashboardViewModel` | `fetchAnalytics()` sets isLoading=true during fetch |
| UT-9.13 | `AnalyticsDashboardViewModel` | On success, isLoading=false, analyticsData populated |
| UT-9.14 | `AnalyticsDashboardViewModel` | On fetch error, isLoading=false, error message set |
| UT-9.15 | `AnalyticsDashboardViewModel` | `summaryCards` computed correctly from raw DTO |
| UT-9.16 | `AnalyticsDashboardViewModel` | `timelineChartData` maps bucket_start to HH:mm label |
| UT-9.17 | `AnalyticsDashboardViewModel` | `pollParticipationChartData` truncates question to 40 chars |
| UT-9.18 | `AnalyticsDashboardViewModel` | `topTopicsRows` maps null display_name to "Anonymous" |

### Integration Tests

| ID | Target | Scenario |
|----|--------|----------|
| IT-9.1 | `GET /api/events/:code/analytics` | Valid host token -- 200 with populated body |
| IT-9.2 | `GET /api/events/:code/analytics` | Missing X-Host-Token header -- 403 |
| IT-9.3 | `GET /api/events/:code/analytics` | Wrong host token value -- 403 |
| IT-9.4 | `GET /api/events/:code/analytics` | Non-existent event code -- 404 |
| IT-9.5 | `GET /api/events/:code/analytics` | Zero-activity event -- 200, all zeroes |
| IT-9.6 | `GET /api/events/:code/analytics` | Verify unique_participants uses UNION of fingerprints |
| IT-9.7 | `GET /api/events/:code/analytics` | Verify poll_participation rates computed correctly |
| IT-9.8 | `GET /api/events/:code/analytics` | Verify timeline buckets are 5-minute intervals |
| IT-9.9 | `GET /api/events/:code/analytics` | Verify top_topics capped at 10, sorted by score |
| IT-9.10 | `GET /api/events/:code/analytics` | Verify average_rating correct for RATING poll |
| IT-9.11 | Performance | 100 participants, 500 topics, 2000 votes -- response under 2000ms |

### End-to-End Tests

| ID | Scenario |
|----|----------|
| E2E-9.1 | Host navigates to analytics from host admin view -- "Analytics" link visible and clickable |
| E2E-9.2 | Unauthenticated user accesses /events/:code/admin/analytics -- redirected to host page |
| E2E-9.3 | Dashboard loads -- all four summary cards visible with numeric values |
| E2E-9.4 | Event with submitted topics and votes -- engagement timeline chart renders with data |
| E2E-9.5 | Event with no activity -- timeline shows "No activity recorded yet" message |
| E2E-9.6 | Event with polls -- poll participation chart renders a bar per poll |
| E2E-9.7 | Event with no polls -- participation chart shows empty-state message |
| E2E-9.8 | Top topics table shows up to 10 rows, ordered by score |
| E2E-9.9 | Topic with display_name -- author column shows the name |
| E2E-9.10 | Anonymous topic -- author column shows "Anonymous" |
| E2E-9.11 | Host clicks "Refresh" -- loading state appears, data updates |
| E2E-9.12 | Event with a RATING poll -- average rating card visible with value or "No responses yet" |
| E2E-9.13 | Dashboard is responsive at 768px viewport width -- all sections readable |

---

## Documentation Deliverables

| ID | Deliverable | Description |
|----|-------------|-------------|
| DOC-9.1 | OpenAPI schema | `GET /api/events/:code/analytics` endpoint fully documented with request header (`X-Host-Token`), 200 response schema (`EventAnalyticsDTO`), and 403/404 error responses |
| DOC-9.2 | `EventAnalyticsDTO` schema | All fields documented: types, units (percentages as 0.0-1.0 floats, timestamps as ISO 8601 UTC strings, ratings as floats rounded to 2 decimal places) |
| DOC-9.3 | Docstrings | `GetEventAnalyticsUseCase`, `AnalyticsRepository` port, and concrete repository implementation have full docstrings describing parameters, return values, and error conditions |
| DOC-9.4 | ViewModel JSDoc | `AnalyticsDashboardViewModel` class and all computed properties have JSDoc blocks describing the transformation applied |
| DOC-9.5 | Analytics dashboard user guide | A brief section added to the host/admin documentation (can be inline in the host view README or in `docs/`) describing what each metric means and how to interpret it |
| DOC-9.6 | Index update | `recharts` dependency documented in `package.json` and noted in frontend setup docs if a setup guide exists |

---

## Technical Notes

### Domain layer additions

```
src/domain/ports/analytics_repository.py
  class AnalyticsRepository(ABC):
    @abstractmethod
    def get_event_analytics(self, event_id: UUID) -> EventAnalyticsDTO: ...

src/application/use_cases/get_event_analytics.py
  class GetEventAnalyticsUseCase:
    def __init__(self, repo: AnalyticsRepository, event_repo: EventRepository): ...
    def execute(self, event_code: str, host_token: str) -> EventAnalyticsDTO: ...

src/application/dtos/analytics.py
  @dataclass
  class TimelineBucket:
    bucket_start: datetime
    topics_submitted: int
    votes_cast: int
    poll_responses: int

  @dataclass
  class PollParticipationSummary:
    poll_id: UUID
    poll_question: str
    poll_type: str
    responder_count: int
    rate: float
    average_rating: float | None  # only for RATING type

  @dataclass
  class TopTopicEntry:
    topic_id: UUID
    text: str
    score: int
    display_name: str | None
    status: str

  @dataclass
  class EventAnalyticsDTO:
    unique_participants: int
    total_topics: int
    total_votes: int
    total_poll_responses: int
    poll_participation: list[PollParticipationSummary]
    timeline: list[TimelineBucket]
    top_topics: list[TopTopicEntry]
```

### Infrastructure SQL design

The concrete `PostgresAnalyticsRepository` MUST use a single database session and
execute queries efficiently. Prefer aggregation in SQL over Python loops:

```sql
-- Unique participants (union of all fingerprint sources)
SELECT COUNT(DISTINCT fingerprint) FROM (
  SELECT fingerprint FROM topics WHERE event_id = :event_id
  UNION
  SELECT v.fingerprint FROM votes v
    JOIN topics t ON v.topic_id = t.id
   WHERE t.event_id = :event_id
  UNION
  SELECT pr.fingerprint FROM poll_responses pr
    JOIN polls p ON pr.poll_id = p.id
   WHERE p.event_id = :event_id
) AS all_fingerprints;

-- Timeline bucketing (topics example; replicate for votes and poll_responses)
SELECT
  DATE_TRUNC('hour', created_at)
    + FLOOR(EXTRACT(MINUTE FROM created_at) / 5) * INTERVAL '5 minutes' AS bucket,
  COUNT(*) AS topic_count
FROM topics
WHERE event_id = :event_id
GROUP BY bucket
ORDER BY bucket;
```

### Frontend charting library

Use `recharts` for both the `EngagementTimeline` (AreaChart or LineChart) and the
`PollParticipationChart` (BarChart). `recharts` is React-native and tree-shakeable.
Install via: `npm install recharts`.

If `recharts` is already a dependency from a prior phase, reuse it. Do not add a second
charting library.

### Access control

The analytics endpoint reuses the same `X-Host-Token` validation middleware from Phase 7.
No new auth infrastructure is required. The middleware MUST be applied as a FastAPI
dependency on the analytics router.

### Performance budget

The endpoint MUST respond within 2000ms for events with up to 100 participants, 500
topics, 2000 votes, and 300 poll responses (the scale target from 00-config.md). If
queries exceed 500ms in profiling, introduce a database-level view or materialized
intermediate table rather than adding a caching layer in this phase.

### Open question resolution

[?]-5 from `01-overview.md` ("Should event analytics be visible to participants after
close?") is resolved as host-only for this phase. Participant-facing post-event summaries
may be added in a follow-on PRD if demand warrants.

---

## Validation Checklist

Before marking Phase 9 complete, verify every item:

- [ ] `AnalyticsRepository` port defined in `src/domain/ports/analytics_repository.py`
- [ ] `EventAnalyticsDTO` and all sub-DTOs defined in `src/application/dtos/analytics.py`
- [ ] `GetEventAnalyticsUseCase` implemented in `src/application/use_cases/`
- [ ] `PostgresAnalyticsRepository` implemented in `src/infrastructure/repositories/`
- [ ] `GET /api/events/:code/analytics` route registered in the presentation layer
- [ ] Route requires `X-Host-Token` header; returns 403 on failure, 404 for unknown code
- [ ] `unique_participants` uses UNION of all three fingerprint sources
- [ ] `poll_participation` rate is 0.0 when unique_participants = 0
- [ ] Timeline buckets are exactly 5-minute intervals; empty buckets are omitted
- [ ] `top_topics` is capped at 10 entries, sorted by score desc then created_at asc
- [ ] RATING poll `average_rating` rounded to 2 decimal places; null when no responses
- [ ] Required database indexes verified present (topics.created_at, votes.created_at, poll_responses.created_at)
- [ ] `recharts` added to `package.json` (or confirmed present)
- [ ] `/events/:code/admin/analytics` route registered in React router
- [ ] Unauthenticated access redirects to `/events/:code/host`
- [ ] `AnalyticsDashboardViewModel` implemented with all specified computed properties
- [ ] `AnalyticsSummaryCards` renders four cards with correct IDs
- [ ] `EngagementTimeline` renders area/line chart with empty-state for zero data
- [ ] `PollParticipationChart` renders horizontal bar chart with empty-state for no polls
- [ ] `TopTopicsTable` renders with Rank, Topic, Author, Score, Status columns
- [ ] Null `display_name` shown as "Anonymous" in table Author column
- [ ] RATING poll average rating card visible per poll
- [ ] "Analytics" link added to host admin navigation with correct ID
- [ ] "Refresh" button re-fetches data and shows loading state
- [ ] All unit tests pass (UT-9.1 through UT-9.18)
- [ ] All integration tests pass (IT-9.1 through IT-9.11)
- [ ] All E2E tests pass (E2E-9.1 through E2E-9.13)
- [ ] IT-9.11 performance test confirms < 2000ms for the specified load
- [ ] OpenAPI schema documents the analytics endpoint (DOC-9.1, DOC-9.2)
- [ ] Docstrings complete on all new Python modules (DOC-9.3)
- [ ] ViewModel JSDoc complete (DOC-9.4)
- [ ] Ruff lint and format checks pass
- [ ] Pyright type checks pass with no new errors
- [ ] All existing Phase 1-8 E2E tests continue to pass (NFR-8 regression guard)
- [ ] Dashboard renders correctly at 768px viewport width (NFR-5 tablet breakpoint)
- [ ] NFR-1: Existing API p95 response time unaffected by new analytics queries
