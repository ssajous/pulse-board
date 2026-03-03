# Code Style Guide

Reference documentation for code conventions, formatting tools, and quality standards in the Pulse Board project.

## Formatting Tools

### Python: Ruff

Ruff handles both formatting and linting for all Python code. It replaces Black, isort, and Flake8 with a single, fast tool.

| Setting | Value |
|---------|-------|
| Line length | 88 characters |
| Target version | Python 3.13 |
| Configuration file | `pyproject.toml` |

Run formatting and linting:

```bash
make format         # Auto-format and auto-fix Python code
make lint           # Check all linters without modifying files
```

Run Ruff individually:

```bash
uv run ruff format .          # Format Python files
uv run ruff format . --check  # Check formatting without changes
uv run ruff check .           # Lint Python files
uv run ruff check . --fix     # Lint and auto-fix where possible
```

### TypeScript: ESLint

ESLint checks all `.ts` and `.tsx` files in the frontend. The configuration in `frontend/eslint.config.js` extends:

- `@eslint/js` recommended rules
- `typescript-eslint` recommended rules
- `eslint-plugin-react-hooks` (enforces Rules of Hooks)
- `eslint-plugin-react-refresh` (validates Fast Refresh boundaries)

`make lint` runs ESLint as part of its full check. To run ESLint alone:

```bash
cd frontend && npx eslint .
```

### Python Type Checking: Pyright

Pyright performs static type analysis on all Python source code.

| Setting | Value |
|---------|-------|
| Mode | `basic` |
| Python version | 3.13 |
| Included paths | `src/` |
| Configuration file | `pyproject.toml` |

Run type checking:

```bash
uv run pyright
```

Pyright runs as part of `make lint`.

## Ruff Lint Rules

The following rule sets are enabled in `pyproject.toml`:

| Code | Rule Set | What It Catches |
|------|----------|-----------------|
| `E` | pycodestyle errors | Syntax and style errors (whitespace, indentation) |
| `F` | Pyflakes | Unused imports, undefined names, redefined variables |
| `I` | isort | Import ordering and grouping |
| `N` | pep8-naming | Naming convention violations |
| `W` | pycodestyle warnings | Style warnings (trailing whitespace, blank lines) |
| `UP` | pyupgrade | Code that can use newer Python syntax |

Import ordering uses `known-first-party = ["pulse_board"]` to correctly sort project imports after third-party packages.

## Naming Conventions

| Element | Python | TypeScript |
|---------|--------|------------|
| Functions and methods | `snake_case` | `camelCase` |
| Variables | `snake_case` | `camelCase` |
| Classes | `PascalCase` | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| File names | `snake_case.py` | `kebab-case.tsx` |
| Test files (backend) | `test_module_name.py` | -- |
| Test files (frontend) | -- | `ModuleName.test.ts` |

### Python Examples

```python
# Constants
MAX_TOPIC_LENGTH = 500
DEFAULT_SORT_ORDER = "created_at"

# Functions
def calculate_net_score(upvotes: int, downvotes: int) -> int:
    """Calculate the net score from upvote and downvote counts."""
    return upvotes - downvotes

# Classes
class TopicRepository(ABC):
    """Abstract base class for topic persistence."""
```

### TypeScript Examples

```typescript
// Constants
const MAX_RECONNECT_ATTEMPTS = 5;
const WS_PING_INTERVAL = 30_000;

// Functions
function formatRelativeTime(dateString: string): string { ... }

// Classes
class TopicsViewModel { ... }
```

## Architecture Patterns

### Onion Architecture (Backend)

Dependencies point inward. Outer layers depend on inner layers, never the reverse.

```
Domain  <--  Application  <--  Infrastructure  <--  Presentation
(innermost)                                         (outermost)
```

| Layer | Contains | Rules |
|-------|----------|-------|
| **Domain** | Entities, value objects, domain services, port interfaces (ABCs) | No framework imports. No FastAPI, no SQLAlchemy, no Pydantic. |
| **Application** | Use cases, DTOs | Depends on domain ports, not concrete implementations. |
| **Infrastructure** | Repository implementations, database models, external API adapters | Implements domain port interfaces. |
| **Presentation** | API routes, request/response schemas | Thin layer for I/O formatting only. No business logic. |

### MVVM (Frontend)

MobX ViewModels handle all state and logic. React components render based on ViewModel observables and call ViewModel actions.

| Layer | Responsibility |
|-------|---------------|
| **ViewModel** (MobX) | Holds observable state, computed properties, and actions. Manages side effects through reactions. |
| **View** (React) | Renders UI from ViewModel state. Calls ViewModel actions on user interaction. Contains no business logic. |
| **Model** (Domain) | Core entities and port interfaces. |

Components wrap themselves with MobX's `observer()` HOC to react to state changes automatically.

### Key Principles

- Use cases depend on port abstractions (ABCs), not concrete implementations
- Inject dependencies at runtime through FastAPI's dependency injection
- ORM models (`infrastructure/database/models/`) are separate from domain entities (`domain/entities/`)
- Keep presentation routes thin -- delegate to use cases immediately
- Use computed properties in ViewModels instead of derived state in components

## Docstrings

Require docstrings on all public APIs: classes, public methods, functions, and modules that export functionality.

Use Google-style format:

```python
def create_topic(self, content: str) -> Topic:
    """Create a new topic with the given content.

    Validates the content, sanitizes HTML, and persists the topic
    to the repository.

    Args:
        content: The topic text. Must be between 1 and 500 characters.

    Returns:
        The created Topic entity with a generated ID and timestamp.

    Raises:
        ValidationError: If content is empty or exceeds the maximum length.
    """
```

For simple functions where the behavior is obvious from the signature, a single-line docstring is sufficient:

```python
def get_by_id(self, topic_id: uuid.UUID) -> Topic | None:
    """Retrieve a topic by its unique identifier."""
```

## Type Hints

Require type hints on all function signatures -- parameters and return types. This applies to both production code and test code.

```python
# Production code
def cast_vote(
    self,
    topic_id: uuid.UUID,
    fingerprint_id: str,
    direction: VoteDirection,
) -> VoteResult:
    ...

# Test code
def test_cast_vote_creates_new_vote(self) -> None:
    ...
```

Use `|` union syntax (Python 3.10+) instead of `Optional` or `Union`:

```python
# Preferred
def get_by_id(self, topic_id: uuid.UUID) -> Topic | None:

# Avoid
def get_by_id(self, topic_id: uuid.UUID) -> Optional[Topic]:
```

## Code Quality Standards

- **Line length**: 88 characters maximum (enforced by Ruff)
- **Function length**: Aim for 30 lines or fewer. Extract helper functions for longer logic.
- **Early returns**: Use guard clauses to reduce nesting depth.
- **String formatting**: Use f-strings exclusively. Do not use `%` formatting or `.format()`.
- **Configuration values**: Load from environment variables through the `Settings` class. Never hardcode connection strings, ports, or secrets.
- **Imports**: Let Ruff sort them. First-party imports (`pulse_board.*`) are grouped separately from third-party packages.
- **Coverage threshold**: 80% minimum (enforced by `pyproject.toml` configuration).

## Code Review Checklist

Use this checklist when reviewing pull requests:

- [ ] Type hints present on all function signatures
- [ ] Docstrings on all public APIs (classes, public methods, exported functions)
- [ ] No functions longer than approximately 30 lines
- [ ] Early returns used to avoid nested conditionals
- [ ] No hardcoded configuration values (URLs, ports, secrets, thresholds)
- [ ] Tests added for new functionality
- [ ] f-strings used for all string formatting
- [ ] Coverage threshold maintained (80%)
- [ ] Architecture layers respected (no inward dependency violations)
- [ ] ViewModel handles state/logic; React component only renders
- [ ] `make lint` passes with no errors
- [ ] `make test-all` passes with no failures or warnings

## Commands Reference

| Command | Description |
|---------|-------------|
| `make format` | Auto-format and auto-fix Python code with Ruff |
| `make lint` | Run all linters: Ruff check, Ruff format check, Pyright, ESLint |
| `uv run ruff check .` | Python lint only |
| `uv run ruff check . --fix` | Python lint with auto-fix |
| `uv run ruff format .` | Python format only |
| `uv run ruff format . --check` | Python format check (no changes) |
| `uv run pyright` | Python type checking only |
| `make test-all` | Run all tests with coverage reporting |
