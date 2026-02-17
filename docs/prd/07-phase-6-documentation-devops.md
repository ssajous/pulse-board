# Phase 6: Documentation & DevOps

## Overview

Create comprehensive documentation including Architecture Decision Records (ADRs), update the README with setup instructions, and configure Docker for production builds. This phase ensures the project is well-documented and deployable.

## Dependencies

- Phases 1-4 must be complete (all features implemented)
- Phase 5 (Testing) should be complete for CI/CD integration

## Functional Requirements

### FR-6.1: Architecture Decision Records (ADRs)

**Description**: Create ADRs documenting the key architectural decisions made for this project, using the MADR 4.0 format.

**Acceptance Criteria**:

- Given the docs/adr/ directory, When I inspect it, Then the following ADRs exist:
  - ADR-001: Frontend technology stack (React + TypeScript + Vite + Tailwind)
  - ADR-002: Backend technology stack (FastAPI + SQLAlchemy + PostgreSQL)
  - ADR-003: Browser fingerprinting approach (FingerprintJS v5 open-source)
  - ADR-004: Real-time communication (WebSockets via Starlette built-in)
  - ADR-005: State management (MobX with MVVM pattern)
- Given each ADR, When I inspect it, Then it follows MADR 4.0 format: Title, Status, Context, Decision, Consequences (positive, negative, neutral)
- Given each ADR, When I inspect the "Considered Alternatives" section, Then at least 2 alternatives are listed with pros/cons

### FR-6.2: Docker Production Build

**Description**: Create a multi-stage Dockerfile for production deployment.

**Acceptance Criteria**:

- Given the Dockerfile, When I run `make docker-build`, Then a production image is built with both backend and frontend
- Given the production image, When I run `make docker-run`, Then the application starts and serves the frontend via the backend
- Given the Dockerfile, When I inspect it, Then it uses multi-stage builds (build stage + runtime stage)
- Given the production image, When I inspect its size, Then it is < 500MB (no dev dependencies)
- Given the Dockerfile, When I inspect it, Then it follows security best practices (non-root user, minimal base image)

### FR-6.3: Docker Compose Production Configuration

**Description**: Create a docker-compose.prod.yml that runs the full application stack.

**Acceptance Criteria**:

- Given docker-compose.prod.yml, When I run it, Then PostgreSQL, and the application start together
- Given the production compose file, When I inspect it, Then it includes health checks for all services
- Given the production compose file, When I inspect it, Then environment variables are loaded from .env file
- Given the production compose file, When I inspect it, Then it includes proper restart policies

### FR-6.4: README Documentation

**Description**: Update README.md with comprehensive project documentation.

**Acceptance Criteria**:

- Given the README, When I read it, Then it includes: project description, features list, architecture overview
- Given the README, When I read the "Getting Started" section, Then it has step-by-step setup instructions for local development
- Given the README, When I read the "Development" section, Then it documents all Makefile targets
- Given the README, When I read the "Architecture" section, Then it explains the onion architecture layers
- Given the README, When I read the "API" section, Then it links to /docs for interactive API documentation
- Given the README, When I read the "Docker" section, Then it explains how to run in Docker for production

### FR-6.5: API Documentation Enhancement

**Description**: Ensure FastAPI auto-generated documentation is comprehensive and well-organized.

**Acceptance Criteria**:

- Given the /docs endpoint, When I visit it, Then all API endpoints are documented with descriptions
- Given each endpoint, When I inspect its docs, Then request/response schemas are shown with examples
- Given the API docs, When I inspect them, Then endpoints are grouped by tag (topics, votes, health)
- Given the API docs, When I inspect them, Then error responses (400, 404, 422) are documented

### FR-6.6: CI-Ready Configuration

**Description**: Prepare configuration files that enable CI/CD pipeline setup (GitHub Actions or similar).

**Acceptance Criteria**:

- Given a CI configuration file, When I inspect it, Then it defines jobs for: lint, type-check, unit-test, integration-test
- Given the CI configuration, When I inspect the test job, Then it uses Docker Compose to spin up PostgreSQL
- Given the CI configuration, When I inspect it, Then it runs on push to main and on pull requests
- Given the CI configuration, When I inspect it, Then it caches uv and npm dependencies for speed

## Technical Notes

- ADRs go in docs/adr/ directory
- Use MADR 4.0 format for ADRs (the project has a create-adr skill available)
- Multi-stage Docker builds should separate build and runtime
- Frontend should be built as static files and served by the backend in production
- README should be concise but comprehensive
- CI configuration can be GitHub Actions (.github/workflows/) as a starting point
