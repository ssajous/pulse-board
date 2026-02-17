# 09: Real-Time Activity Pulse Indicator

## Category

Engagement & Discovery

## Complexity

Small

## Overview

Add a visual "pulse" indicator that reflects the current level of activity on the board -- a heartbeat-like animation or badge that shows how active the community is right now. This leverages the existing WebSocket infrastructure to display live engagement metrics (votes per minute, active users, recent submissions) without any new backend services.

## Problem Statement

When a user visits the board, there is no indication of whether the community is currently active. A board with 50 topics could have 100 active users voting right now, or it could be dormant. Without activity signals, users lack the social proof that encourages participation. Showing that "the community is alive" creates a sense of immediacy and motivates engagement.

Mentimeter's live audience count and Slido's activity indicator both demonstrate that simple presence signals drive higher participation rates.

## User Stories

1. **As a community member**, I want to see a visual indicator of current board activity so I know whether the community is active right now.
2. **As a community member**, I want to see how many votes have been cast recently so I can gauge engagement level.
3. **As a returning visitor**, I want to see a "pulse" animation that reflects real-time activity so the board feels alive.

## Design Considerations

### Activity Metrics

Track via the existing WebSocket connection (no new API endpoints needed):

- **Votes per minute**: count WebSocket vote events received in the last 60 seconds
- **Recent submissions**: count topic creation events in the last 5 minutes
- **Connected users**: optional, requires the backend to broadcast connection count

### Visual Design

**Pulse Indicator** (header area):
- A small animated dot/ring that pulses faster when activity is higher
- Color gradient: gray (inactive) -> green (low) -> orange (moderate) -> red (high)
- Tooltip on hover showing exact metrics: "12 votes in the last minute"

**Activity Levels**:

| Level | Votes/min | Visual |
|-------|-----------|--------|
| Dormant | 0 | Gray dot, no animation |
| Low | 1-5 | Green, slow pulse (2s) |
| Moderate | 6-15 | Orange, medium pulse (1s) |
| High | 16+ | Red, fast pulse (0.5s) |

### Frontend Architecture

- New `ActivityPulse` component in the `Header`
- Pure client-side computation: count WebSocket events within a sliding window
- No backend changes required -- piggyback on existing vote and topic WebSocket events
- `TopicsViewModel` extended with:
  - `recentVoteCount: number` computed from a rolling event buffer
  - `activityLevel: 'dormant' | 'low' | 'moderate' | 'high'` computed property
  - Event buffer: array of timestamps, pruned every 60 seconds

```typescript
// Simplified logic
get activityLevel(): ActivityLevel {
  const votesLastMinute = this.eventBuffer
    .filter(t => Date.now() - t < 60_000).length;
  if (votesLastMinute === 0) return 'dormant';
  if (votesLastMinute <= 5) return 'low';
  if (votesLastMinute <= 15) return 'moderate';
  return 'high';
}
```

### CSS Animation

```css
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

.pulse-indicator {
  animation: pulse var(--pulse-speed) ease-in-out infinite;
}
```

- Use `prefers-reduced-motion` to disable animation for accessibility (feature 06)
- Tailwind CSS `animate-pulse` utility can be used as a starting point

### Backend Enhancement (Optional)

If connected user count is desired:
- `ConnectionManager` already tracks connections
- Broadcast `{"type": "presence", "count": N}` periodically (every 30s)
- Minimal change to existing WebSocket infrastructure

## Dependencies

- Phase 4 (WebSocket) -- relies on existing WebSocket event stream
- No new backend endpoints or database changes required

## Open Questions

1. Should the pulse indicator show exact numbers or just a qualitative level?
2. Should there be a "users online" count, or does that risk making small communities feel empty?
3. Should the activity indicator be per-topic (individual topic cards) or board-wide (header only)?
