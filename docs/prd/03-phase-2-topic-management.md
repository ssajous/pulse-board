# Phase 2: Topic Management (CRUD)

## Overview

Implement the Topic entity and full create/list functionality across all architecture layers. This phase delivers a working topic board where users can submit topics and see them ranked by score.

## Dependencies

- Phase 1 (Project Foundation) must be complete

## Functional Requirements

### FR-2.1: Topic Domain Entity

**Description**: Create the Topic domain entity with business rules. The entity lives in the domain layer with zero framework dependencies.

**Acceptance Criteria**:

- Given a Topic entity, When I inspect its properties, Then it has: id (UUID), content (str), score (int), created_at (datetime)
- Given a new Topic, When it is created, Then score defaults to 0 and created_at defaults to now
- Given content exceeding 255 characters, When creating a Topic, Then a domain validation error is raised
- Given empty or whitespace-only content, When creating a Topic, Then a domain validation error is raised
- Given the Topic entity file, When I inspect imports, Then there are NO imports from FastAPI, SQLAlchemy, Pydantic, or any framework

### FR-2.2: Topic Repository Port

**Description**: Define an abstract TopicRepository interface (port) in the domain layer.

**Acceptance Criteria**:

- Given the TopicRepository port, When I inspect it, Then it defines: create(topic) -> Topic, list_active() -> list[Topic], get_by_id(id) -> Topic | None, delete(id) -> None
- Given the port, When I inspect it, Then it is an ABC (Abstract Base Class)
- Given the port, When I inspect imports, Then there are only domain-layer imports

### FR-2.3: Create Topic Use Case

**Description**: Implement the CreateTopic application use case that orchestrates topic creation through the repository port.

**Acceptance Criteria**:

- Given valid topic content, When the use case executes, Then a new Topic is persisted via the repository
- Given invalid content (empty, too long), When the use case executes, Then it raises a domain validation error without touching the repository
- Given the use case, When I inspect its constructor, Then it accepts a TopicRepository port (dependency injection)

### FR-2.4: List Topics Use Case

**Description**: Implement the ListTopics application use case that retrieves and sorts topics.

**Acceptance Criteria**:

- Given multiple topics exist, When the use case executes, Then topics are returned sorted by score descending
- Given topics with equal scores, When the use case executes, Then they are sorted by created_at descending (newest first)
- Given no topics exist, When the use case executes, Then an empty list is returned

### FR-2.5: SQLAlchemy Topic Repository

**Description**: Implement the TopicRepository port using SQLAlchemy in the infrastructure layer.

**Acceptance Criteria**:

- Given valid topic data, When create() is called, Then a row is inserted into the topics table
- Given existing topics, When list_active() is called, Then all topics with score > -5 are returned
- Given a topic ID, When get_by_id() is called, Then the matching topic is returned or None
- Given the implementation, When I inspect it, Then it maps between ORM models and domain entities

### FR-2.6: Topic REST API Endpoints

**Description**: Create REST API endpoints for topic management in the presentation layer.

**Acceptance Criteria**:

- Given valid JSON body {"content": "My topic"}, When I POST /api/topics, Then a 201 response is returned with the created topic
- Given invalid body (empty content), When I POST /api/topics, Then a 422 response with validation details is returned
- Given existing topics, When I GET /api/topics, Then a 200 response with sorted topic list is returned
- Given the API, When I inspect /docs, Then both endpoints are documented with schemas

### FR-2.7: Topic Alembic Migration

**Description**: Create an Alembic migration for the topics table.

**Acceptance Criteria**:

- Given the migration, When applied, Then a `topics` table exists with columns: id (UUID PK), content (VARCHAR 255), score (INTEGER default 0), created_at (TIMESTAMP WITH TIMEZONE)
- Given the migration, When rolled back, Then the topics table is dropped

### FR-2.8: Frontend Topic List Display

**Description**: Create a React component that displays topics sorted by score, matching the sample UI mockup.

**Acceptance Criteria**:

- Given topics from the API, When the page loads, Then topics are displayed as cards sorted by score descending
- Given a topic card, When I inspect it, Then it shows: content, score (color-coded: green positive, gray zero, red negative), timestamp
- Given a topic with score <= -3, When displayed, Then a "Risk of Removal" warning badge appears
- Given a negative score topic, When displayed, Then a progress bar toward removal is shown
- Given no topics, When the page loads, Then an empty state message is shown

### FR-2.9: Frontend Topic Submission Form

**Description**: Create a topic submission form with character limit validation.

**Acceptance Criteria**:

- Given the form, When I type content, Then a character counter shows {current}/255
- Given content exceeding 255 characters, When typing, Then the counter turns red and submit is disabled
- Given empty or whitespace-only content, When inspecting the submit button, Then it is disabled
- Given valid content, When I click "Post Topic", Then the topic is submitted via POST /api/topics
- Given a successful submission, When complete, Then the form clears and a success toast appears
- Given the form, When I inspect it, Then it has id="topic-form" and the input has id="topic-input"

### FR-2.10: MobX Topics ViewModel

**Description**: Create a TopicsViewModel using MobX that manages all topic state and business logic, following the MVVM pattern.

**Acceptance Criteria**:

- Given the ViewModel, When I inspect it, Then it has observable properties: topics (array), isLoading (boolean), error (string | null)
- Given the ViewModel, When I inspect computed properties, Then it has sortedTopics (sorted by score desc, then created_at desc)
- Given the ViewModel, When fetchTopics() is called, Then it fetches from GET /api/topics and updates the topics observable
- Given the ViewModel, When submitTopic(content) is called, Then it POSTs to /api/topics and adds the new topic to the list
- Given the React components, When I inspect them, Then they are wrapped with observer() and receive state/actions from the ViewModel only

## Technical Notes

- Domain entities must have zero framework imports
- ORM models (infrastructure) are separate from domain entities
- Use dependency injection for repository in use cases
- API schemas (Pydantic) are in presentation layer only
- Frontend components should be "dumb" -- all logic in ViewModel
