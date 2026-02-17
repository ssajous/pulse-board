# Phase 3: Voting System & Browser Fingerprinting

## Overview

Implement the voting mechanism with upvote/downvote/toggle/cancel semantics, browser fingerprinting via FingerprintJS v5 for anonymous user identification, and community censure logic that permanently removes topics reaching score <= -5.

## Dependencies

- Phase 2 (Topic Management) must be complete

## Functional Requirements

### FR-3.1: Vote Domain Entity

**Description**: Create the Vote domain entity representing a single user's vote on a topic.

**Acceptance Criteria**:

- Given a Vote entity, When I inspect its properties, Then it has: id (UUID), topic_id (UUID), fingerprint_id (str), value (int: +1 or -1), created_at (datetime), updated_at (datetime)
- Given a Vote, When the value is set, Then only +1 (upvote) or -1 (downvote) are accepted
- Given the Vote entity file, When I inspect imports, Then there are NO framework imports

### FR-3.2: Vote Repository Port

**Description**: Define an abstract VoteRepository interface in the domain layer.

**Acceptance Criteria**:

- Given the VoteRepository port, When I inspect it, Then it defines: save(vote) -> Vote, find_by_topic_and_fingerprint(topic_id, fingerprint_id) -> Vote | None, delete(vote_id) -> None, count_by_topic(topic_id) -> int
- Given the port, When I inspect it, Then it is an ABC

### FR-3.3: Voting Business Rules (Domain Service)

**Description**: Implement voting business rules as a domain service. The rules handle upvote, downvote, toggle, and cancel semantics.

**Acceptance Criteria**:

- Given no existing vote, When a user upvotes, Then a new Vote(value=+1) is created and topic score increases by 1
- Given no existing vote, When a user downvotes, Then a new Vote(value=-1) is created and topic score decreases by 1
- Given an existing upvote, When the user upvotes again, Then the vote is cancelled (deleted) and topic score decreases by 1
- Given an existing downvote, When the user downvotes again, Then the vote is cancelled (deleted) and topic score increases by 1
- Given an existing upvote, When the user downvotes, Then the vote toggles to -1 and topic score decreases by 2
- Given an existing downvote, When the user upvotes, Then the vote toggles to +1 and topic score increases by 2

### FR-3.4: Community Censure Logic

**Description**: Implement the community censure rule: when a topic's score reaches <= -5, it is permanently removed.

**Acceptance Criteria**:

- Given a topic with score -4, When it receives a downvote (score becomes -5), Then the topic is permanently deleted from the database
- Given a censured topic, When the topic list is fetched, Then the removed topic does not appear
- Given a topic is censured, When the action completes, Then a censure event is emitted (for WebSocket notification in Phase 4)
- Given a topic with score -4, When it receives an upvote, Then the topic remains (score becomes -3) -- censure only triggers at <= -5

### FR-3.5: Cast Vote Use Case

**Description**: Implement the CastVote application use case that orchestrates the voting flow.

**Acceptance Criteria**:

- Given a valid topic_id and fingerprint_id, When CastVote executes with direction "up", Then the voting domain service processes the vote
- Given a valid topic_id and fingerprint_id, When CastVote executes with direction "down", Then the voting domain service processes the vote
- Given an invalid topic_id, When CastVote executes, Then a "topic not found" error is raised
- Given the use case, When I inspect its constructor, Then it accepts VoteRepository and TopicRepository ports via dependency injection

### FR-3.6: Vote REST API Endpoint

**Description**: Create the vote API endpoint in the presentation layer.

**Acceptance Criteria**:

- Given body {"fingerprint_id": "abc123", "direction": "up"}, When I POST /api/topics/{topic_id}/votes, Then a 200 response is returned with updated topic score
- Given body {"fingerprint_id": "abc123", "direction": "down"}, When I POST /api/topics/{topic_id}/votes, Then a 200 response is returned with updated topic score
- Given a non-existent topic_id, When I POST /api/topics/{topic_id}/votes, Then a 404 response is returned
- Given a vote that triggers censure, When the response is returned, Then it includes {"censured": true} to indicate topic removal
- Given an invalid direction (not "up" or "down"), When I POST, Then a 422 validation error is returned

### FR-3.7: FingerprintJS v5 Integration

**Description**: Integrate FingerprintJS v5 (open-source MIT version) in the frontend to generate a stable browser fingerprint for vote tracking.

**Acceptance Criteria**:

- Given a user visits the page, When FingerprintJS loads, Then a fingerprint ID is generated and stored in the application state
- Given the same browser and device, When revisiting the page, Then the same fingerprint ID is generated (within FingerprintJS accuracy limits)
- Given the fingerprint ID, When a vote is cast, Then the fingerprint ID is sent with the vote request
- Given FingerprintJS fails to load, When a user tries to vote, Then voting is disabled with an appropriate message

### FR-3.8: Vote Alembic Migration

**Description**: Create an Alembic migration for the votes table.

**Acceptance Criteria**:

- Given the migration, When applied, Then a `votes` table exists with columns: id (UUID PK), topic_id (UUID FK to topics), fingerprint_id (VARCHAR), value (INTEGER), created_at (TIMESTAMP WITH TIMEZONE), updated_at (TIMESTAMP WITH TIMEZONE)
- Given the migration, When applied, Then a unique constraint exists on (topic_id, fingerprint_id) -- one vote per user per topic
- Given the migration, When rolled back, Then the votes table is dropped

### FR-3.9: Frontend Vote Buttons with 3 Visual States

**Description**: Implement vote buttons on each topic card with three visual states reflecting the user's current vote.

**Acceptance Criteria**:

- Given no existing vote (neutral), When displayed, Then both thumbs-up and thumbs-down are gray/default
- Given the user has upvoted, When displayed, Then the thumbs-up is highlighted green and thumbs-down is default
- Given the user has downvoted, When displayed, Then the thumbs-down is highlighted red and thumbs-up is default
- Given the user clicks thumbs-up while neutral, When the click completes, Then the button changes to upvoted state (optimistic update)
- Given the user clicks thumbs-up while already upvoted, When the click completes, Then the button returns to neutral state (vote cancelled)
- Given the user clicks thumbs-down while upvoted, When the click completes, Then thumbs-down highlights red and thumbs-up returns to default (vote toggled)

### FR-3.10: MobX Voting Integration in ViewModel

**Description**: Extend the TopicsViewModel to handle voting state and actions.

**Acceptance Criteria**:

- Given the ViewModel, When I inspect it, Then it has an observable Map of userVotes: Map<topicId, voteDirection>
- Given the ViewModel, When castVote(topicId, direction) is called, Then it optimistically updates the local score and vote state
- Given a successful vote API response, When received, Then the server score replaces the optimistic score
- Given a failed vote API response, When received, Then the optimistic update is rolled back
- Given the fingerprint ID, When the ViewModel initializes, Then it stores the fingerprint for use in all vote requests

## Technical Notes

- FingerprintJS v5 is the open-source MIT version (not the commercial Pro version)
- The fingerprint ID is ephemeral (not stored server-side for privacy) -- only the vote record links topic + fingerprint
- Vote toggling and cancellation must be atomic (use database transactions)
- Optimistic UI updates improve perceived performance but must handle rollback
