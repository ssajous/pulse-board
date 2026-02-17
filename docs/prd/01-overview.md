# Community Pulse Board -- Overview

## Problem Statement

Teams and communities need a low-friction way to surface topics that matter most to the group. Traditional survey tools require setup, authentication, and overhead. Community Pulse Board provides an anonymous, real-time feedback surface where topics are ranked purely by collective sentiment.

## Goals

- **Anonymous topic submission**: Any visitor can submit a topic (255-character limit) without signing in or identifying themselves.
- **Upvote/downvote with community censure**: Each topic can be upvoted or downvoted. When a topic's score drops to -5 or below, it is permanently removed from the board.
- **Real-time score updates via WebSockets**: All connected clients see score changes immediately without refreshing the page.
- **Vote manipulation prevention**: Browser fingerprinting via FingerprintJS v5 limits each browser to a single vote per topic.
- **Clean onion architecture**: The codebase follows strict onion architecture with domain, application, infrastructure, and presentation layers on both backend and frontend.

## Non-Goals

- User accounts or authentication
- Comments or threads on topics
- Topic categories or tags
- Admin moderation panel
- Mobile native app
- Multi-room or channel support

## User Stories

1. **As a community member**, I want to submit a topic anonymously so my idea is judged on merit.
2. **As a community member**, I want to upvote or downvote topics so the most relevant rise to the top.
3. **As a community member**, I want to see scores update in real-time so I know what is trending now.
4. **As a community member**, I want heavily downvoted topics removed so the board stays useful.

## Architecture Overview

The project follows onion architecture (also known as clean architecture) on both the backend and frontend. Dependencies always point inward: outer layers depend on inner layers, never the reverse.

### Backend Layers (FastAPI / Python)

```
Domain (innermost)
  -> Application
    -> Infrastructure
      -> Presentation (outermost)
```

- **Domain**: Core business rules, entities (`Topic`, `Vote`), value objects, domain services, and port interfaces defined as abstract base classes. This layer has zero framework imports.
- **Application**: Use cases that orchestrate domain logic (e.g., `SubmitTopicUseCase`, `CastVoteUseCase`). Depends only on domain ports. Contains DTOs for data crossing layer boundaries.
- **Infrastructure**: Concrete implementations of domain ports -- PostgreSQL repositories via SQLAlchemy, WebSocket connection managers, FingerprintJS verification adapters. All external I/O lives here.
- **Presentation**: FastAPI route handlers, Pydantic request/response schemas, WebSocket endpoint definitions. This layer is kept thin; it only handles HTTP/WS I/O formatting and delegates to application use cases.

### Frontend Layers (React / TypeScript)

```
Domain (innermost)
  -> Application
    -> Infrastructure
      -> Presentation (outermost)
```

- **Domain**: Core business entities (`Topic`, `Vote`) and port interfaces defined as TypeScript interfaces.
- **Application**: Use-case functions (pure logic) that operate on domain entities.
- **Infrastructure**: HTTP and WebSocket client implementations that fulfill domain port interfaces.
- **Presentation**: React components and MobX ViewModels. The MVVM pattern keeps components as dumb renderers; all state and logic lives in observable ViewModels that expose computed properties and actions.

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend Framework | FastAPI | Async-first, WebSocket support, auto-docs |
| Frontend Framework | React + TypeScript | Type safety, component model |
| Build Tool | Vite | Fast HMR, modern bundling |
| State Management | MobX | MVVM pattern per project standards |
| Database | PostgreSQL | Durable, transactional, production-ready |
| Migrations | Alembic | Standard for SQLAlchemy |
| WebSocket (Backend) | Starlette built-in | No extra dependency, production-ready for single instance |
| WebSocket (Frontend) | react-use-websocket | React-idiomatic hooks, built-in reconnection |
| Browser Fingerprinting | FingerprintJS v5 (MIT) | Best maintained, 40-60% accuracy, native TS |
| Styling | Tailwind CSS | Utility-first, rapid prototyping |
| Containerization | Docker + Docker Compose | Infrastructure management per CLAUDE.md |

## Phase Summary

| Phase | Name | Description | Dependencies |
|-------|------|-------------|--------------|
| 1 | Project Foundation | Scaffolding, Docker, Makefile, folder structure | None |
| 2 | Topic Management | Topic CRUD, REST API, frontend display | Phase 1 |
| 3 | Voting System | Voting, fingerprinting, censure logic | Phase 2 |
| 4 | Real-Time WebSockets | Live score updates, re-ranking | Phase 3 |
| 5 | Testing & Quality | Unit, integration, E2E tests, linting | Phases 1-4 |
| 6 | Documentation & DevOps | ADRs, Docker prod build, README | Phases 1-4 |

## Non-Functional Requirements

| ID | Requirement | Threshold |
|----|-------------|-----------|
| NFR-1 | API response time for all CRUD operations (p95) | < 200ms |
| NFR-2 | WebSocket message delivery from vote to all connected clients | < 100ms |
| NFR-3 | Frontend initial load on a 3G connection | < 3s |
| NFR-4 | Data durability on topic submission (PostgreSQL guarantees) | Zero data loss |
| NFR-5 | WebSocket reconnection after disconnection | Within 5s |
| NFR-6 | Concurrent WebSocket connections per instance | 50 minimum |
| NFR-7 | Total unit test execution time; individual test ceiling | < 10s total; < 2s per test |
| NFR-8 | Code coverage for domain and application layers | 80% minimum |

## Open Questions

1. **Fingerprint storage**: Should fingerprint IDs be stored server-side for vote tracking, or should voting state be entirely client-managed?
2. **Data retention**: What is the desired data retention policy for topics (indefinite, TTL-based)?
3. **Rate limiting**: Should there be rate limiting on topic submissions (e.g., max 5 per hour per fingerprint)?
