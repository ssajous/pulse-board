# 04: Community Pulse Analytics Dashboard

## Category

Analytics & Insights

## Complexity

Large

## Overview

Build a read-only analytics dashboard that visualizes community engagement patterns, voting trends, topic velocity, and participation metrics over time. This provides board operators and community leaders with aggregate insights into what the community cares about and how engagement evolves.

## Problem Statement

The current board shows a real-time snapshot of topics and scores but provides no historical perspective. Board operators cannot answer questions like: "How many topics were submitted this week vs. last week?", "What time of day sees the most voting activity?", or "Is community engagement trending up or down?" Without analytics, the board is a transient tool rather than a source of actionable community intelligence.

Platforms like Slido (post-event analytics), Polis (consensus reports), and IdeaScale (idea funnel analytics) demonstrate that analytics transform feedback tools from ephemeral to strategic.

## User Stories

1. **As a board operator**, I want to see total topics submitted and votes cast over a time period so I can measure community engagement.
2. **As a board operator**, I want to see a time-series chart of voting activity so I can identify when the community is most active.
3. **As a board operator**, I want to see which topics received the most engagement (votes + reactions) so I can understand community priorities.
4. **As a community member**, I want to see a "board health" indicator (active users, topics per day) so I know the community is vibrant.
5. **As a board operator**, I want to export analytics data so I can include it in reports and presentations.

## Design Considerations

### Metrics to Track

**Engagement Metrics**:
- Topics submitted per time period (day/week/month)
- Votes cast per time period
- Unique fingerprints active per time period (proxy for unique users)
- Average votes per topic
- Topic censure rate (percentage of topics that reach -5)

**Content Metrics**:
- Top topics by score (all-time and per period)
- Most controversial topics (high vote count but near-zero score)
- Average topic lifespan (time from creation to last vote)
- Topic submission rate trend (growing/declining)

**Temporal Metrics**:
- Voting activity heatmap by hour-of-day and day-of-week
- Peak engagement windows
- Time-to-first-vote for new topics

### Backend Architecture

**Domain Layer**:
- `AnalyticsSnapshot` value object containing computed metrics
- `AnalyticsPort` interface for querying aggregate data
- No business logic mutations -- analytics is purely read-only

**Application Layer**:
- `GetEngagementMetricsUseCase`: returns metrics for a date range
- `GetTopicInsightsUseCase`: returns per-topic analytics
- `GetTemporalPatternsUseCase`: returns time-based activity patterns

**Infrastructure Layer**:
- SQL queries with aggregate functions (COUNT, AVG, GROUP BY) against existing tables
- Consider materialized views or summary tables for expensive queries
- Optional: time-series data collection for fine-grained temporal analysis

**Presentation Layer**:
- `GET /api/analytics/engagement?from=...&to=...` -- engagement metrics
- `GET /api/analytics/topics/insights` -- per-topic analytics
- `GET /api/analytics/temporal` -- time-based patterns
- `GET /api/analytics/export?format=csv` -- data export

### Frontend Architecture

- Dedicated `/analytics` route (separate from the main board view)
- Chart library: Recharts (React-native, composable, lightweight)
- Dashboard layout:
  - Top row: KPI cards (total topics, total votes, active users, censure rate)
  - Middle row: Time-series line chart of engagement over time
  - Bottom row: Top topics table + activity heatmap
- `AnalyticsViewModel` with:
  - Observable date range filter
  - Computed metrics from API responses
  - Loading and error states
  - Export action

### Privacy Considerations

- Analytics must never expose individual fingerprint IDs or per-user behavior
- All metrics are aggregate (minimum group size of 5 for any breakdown)
- No tracking of individual user journeys across topics
- Export data contains only aggregate counts, never raw vote records

## Dependencies

- Phase 2 (Topic Management) -- topics data source
- Phase 3 (Voting System) -- vote data source
- Phase 5 (Testing) -- test coverage for aggregate queries

## Open Questions

1. Should analytics be accessible to everyone or restricted to a board operator role (which would require some form of authentication)?
2. What chart library best fits the project? Recharts, Nivo, and Victory are all viable React options.
3. Should analytics data be computed on-demand or pre-aggregated on a schedule?
4. What is the minimum data volume needed before analytics becomes meaningful?
