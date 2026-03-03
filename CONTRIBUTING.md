# Contributing to Pulse Board

Thank you for your interest in contributing to Pulse Board. This guide covers the branch strategy, commit conventions, pull request process, and quality standards the project follows.

## Getting Started

Set up your local development environment before making changes:

- **[Getting Started Guide](docs/guides/getting-started.md)** -- Install prerequisites and run the application in under 10 minutes.
- **Development Setup** -- See the [Local Development](#quick-reference) section below for the commands you will use most often.

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.13+ | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js | 22 LTS | Install via [nvm](https://github.com/nvm-sh/nvm), then `nvm install 22` |
| uv | Latest | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Docker | Latest | [docs.docker.com/get-docker](https://docs.docker.com/get-started/get-docker/) |

### Quick Reference

```bash
# Install dependencies
uv sync
cd frontend && nvm use 22 && npm install && cd ..

# Start everything (backend + frontend + PostgreSQL)
make dev

# Run all tests
make test-all

# List all available make targets
make help
```

## Branch Strategy

The `main` branch is protected. Never commit directly to it.

| Branch prefix | Purpose | Example |
|---------------|---------|---------|
| `feat/` | New features | `feat/word-cloud-polls` |
| `fix/` | Bug fixes | `fix/duplicate-vote-prevention` |
| `refactor/` | Code restructuring | `refactor/simplify-vote-counting` |
| `test/` | Test additions or fixes | `test/poll-activation-e2e` |
| `docs/` | Documentation changes | `docs/contributing-guide` |
| `chore/` | Tooling and config changes | `chore/upgrade-playwright` |

### Workflow

1. Create a branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```
2. Make your changes and commit incrementally.
3. Push your branch and open a pull request.
4. A human reviewer approves and merges the PR. Contributors do not merge their own PRs.

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/) with a type and scope:

```
type(scope): description
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | Add a new feature |
| `fix` | Fix a bug |
| `refactor` | Restructure code without changing behavior |
| `test` | Add or update tests |
| `docs` | Update documentation |
| `chore` | Tooling, dependencies, CI configuration |
| `perf` | Improve performance |
| `ci` | CI/CD pipeline changes |

### Examples

```
feat(polls): add multiple choice poll support
fix(voting): prevent duplicate votes on same poll
test(e2e): add poll activation tests
refactor(topics): simplify vote counting logic
docs(contributing): add branch strategy section
chore(deps): upgrade FastAPI to 0.115
```

### Guidelines

- Keep commits atomic and focused. Each commit should represent one logical change.
- Write the subject line in imperative mood ("add feature", not "added feature").
- Use the commit body to explain **why** the change was made, not just what changed.
- Do not amend previous commits. Create new commits for new changes.

## Pull Request Process

### Before Opening a PR

Complete all of these checks locally:

1. **Run all tests:**
   ```bash
   make test-all
   make test-e2e
   ```

2. **Run code quality checks:**
   ```bash
   make lint
   ```

3. **Auto-format if needed:**
   ```bash
   make format
   ```

4. Verify there are no test warnings or failures in the output.

### Writing the PR Description

Include the following sections in every pull request:

- **Motivation** -- Why is this change needed?
- **Changes** -- What did you change? Summarize the approach.
- **Test plan** -- How did you verify the change works? List specific tests added or manual verification steps.
- **Screenshots** -- Include screenshots for any UI changes.

### Review and Merge

- A human reviewer must approve the PR before it merges.
- PRs are squash-merged to `main` to maintain a clean commit history.
- Address all review feedback with new commits (do not force-push or amend).

## Code Quality Requirements

All contributed code must meet these standards:

- **Type hints** on all Python function signatures and return types.
- **Docstrings** on all public APIs (classes, functions, methods).
- **88-character line limit** enforced by Ruff.
- **No test warnings** -- all tests pass cleanly.
- **80% code coverage** minimum. Builds fail below this threshold.

### Backend Style

| Convention | Example |
|------------|---------|
| Functions and variables | `snake_case` |
| Classes | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |
| String formatting | f-strings |

### Frontend Style

| Convention | Example |
|------------|---------|
| Components | `PascalCase` (`TopicCard.tsx`) |
| ViewModels | `PascalCase` (`TopicsViewModel.ts`) |
| Files and folders | `kebab-case` (`search-bar/`) |
| Variables and functions | `camelCase` |

### Linting and Formatting Tools

| Tool | Purpose | Command |
|------|---------|---------|
| Ruff | Python linting and formatting | `make lint` / `make format` |
| Pyright | Python type checking | `make lint` (included) |
| ESLint | TypeScript/React linting | `make lint` (included) |

## Testing Requirements

Every contribution must include appropriate tests:

- **New features** require unit tests and, when applicable, integration or E2E tests.
- **Bug fixes** require a regression test that fails without the fix.

### Test Types

| Type | Location | Command | Infrastructure |
|------|----------|---------|----------------|
| Backend unit | `tests/unit/` | `make test` | None |
| Frontend unit | `frontend/src/**/__tests__/` | `make test-frontend` | None |
| Integration | `tests/integration/` | `make test-integration` | PostgreSQL (Docker) |
| End-to-end | `tests/e2e/` | `make test-e2e` | Full stack |

### Test Standards

- Unit tests run in under 2 seconds total. Individual tests complete in milliseconds.
- Unit tests produce no side effects: no database writes, no network calls, no queue messages.
- Integration tests run against real PostgreSQL via Docker.
- E2E tests use Playwright with two-browser fixtures to verify real-time WebSocket behavior.
- Test files mirror the source tree structure. See [Test Conventions](docs/testing/test-conventions.md) for naming rules and patterns.

For full details on the testing strategy, architecture, and conventions, see:

- **[Testing Strategy](docs/testing/testing-strategy.md)** -- Why the project tests things the way it does.
- **[Test Conventions](docs/testing/test-conventions.md)** -- File organization, naming, patterns, and anti-patterns.

## Architecture

Both the backend and frontend follow **onion architecture** (clean architecture). Dependencies point inward -- outer layers depend on inner layers, never the reverse.

### Layer Structure

```
Domain (innermost)
  --> Application
    --> Infrastructure
      --> Presentation (outermost)
```

| Layer | Contains | Rules |
|-------|----------|-------|
| **Domain** | Entities, value objects, services, port interfaces (ABCs) | No framework imports. Pure Python / TypeScript. |
| **Application** | Use cases, DTOs | Depends only on domain ports, never on infrastructure. |
| **Infrastructure** | Repository implementations, API adapters | Implements domain port interfaces. |
| **Presentation** | API routes, request/response schemas, React components | Thin layer. No business logic. |

### Key Principles

- Define interfaces (ports) in the domain layer. Implement them in infrastructure.
- Use cases depend on port abstractions, not concrete implementations.
- Inject dependencies at runtime via dependency injection.
- ORM models are separate from domain entities.
- The domain layer has **no** imports from FastAPI, SQLAlchemy, Pydantic, React, or MobX.

### Frontend MVVM Pattern

The frontend uses **MobX ViewModels** following the MVVM pattern:

- **ViewModels** handle all state, logic, computed properties, and side effects.
- **React components** are thin `observer()` wrappers that render based on ViewModel state.
- Components contain no business logic and no direct API calls.

For architecture decision records, see the [ADRs](docs/architecture/decisions/).

## Package Management

### Python (Backend)

Use `uv` exclusively. Never use `pip`.

```bash
# Add a production dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Sync all dependencies from pyproject.toml
uv sync

# Run a tool
uv run ruff check .
```

**Forbidden commands:** `uv pip install`, `pip install`, `@latest` syntax.

### Node.js (Frontend)

Use `npm` with Node.js 22 LTS, managed via `nvm`.

```bash
# Switch to the correct Node version
nvm use 22

# Install dependencies
cd frontend && npm install

# Add a dependency
npm install package-name

# Add a dev dependency
npm install --save-dev package-name
```

## Make Targets Reference

Run `make help` for the full list. Here are the targets you will use most often:

| Task | Command |
|------|---------|
| Start the full application | `make dev` |
| Start backend only | `make dev-backend` |
| Start frontend only | `make dev-frontend` |
| Run backend unit tests | `make test` |
| Run frontend unit tests | `make test-frontend` |
| Run integration tests | `make test-integration` |
| Run all tests (unit + integration + frontend) | `make test-all` |
| Run end-to-end tests | `make test-e2e` |
| Run linters and type checks | `make lint` |
| Auto-format code | `make format` |
| Run database migrations | `make migrate` |
| Start infrastructure (PostgreSQL) | `make infra-up` |
| Stop infrastructure | `make infra-down` |
| Clean all build artifacts | `make clean` |
| Show current version | `make version` |
