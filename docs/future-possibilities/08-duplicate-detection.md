# 08: Duplicate Detection & Topic Merging

## Category

Content Quality

## Complexity

Medium-Large

## Overview

Automatically detect when a newly submitted topic is semantically similar to an existing one and offer to merge or redirect the submitter. This prevents vote fragmentation across duplicate topics and keeps the board clean as submission volume increases.

## Problem Statement

As boards scale, multiple users independently submit topics about the same concern. Without duplicate detection, votes are split across 3-4 similar topics instead of consolidating on one. This dilutes the signal, makes the board harder to scan, and frustrates users who see redundant entries. The problem compounds over time as the topic count grows.

Platforms like IdeaScale (duplicate detection), UserVoice (idea merging), and Stack Overflow (duplicate question linking) demonstrate that duplicate management is essential for any crowdsourced content system.

## User Stories

1. **As a community member**, I want to be alerted if my topic is similar to an existing one before I submit so I can vote on the existing topic instead.
2. **As a community member**, I want to see suggested similar topics while I'm typing so I can avoid creating duplicates.
3. **As a board operator**, I want the system to flag potential duplicates so I can merge them and consolidate votes.
4. **As a community member**, I want merged topics to retain the combined vote count so no engagement is lost.

## Design Considerations

### Detection Approaches

**Approach 1: Text Similarity (MVP)**
- Use trigram similarity (`pg_trgm` PostgreSQL extension) for fuzzy text matching
- Compute similarity score between new topic text and all existing topics
- Flag as potential duplicate if similarity > 0.4 (tunable threshold)
- Fast, no external dependencies, works well for short text (topics are max 255 chars)

**Approach 2: Embedding-Based Similarity (Advanced)**
- Generate text embeddings using a lightweight model (e.g., `all-MiniLM-L6-v2` via `sentence-transformers`)
- Store embeddings in PostgreSQL with `pgvector` extension
- Cosine similarity search for semantic matching
- Catches paraphrases that trigram matching misses (e.g., "deploy process is slow" vs "CI/CD pipeline performance")

**Approach 3: Hybrid**
- Use trigram matching for real-time type-ahead suggestions (fast, low overhead)
- Use embeddings for batch duplicate detection and merge suggestions (higher quality)

### Backend Architecture

**Domain Layer**:
- `DuplicateCandidate` value object: `topic_id`, `similarity_score`, `matched_text`
- `DuplicateDetectionPort` interface: `find_similar(text, threshold) -> list[DuplicateCandidate]`
- `TopicMerge` entity: `source_topic_id`, `target_topic_id`, `merged_at`, `merged_votes_count`

**Application Layer**:
- `CheckDuplicatesUseCase`: given topic text, returns potential duplicates above threshold
- `MergeTopicsUseCase`: merges source into target, transfers votes, archives source
- Vote transfer logic: re-assign votes from source to target, handle conflicts (same fingerprint voted on both)

**Infrastructure Layer**:
- PostgreSQL `pg_trgm` extension for trigram similarity
- `similarity()` and `%` operator for fuzzy matching
- Index: `CREATE INDEX idx_topics_trgm ON topics USING gin (text gin_trgm_ops)`
- Optional: `pgvector` extension for embedding storage and similarity search

**Presentation Layer**:
- `GET /api/topics/similar?text=...` -- returns potential duplicates for given text
- `POST /api/topics/merge` -- merge two topics (operator action)
- Extend `POST /api/topics` response to include `similar_topics` when detected

### Frontend Architecture

- **Type-ahead suggestions**: As the user types in the topic form, debounced API calls check for similar topics
- `SimilarTopicsSuggestion` component shown below the input:
  - "Similar topics already exist:" with clickable links
  - "Submit anyway" button to proceed despite duplicates
- **Merge UI** (operator view): side-by-side comparison of duplicate candidates with merge button
- `TopicFormViewModel` extended with:
  - `similarTopics: DuplicateCandidate[]` observable
  - `checkDuplicates()` action triggered on input change (debounced)
  - `dismissSuggestion()` to hide suggestions and proceed

### Vote Transfer Rules

When merging topic A into topic B:
1. All votes from A are transferred to B
2. If a fingerprint voted on both A and B, keep the vote on B (target wins)
3. Topic A is archived (not deleted) with a reference to B
4. The score on B is recalculated from all transferred + original votes
5. WebSocket event broadcasts the merge to update all connected clients

## Dependencies

- Phase 2 (Topic Management) -- topic creation flow where detection integrates
- Phase 3 (Voting System) -- vote transfer during merge requires vote repository
- PostgreSQL `pg_trgm` extension (comes bundled, just needs `CREATE EXTENSION`)

## Open Questions

1. Should duplicate detection be mandatory (block submission) or advisory (suggest but allow)?
2. Who can trigger a merge -- any user, or only a designated operator?
3. What similarity threshold produces the best balance of precision and recall for 255-char topics?
4. Should merged topics show a "merged from X" indicator?
