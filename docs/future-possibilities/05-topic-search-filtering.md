# 05: Topic Search & Text Filtering

## Category

Engagement & Discovery

## Complexity

Small

## Overview

Add a search bar and text filtering capability to the topic list, allowing users to quickly find topics by keyword. As the board grows beyond 20-30 topics, scrolling through the full list becomes impractical. Real-time client-side filtering provides instant results for small-to-medium boards.

## Problem Statement

The current board displays all topics in a single sorted list with no way to search or filter. As the number of topics grows, users cannot efficiently locate a specific topic they want to vote on or check. This friction discourages engagement -- if a user can't quickly find a relevant topic, they're less likely to participate.

Every major feedback platform (Slido, IdeaScale, UserVoice, Reddit) provides search as a fundamental navigation tool.

## User Stories

1. **As a community member**, I want to type a keyword and instantly see matching topics so I can find what I'm looking for without scrolling.
2. **As a community member**, I want the search to filter in real-time as I type so I get immediate feedback.
3. **As a community member**, I want to clear the search and see all topics again with a single action.
4. **As a community member**, I want the search to match against the full topic text so partial matches are found.

## Design Considerations

### Search Approach

**Client-side filtering** (recommended for MVP):
- Filter the existing in-memory topic list using a case-insensitive substring match
- No additional API calls or backend changes needed
- Instant response as the user types
- Scales well for boards with up to ~500 topics

**Server-side search** (future enhancement):
- `GET /api/topics?q=keyword` with PostgreSQL `ILIKE` or full-text search
- Required when the board exceeds what can be loaded in a single page
- Consider `pg_trgm` extension for fuzzy matching

### Frontend Architecture

- New `SearchBar` component in the `TopicListHeader` area
- Input with debounce (150-200ms) to avoid excessive re-renders
- `TopicsViewModel` extended with:
  - `searchQuery: string` observable
  - `filteredTopics: Topic[]` computed property that applies the search filter
  - The existing topic list rendering uses `filteredTopics` instead of the raw list

```
TopicListHeader
├── SearchBar (input + clear button)
├── SortSelector (from feature 01, future)
└── TopicCount ("showing 5 of 42 topics")
```

- Clear button (X icon) visible when search has text
- Show result count: "Showing X of Y topics"
- Empty state when no topics match: "No topics match your search"

### Keyboard Shortcuts

- `/` or `Ctrl+K` to focus the search bar (standard convention)
- `Escape` to clear search and unfocus
- These integrate naturally with the accessibility feature (feature 06)

### WebSocket Integration

- New topics arriving via WebSocket should be included in search results if they match the current query
- Removed topics (censured) should be removed from filtered results

## Dependencies

- Phase 2 (Topic Management) -- existing topic list and ViewModel

## Open Questions

1. Should search highlight matching text within topic cards?
2. Should there be a minimum character count before filtering activates (e.g., 2 characters)?
3. Should search history be persisted in `localStorage` for returning users?
