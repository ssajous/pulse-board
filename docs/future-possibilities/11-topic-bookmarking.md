# 11: Topic Bookmarking & Personal Feed

## Category

Personalization

## Complexity

Small-Medium

## Overview

Allow users to bookmark topics they want to track and view a personalized "My Topics" feed. Bookmarks are stored locally (tied to the browser fingerprint) to maintain anonymity. This gives users a way to curate their experience without requiring accounts, providing personal value on top of the communal board.

## Problem Statement

As the board grows, users lose track of topics they care about. A topic that was interesting yesterday may have scrolled off the visible area or been buried by newer submissions. Without a way to mark and return to specific topics, users must scan the entire board each visit to find what they're following. This friction reduces repeat engagement.

Platforms like Reddit (save/bookmark), IdeaScale (follow idea), and UserVoice (subscribe to idea) all provide personal tracking mechanisms that drive return visits.

## User Stories

1. **As a community member**, I want to bookmark a topic so I can quickly find it later.
2. **As a community member**, I want to view all my bookmarked topics in a filtered view so I can focus on what matters to me.
3. **As a community member**, I want to see if a bookmarked topic's score has changed since I last viewed it so I can stay updated.
4. **As a returning visitor**, I want my bookmarks to persist across sessions so I don't lose my curated list.
5. **As a community member**, I want to remove a bookmark when I'm no longer interested so my feed stays relevant.

## Design Considerations

### Storage Approach

**Option 1: Client-side only (recommended for MVP)**
- Store bookmarked topic IDs in `localStorage`
- Zero backend changes, immediate implementation
- Limitation: bookmarks don't sync across browsers/devices
- Data structure: `pulse-board-bookmarks: ["topic-id-1", "topic-id-2", ...]`

**Option 2: Server-side with fingerprint**
- Store bookmarks in a `bookmarks` table: `fingerprint_id`, `topic_id`, `created_at`
- Survives `localStorage` clearing
- Syncs across sessions with same browser fingerprint
- Requires backend API endpoints

### Frontend Architecture

**Bookmark Button**:
- Small bookmark/flag icon on each `TopicCard`
- Toggle on/off with visual state (outlined vs. filled)
- Position: top-right corner of the card, unobtrusive

**Bookmarked Topics View**:
- Filter toggle in `TopicListHeader`: "All Topics" / "My Bookmarks"
- When active, only shows bookmarked topics (client-side filter)
- Badge showing bookmark count: "My Bookmarks (5)"
- Empty state: "No bookmarked topics. Tap the bookmark icon on any topic to track it."

**Score Change Indicator**:
- Store the last-seen score for each bookmark in `localStorage`
- On load, compare current score with last-seen: show a delta badge ("+3" or "-2")
- Clear the delta when the user views the topic (mark as "seen")

**ViewModel Integration**:
- `TopicsViewModel` extended with:
  - `bookmarkedTopicIds: Set<string>` observable (hydrated from `localStorage`)
  - `isBookmarked(topicId): boolean` computed
  - `toggleBookmark(topicId)` action
  - `bookmarkedTopics: Topic[]` computed (filtered from full list)
  - `showBookmarksOnly: boolean` observable for filter toggle
  - `bookmarkScoreDeltas: Map<topicId, number>` computed from stored vs. current scores

### Component Structure

```
topic-card/
├── TopicCard.tsx           # existing
├── TopicCardContent.tsx    # existing
├── TopicCardScore.tsx      # existing
├── TopicCardBookmark.tsx   # new - bookmark toggle button
└── index.ts
```

### WebSocket Integration

- When a vote event updates a bookmarked topic's score, the delta is automatically recalculated
- Optional: highlight bookmarked topics that changed while the user was away (visual notification)

### Data Model (if server-side)

```sql
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint_id VARCHAR(255) NOT NULL,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (fingerprint_id, topic_id)
);
```

## Dependencies

- Phase 2 (Topic Management) -- existing topic list and cards
- Phase 3 (Voting System) -- fingerprint infrastructure (if server-side storage)

## Open Questions

1. Should bookmarks be client-only (`localStorage`) or server-side (fingerprint-linked)?
2. Should there be a limit on the number of bookmarks per user?
3. Should bookmarked topics that get censured (score <= -5) be removed from bookmarks automatically, or show as "removed"?
4. Should the bookmark view be a separate page (`/bookmarks`) or a filter on the main board?
