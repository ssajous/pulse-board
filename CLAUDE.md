# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Team

1. Use system-architect agent in plan mode when designing features or bug fixes. The planning should use the deep-research agent to find the best approach before creating the design
2. Use python-expert agent to implement python code
3. Use the frontend-developer agent when designing and building frontend code
4. Use mvvm-mobx-specialist agent for state management and setting up MVVM architecture on the frontend
5. Use quality-engineer agent to plan and write unit, integration, and end-to-end tests
6. Use the security-review skill to ensure proper security best practices on the current work branch
7. Use code-simplifier skill to clean up code before final completion


When switching from plan mode to implementation mode, use the correct agents for implementation.

## Task Management

1. When executing tasks ALWAYS try to use a subagent to perform the task
2. Try to execute tasks in parallel when dependencies allow it.

## Local Development

### Prerequisites
- Python 3.13+
- Node.js v22 LTS (use `nvm use 22`)
- uv package manager


### Backend (FastAPI with Hot Reload)
```bash
# Install dependencies
uv sync

# Create .env file with required settings (see .env.example)
cp .env.example .env

# Start backend with hot reload
make dev-backend
```
- Runs on http://localhost:8000
- API docs: http://localhost:8000/docs
- Auto-reloads on Python file changes

### Frontend (Vite with HMR)
```bash
cd frontend
npm install
npm run dev
```
- Runs on http://localhost:5173
- Auto-reloads on file changes (React Fast Refresh)

### Running Both Together
1. `make dev`

### Docker & Infrastructure

All infrastructure dependencies (databases, message queues, caches, etc.) are managed through Docker Compose. Never install infrastructure services directly on the host machine.

**Prerequisites**:
- Docker Desktop or Docker Engine with Compose plugin
- All infrastructure defined in `docker-compose.yml`

**Makefile as Single Entry Point**:
The Makefile is the canonical interface for all development tasks. All common operations should be accessible via make targets:

| Task | Command |
|------|---------|
| Start application | `make dev` or `make run` |
| Start backend only | `make dev-backend` |
| Start frontend only | `make dev-frontend` |
| Run unit tests | `make test` or `make test-unit` |
| Run integration tests | `make test-integration` |
| Run all tests | `make test-all` |
| Run end-to-end tests | `make test-e2e` |
| Start infrastructure | `make infra-up` |
| Stop infrastructure | `make infra-down` |
| Full Docker build | `make docker-build` |
| Run in Docker | `make docker-run` |
| Clean up | `make clean` |
| Show version | `make version` |
| Bump version | `make version-patch` / `make version-minor` / `make version-major` |

**Rules**:
- All new automation tasks MUST be added to the Makefile
- Document each target with a help comment: `target: ## Description`
- Use `make help` to list all available targets
- Infrastructure should start automatically when running `make dev`
- Tests requiring infrastructure should use `docker-compose` to spin up dependencies
- Version management uses semantic versioning via Makefile targets

**Docker Compose Structure**:
```yaml
services:
  app:           # Main application (optional for local dev)
  db:            # Database (PostgreSQL, etc.)
  redis:         # Cache/session store
  # ... other infrastructure services
```

## Core Development Rules

1. Code Quality
   - Type hints required for all code
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum
   - Proper onion architecture is maintained

2. Testing Requirements
   - Coverage: test edge cases and errors
   - Code follows pythonic PEP 8 guidelines
   - New features require tests
   - Bug fixes require regression tests
   - Unit tests run quickly with no test running longer than 2 seconds, with most just a few ms.
   - Unit tests should not have side effects and cause any database records to be created, messages to be placed on a queue, etc.
   - Unit test and integration tests should be setup in a folder structure that mirrors the code they are testing. 
     The files should be named so it's clear what code file they are testing. For example to test 
     src/spotify_downloader/models/track.py there should be a test file in tests/unit/spotify_downloader/models/track_tests.py.
   - Tests should all pass with no warnings or errors

3. Code Style
    - PEP 8 naming (snake_case for functions/variables)
    - Class names in PascalCase
    - Constants in UPPER_SNAKE_CASE
    - Document with docstrings
    - Use f-strings for formatting
4. Package Management
   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uv run tool`
   - Installing dependencies: `uv sync`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

5. Onion Architecture (Clean Architecture)

   **Core Principle**: Dependencies only point inward - outer layers depend on inner layers, never the reverse.

   **Layer Structure (Inner to Outer)**:
   - **Domain**: Core business rules, entities, value objects, domain services, port interfaces (ABCs)
   - **Application**: Use cases, commands/queries, DTOs - orchestrates domain logic
   - **Infrastructure**: Implements ports (repositories, external APIs, database adapters)
   - **Presentation**: API routes, request/response schemas, UI components

   **Python/FastAPI Backend Structure**:
   ```
   src/
   ├── domain/
   │   ├── entities/       # Business objects with identity
   │   ├── value_objects/  # Immutable, identity-less objects
   │   ├── services/       # Domain services (pure business logic)
   │   └── ports/          # Abstract interfaces (ABC)
   ├── application/
   │   ├── use_cases/      # Application-specific business rules
   │   └── dtos/           # Data transfer objects
   ├── infrastructure/
   │   ├── repositories/   # Database implementations
   │   └── external/       # Third-party API adapters
   └── presentation/
       ├── api/routes/     # FastAPI router endpoints
       └── api/schemas/    # Pydantic request/response models
   ```

   **React/TypeScript Frontend Structure**:
   ```
   src/
   ├── domain/
   │   ├── entities/       # Core business objects
   │   └── ports/          # TypeScript interfaces
   ├── application/
   │   └── use-cases/      # Application logic (pure functions)
   ├── infrastructure/
   │   └── api/            # HTTP client implementations
   └── presentation/
       ├── components/     # React UI components
       └── hooks/          # React hooks (can act as adapters)
   ```

   **Key Rules**:
   - Domain layer has NO framework imports (no FastAPI, no SQLAlchemy, no Pydantic)
   - Define interfaces (ports) in inner layers; implement in outer layers
   - Use cases depend on port abstractions, not concrete implementations
   - Inject dependencies at runtime via dependency injection
   - Keep presentation layer thin - only I/O formatting
   - ORM models are separate from domain entities

   **Testing by Layer**:
   - Domain: Pure unit tests, no mocks needed (fastest)
   - Application: Unit tests with mocked ports
   - Infrastructure: Integration tests with real database/services
   - Presentation: E2E tests

   **Common Pitfalls to Avoid**:
   - Importing framework code into domain layer
   - Business logic in controllers/routes
   - Direct database access in use cases (use repository ports)
   - Using ORM entities as domain entities
   - Over-engineering for small projects

6. MVVM on the frontend. 
   - Use MOBX to create MVVM-style view models that handle all state and logic for the React components. 
   - The React components should be as dumb as possible and only responsible for rendering the UI based on the state and actions provided by the view models.
   - Make intelligent use of calculated properties and reactions in the view models so the application only cares about state changes. The view model will handle all the side-effects from those core state chantes


## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organization**: Balance file organization with simplicity - use an appropriate number of files for the project scale
- **Hardcode Nothing**: Any configuration values should be properly loaded from configuration objects that are populated with environment variables
- **12 Factor**: Follow best-practices for building 12-factor application as this will be deployed using docker and likely kubernetes.

## Python Tools

## Code Formatting

1. Ruff
   - Format: `uv run ruff format .`
   - Check: `uv run ruff check .`
   - Fix: `uv run ruff check . --fix`
   - Critical issues:
     - Line length (88 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

2. Type Checking
   - Tool: `uv run pyright`
   - Requirements:
     - Explicit None checks for Optional
     - Type narrowing for strings
     - Version warnings can be ignored if checks pass

## Back End Tools

1. FastAPI. The backend should be written in Python using FastAPI
2. Any File upload capability should use Multipart file uploads from the front end.

## Front End Tools

1. React. The frontend should be written in react using Typescript.
2. Tailwind CSS
   - Use tailwindcss for all front-end components and page layout
   - Follow web standards and best practices
   - Use Tailwind docs for guidance and advice on how to use it https://tailwindcss.com/docs and what are the available building blocks
   - Use existing Tailwind css classes, don't create redundant CSS. Use available tools or variable declaration for color scheme and theme. Look and feel should be DRY
3. Use nvm to manage node version and make sure to use version 22 LTS

## Frontend Component Patterns

### Component Decomposition
- Components exceeding 100 lines should be decomposed into sub-components
- Use folder structure with barrel exports: `component-name/index.ts`
- Sub-components prefixed with parent name: `TypeFilterTrigger`, `TypeFilterDropdown`
- Use `memo()` for sub-components receiving stable props
- Use `forwardRef` when refs need to be passed to child components
- Use MVVM pattern with MobX for state management, keeping components as dumb as possible
- ViewModels handle all state and logic, components only render based on ViewModel state and actions

### ID Attributes for E2E Testing
- Convention: `{component}-{element}-{optional-identifier}`
- Required on: form inputs, buttons, interactive containers, list items, navigation
- Dynamic IDs use template literals: `` id={`result-card-${id}`} ``
- Examples:
  - `id="search-form"` - Form container
  - `id="search-input"` - Search input field
  - `id="type-filter-trigger"` - Filter dropdown trigger
  - `id="type-filter-option-Feat"` - Dynamic type option
  - `id="result-card-abc123"` - Dynamic result card
  - `id="sidebar"` - Sidebar panel

### Component Folder Structure
```
components/
  search/
    search-bar/
      SearchBar.tsx         # Main orchestrator
      SearchInput.tsx       # Sub-component
      SearchSubmitButton.tsx
      index.ts              # Barrel export
    type-filter/
      TypeFilter.tsx
      TypeFilterTrigger.tsx
      TypeFilterDropdown.tsx
      index.ts
    result-card/
      ResultCard.tsx
      ResultCardHeader.tsx
      ResultCardContent.tsx
      index.ts
```

### Testing Approach
- Semantic queries first (getByRole, getByText)
- ID selectors for e2e tests (Playwright/Cypress): `document.getElementById()`
- Test sub-components independently
- Mock parent components when testing children

## Git

1. Do NOT mention Claude Code in the commit messages
2. Do NOT add co-authors in commit 
3. Do NOT amend commits. New changes must be a new commit. Make no assumptions about when changes may have been pushed to a remote
4. ALWAYS Commit to git after the completion of each task. Commits should have detailed commit messages.
5. Use conventional commit messages with a clear type and scope, e.g. `feat(auth): add JWT token refresh endpoint`
6. Only push up to branches other than main
7. NEVER Commit to main
8. If the current branch is main, create a feature or fix branch for the current work
9. NEVER merge to main, all merging into main should be handled by Pull Requests
10. Pull Request approval and merging is ALWAYS handled by a human
11. Prior to creating a PR, ensure that all code quality checks pass. 
    - All unit, integration and e2e tests pass. 
    - Code simplifier has been run 
    - Secruity review has been completed with no critical issues. 
    - The PR description should be detailed and include the motivation for the change, a description of the change, and any relevant context or screenshots.
