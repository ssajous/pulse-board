# 02: Emoji Reactions Beyond Binary Voting

## Category

Collaboration & Content Quality

## Complexity

Medium

## Overview

Extend the current binary upvote/downvote system with a set of curated emoji reactions (e.g., fire, lightbulb, heart, question mark, warning) that allow users to express nuanced sentiment without requiring text comments or user accounts. This provides richer feedback signals while preserving Pulse Board's anonymous, low-friction design.

## Problem Statement

Binary voting captures direction (agree/disagree) but not sentiment type. A topic about a critical production issue and a topic about a fun team outing might both receive upvotes, but for very different reasons. Without richer feedback mechanisms, board operators and community members cannot distinguish between urgency, enthusiasm, curiosity, and concern.

Platforms like Slido (audience reactions), Mentimeter (emoji scales), and GitHub (issue reactions) have shown that lightweight emoji reactions significantly increase engagement and provide actionable signal without the overhead of comments.

## User Stories

1. **As a community member**, I want to react to a topic with a specific emoji so I can express that something is urgent (fire), insightful (lightbulb), or concerning (warning) without writing a comment.
2. **As a community member**, I want to see aggregated reaction counts on each topic so I can quickly gauge the community's sentiment type.
3. **As a board viewer**, I want to see which reactions are most common on a topic so I can understand the community's response at a glance.
4. **As a community member**, I want to toggle my reaction off if I change my mind, similar to how voting works today.

## Design Considerations

### Reaction Set

Use a curated, fixed set of 5-6 reactions to keep the UI clean and prevent emoji overload:

| Emoji | Meaning | Use Case |
|-------|---------|----------|
| Fire | Hot/Urgent | Time-sensitive or trending topics |
| Lightbulb | Insightful | Good ideas, novel thinking |
| Heart | Love | Strong positive sentiment |
| Question | Curious | Wants more discussion |
| Warning | Concern | Potential issues or risks |
| Celebration | Celebrate | Milestones, achievements |

### Backend Architecture

**Domain Layer**:
- New `Reaction` entity: `id`, `topic_id`, `fingerprint_id`, `emoji_type` (enum), `created_at`
- `ReactionRepositoryPort` ABC with: `save()`, `delete()`, `find_by_topic_and_fingerprint()`, `count_by_topic_grouped()`
- Unique constraint: one reaction of each type per fingerprint per topic

**Application Layer**:
- `AddReactionUseCase`: validates emoji type, checks for existing reaction, creates or toggles
- Returns updated reaction counts for the topic

**Infrastructure Layer**:
- `reactions` database table with migration
- SQLAlchemy model mapping

**Presentation Layer**:
- `POST /api/topics/{topic_id}/reactions` with body `{"fingerprint_id": "...", "emoji_type": "fire"}`
- Response includes updated reaction counts: `{"fire": 12, "lightbulb": 5, ...}`

### Frontend Architecture

- `ReactionBar` sub-component within `TopicCard`
- Each reaction shown as emoji + count, highlighted if the current user has reacted
- Click to toggle reaction on/off (optimistic update, same pattern as voting)
- `TopicsViewModel` extended with `reactions: Map<topicId, ReactionCounts>` observable
- Reactions broadcast via WebSocket for real-time updates

### Relationship with Existing Voting

Reactions are **independent** from upvote/downvote. A user can both vote and react. Reactions do not affect the topic score or censure logic. This keeps the existing voting system clean and adds a supplementary signal layer.

## Dependencies

- Phase 3 (Voting System) -- follows the same fingerprint-based, toggle-on/off pattern
- Phase 4 (WebSocket) -- for real-time reaction count broadcasts

## Open Questions

1. Should users be allowed to add multiple different reactions to the same topic, or limited to one reaction type per topic?
2. Should reaction counts be visible to everyone, or only shown in aggregate (e.g., "12 reactions" without breakdown)?
3. Should there be a way to filter or sort topics by reaction type (e.g., "show me all fire topics")?
