# 01: Trending & Smart Sort Algorithms

## Category

Engagement & Discovery

## Complexity

Medium

## Overview

Replace the current static score-based ordering with intelligent sorting algorithms that surface trending, recently active, and time-weighted topics. This gives users multiple lenses to view the board and prevents older high-score topics from permanently dominating the feed.

## Problem Statement

The current board sorts topics by raw vote score. This creates a "rich get richer" dynamic where early topics accumulate votes and remain at the top indefinitely, while newer submissions struggle for visibility regardless of their relevance. Communities need sorting that reflects recency and momentum, not just total score.

Platforms like Reddit, Hacker News, and Slido have demonstrated that time-decay algorithms dramatically improve content discovery and sustained engagement.

## User Stories

1. **As a community member**, I want to sort topics by "trending" so I can see what is gaining momentum right now, not just what was popular earlier.
2. **As a community member**, I want to sort by "newest" so I can find fresh topics that haven't had time to accumulate votes.
3. **As a community member**, I want the default sort to balance recency and score so the board feels dynamic every time I visit.
4. **As a returning visitor**, I want to see which topics gained the most votes since my last visit so I can catch up quickly.

## Design Considerations

### Sorting Algorithms

**Hot/Trending (Reddit-inspired)**:
```
score = log10(max(|votes|, 1)) + (created_at_epoch / 45000)
```
This formula gives a logarithmic weight to votes and a linear weight to time, so newer topics with modest engagement can compete with older topics that have high scores.

**Wilson Score (confidence-based)**:
For boards with high traffic, Wilson score ranking provides a statistically sound way to rank items by the lower bound of their confidence interval, preventing items with few votes from ranking disproportionately high.

**Time-Decay**:
```
decayed_score = raw_score * e^(-lambda * hours_since_creation)
```
A simple exponential decay that reduces score influence over time. The decay constant (lambda) controls how aggressively old topics lose rank.

### Backend Architecture

- Add a `sort` query parameter to `GET /api/topics` accepting: `score` (default, current behavior), `trending`, `newest`, `active`
- Compute trending scores server-side to avoid client-side date drift
- Cache trending scores with short TTL (30-60 seconds) since they change gradually
- Domain layer: Add a `SortStrategy` port interface; implement concrete strategies in infrastructure

### Frontend Architecture

- Add a sort selector component in the `TopicListHeader`
- Store selected sort preference in `TopicsViewModel` as an observable
- Persist sort preference in `localStorage` so it survives page reloads
- Re-fetch topics when sort changes (or re-sort client-side for small boards)

### WebSocket Integration

- When a vote arrives via WebSocket, re-apply the active sort algorithm client-side
- For trending sort, periodically re-sort (every 30s) since time decay changes rankings even without new votes

## Dependencies

- Phase 2 (Topic Management) -- existing topic listing endpoint
- Phase 4 (WebSocket) -- for real-time re-sorting on vote events

## Open Questions

1. Should the trending algorithm parameters (decay rate, time weight) be configurable per board instance?
2. Should the API pre-compute and store trending scores, or compute them at query time?
3. Is client-side re-sorting acceptable for boards under 100 topics, or should all sorting be server-authoritative?
