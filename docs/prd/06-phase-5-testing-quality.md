# Phase 5: Testing & Quality Assurance

## Overview

Implement comprehensive testing across all architecture layers and set up code quality tooling. Tests follow the onion architecture testing strategy: pure unit tests for domain, mocked port tests for application, integration tests with real database for infrastructure, and E2E tests with Playwright for presentation.

## Dependencies

- Phases 1-4 must be complete (all features implemented before comprehensive testing)

## Functional Requirements

### FR-5.1: Domain Layer Unit Tests

**Description**: Write pure unit tests for domain entities, value objects, and domain services. These tests have zero external dependencies and no mocks.

**Acceptance Criteria**:

- Given the Topic entity, When tested, Then all validation rules are covered (empty content, whitespace-only, >255 chars, valid content)
- Given the Vote entity, When tested, Then value constraints are covered (+1, -1, invalid values)
- Given the voting domain service, When tested, Then all 6 voting scenarios are covered (upvote new, downvote new, toggle up->down, toggle down->up, cancel upvote, cancel downvote)
- Given the censure logic, When tested, Then boundary conditions are covered (score -4 -> -5 triggers censure, score -4 -> -3 does not)
- Given all domain tests, When I run them, Then they execute in < 1 second total with zero external dependencies
- Given the test files, When I inspect their location, Then they mirror the source structure: tests/unit/domain/entities/topic_tests.py, tests/unit/domain/services/voting_service_tests.py, etc.

### FR-5.2: Application Layer Unit Tests

**Description**: Write unit tests for use cases with mocked repository ports. These tests verify orchestration logic without touching the database.

**Acceptance Criteria**:

- Given the CreateTopic use case, When tested with a mock TopicRepository, Then topic creation and validation are verified
- Given the ListTopics use case, When tested with a mock TopicRepository, Then sorting behavior is verified
- Given the CastVote use case, When tested with mock VoteRepository and TopicRepository, Then vote processing and censure triggering are verified
- Given all application tests, When I run them, Then they execute in < 2 seconds total
- Given the test files, When I inspect their location, Then they follow: tests/unit/application/use_cases/create_topic_tests.py, etc.

### FR-5.3: Infrastructure Integration Tests

**Description**: Write integration tests for repository implementations using a real PostgreSQL database (via Docker Compose).

**Acceptance Criteria**:

- Given the SQLAlchemy TopicRepository, When tested against PostgreSQL, Then CRUD operations work correctly
- Given the SQLAlchemy VoteRepository, When tested against PostgreSQL, Then vote persistence and unique constraints work
- Given the integration tests, When I run `make test-integration`, Then Docker Compose starts PostgreSQL, tests run, and containers stop
- Given the test database, When tests complete, Then test data is cleaned up (transaction rollback or truncation)
- Given the test files, When I inspect their location, Then they follow: tests/integration/infrastructure/repositories/topic_repository_tests.py, etc.

### FR-5.4: API Integration Tests

**Description**: Write integration tests for REST API endpoints using FastAPI's TestClient.

**Acceptance Criteria**:

- Given POST /api/topics with valid data, When tested, Then 201 response with topic data is returned
- Given POST /api/topics with invalid data, When tested, Then 422 response with validation errors is returned
- Given GET /api/topics, When tested, Then 200 response with sorted topics is returned
- Given POST /api/topics/{id}/votes, When tested, Then vote processing and score update work correctly
- Given GET /health, When tested, Then health status is returned
- Given the test files, When I inspect their location, Then they follow: tests/integration/presentation/api/routes/topics_tests.py, etc.

### FR-5.5: End-to-End Tests with Playwright

**Description**: Write E2E tests using Playwright that test the full user workflow through the browser.

**Acceptance Criteria**:

- Given the E2E test suite, When testing topic submission, Then: fill form -> submit -> verify topic appears in list
- Given the E2E test suite, When testing voting, Then: click upvote -> verify score increments -> click again -> verify score decrements (cancel)
- Given the E2E test suite, When testing censure, Then: downvote a topic to -5 -> verify topic disappears -> verify toast notification
- Given the E2E test suite, When testing real-time updates, Then: open two browser tabs -> vote in one -> verify score updates in the other
- Given the E2E tests, When I run `make test-e2e`, Then Playwright tests execute against the running application
- Given all interactive elements, When tested, Then they are located by ID attributes following the convention: {component}-{element}-{identifier}

### FR-5.6: Code Quality Tooling Setup

**Description**: Configure and verify Ruff (formatting + linting), Pyright (type checking), and ESLint/Prettier (frontend) as part of the development workflow.

**Acceptance Criteria**:

- Given the backend code, When I run `uv run ruff format . --check`, Then all files pass formatting (88 char line length)
- Given the backend code, When I run `uv run ruff check .`, Then no linting errors are found
- Given the backend code, When I run `uv run pyright`, Then no type errors are found
- Given the frontend code, When I run `npm run lint`, Then no linting errors are found
- Given all quality checks, When I run `make lint` (or similar), Then all checks run and pass

### FR-5.7: Test Coverage Reporting

**Description**: Set up test coverage reporting with minimum thresholds.

**Acceptance Criteria**:

- Given the test suite, When I run `make test` with coverage, Then a coverage report is generated
- Given the coverage report, When I inspect domain layer coverage, Then it is >= 90%
- Given the coverage report, When I inspect application layer coverage, Then it is >= 80%
- Given the coverage report, When I inspect overall coverage, Then it is >= 80%

## Technical Notes

- Unit tests must run quickly (individual tests < 2s per CLAUDE.md, most just a few ms)
- Unit tests must have no side effects (no database records, no message queues)
- Test file naming convention: {module}_tests.py (mirrors source structure)
- Integration tests use Docker Compose for PostgreSQL
- E2E tests require both backend and frontend running
- Use pytest for all Python tests
- Use Playwright (not Cypress) for E2E tests
