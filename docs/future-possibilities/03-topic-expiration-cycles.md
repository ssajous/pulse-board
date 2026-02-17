# 03: Topic Expiration & Pulse Cycles

## Category

Engagement & Content Quality

## Complexity

Medium

## Overview

Introduce time-based topic lifecycle management through configurable expiration periods and recurring "pulse cycles." Topics automatically expire after a set duration, and the board can operate in cycles (daily, weekly, sprint-aligned) where each cycle starts fresh. This keeps the board relevant and prevents stale topics from cluttering the view.

## Problem Statement

Without expiration, the board accumulates topics indefinitely. Over time, resolved issues, completed initiatives, and outdated concerns remain visible alongside current topics. This reduces the board's signal-to-noise ratio and makes it harder for users to identify what matters right now. Communities that use Pulse Board for recurring check-ins (standups, retros, sprint planning) need a way to reset the board periodically.

Platforms like IdeaScale (campaign-based cycles), Slido (event-scoped sessions), and Mentimeter (session-based polling) all scope content to time windows to maintain relevance.

## User Stories

1. **As a board operator**, I want to set a topic expiration period (e.g., 7 days) so stale topics are automatically archived.
2. **As a community member**, I want to see how much time a topic has before it expires so I can prioritize my engagement.
3. **As a board operator**, I want to start a new pulse cycle (e.g., weekly retro) so the board resets and previous topics are archived but not deleted.
4. **As a returning visitor**, I want to browse past pulse cycles so I can see historical topics and trends.
5. **As a community member**, I want expiring topics to be visually indicated so I know which ones are about to disappear.

## Design Considerations

### Expiration Model

**Topic-level TTL**:
- Add `expires_at` (nullable `datetime`) to the `Topic` entity
- When set, topics are excluded from the active feed after expiration
- Expired topics move to an "archived" state rather than being deleted

**Pulse Cycles**:
- New `PulseCycle` entity: `id`, `name`, `started_at`, `ended_at`, `status` (active/completed)
- Topics belong to a cycle via `cycle_id` foreign key (nullable for backwards compatibility)
- Only one cycle can be active at a time
- Ending a cycle archives all its topics and optionally starts a new one

### Backend Architecture

**Domain Layer**:
- `PulseCycle` entity with lifecycle methods: `start()`, `end()`, `is_active`
- Extend `Topic` entity with `expires_at` and `cycle_id` fields
- `PulseCycleRepositoryPort` for cycle CRUD
- Domain service for cycle transitions

**Application Layer**:
- `CreatePulseCycleUseCase`: starts a new cycle, ends the current one
- `ArchiveExpiredTopicsUseCase`: batch operation to archive expired topics
- Modify `ListTopicsUseCase` to filter by active cycle and non-expired status

**Infrastructure Layer**:
- Background task (FastAPI `BackgroundTasks` or scheduled job) to check for expired topics periodically
- Database migration adding `expires_at` to topics and `pulse_cycles` table

**Presentation Layer**:
- `GET /api/cycles` -- list all cycles with topic counts
- `POST /api/cycles` -- start a new cycle
- `GET /api/cycles/{id}/topics` -- list topics from a specific cycle
- Extend `GET /api/topics` with `?cycle=current` filter (default)

### Frontend Architecture

- Cycle selector in the header showing the active cycle name and duration
- Countdown or "time remaining" badge on topic cards when expiration is set
- Visual fade-out effect for topics approaching expiration (e.g., reduced opacity in last 10% of TTL)
- Archive browser for viewing past cycles
- `PulseCycleViewModel` managing cycle state and transitions

### WebSocket Integration

- Broadcast `topic_expired` events when topics are archived
- Broadcast `cycle_started` and `cycle_ended` events for cycle transitions
- Connected clients automatically filter out expired topics without page refresh

## Dependencies

- Phase 2 (Topic Management) -- extends the existing topic entity
- Phase 4 (WebSocket) -- for real-time expiration and cycle events

## Open Questions

1. Should expiration be per-topic (set by submitter) or board-wide (set by operator)?
2. Should archived topics be viewable by all users, or only by board operators?
3. How should vote scores and reactions carry over (or not) between cycles?
4. Should there be an option to "carry forward" a topic from one cycle to the next?
