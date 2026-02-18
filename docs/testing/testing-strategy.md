# Testing Strategy

This document explains the reasoning behind Pulse Board's testing architecture, how each test type contributes to confidence in the system, and why the testing patterns are structured the way they are. It is written for contributors who want to understand not just *how* to write tests, but *why* the project tests things the way it does.

## Overview

Pulse Board's testing strategy is built on two foundational principles: **fast feedback** and **architectural alignment**. Tests are organized to mirror the onion architecture of the codebase, so each architectural layer has a testing approach that matches its role and its distance from external systems.

The goal is not to maximize line coverage for its own sake. Instead, the project aims to create a test suite that catches real bugs quickly, runs in seconds during local development, and provides clear diagnostic information when something breaks. Every test should answer the question: "If this test fails, what exactly is wrong?"

The project enforces an 80% code coverage threshold as a floor, not a ceiling. Coverage below 80% blocks the build. Coverage above 80% is valuable only when it protects against meaningful failure modes.

## Testing Pyramid

Pulse Board follows the classic testing pyramid with a deliberate emphasis on the bottom layer:

```
        /  E2E  \          ~5 tests   | Minutes | Real browsers + WebSocket
       /----------\
      / Integration \       ~10 tests  | Seconds | Real PostgreSQL
     /----------------\
    /    Unit Tests     \   ~40 tests  | < 2s    | No I/O, no mocks needed at domain level
   /______________________\
```

**Unit tests** form the wide base. They run in under 2 seconds total and cover the domain entities, domain services, application use cases, and presentation routes. The speed matters because developers run `make test` dozens of times per session. A slow unit test suite discourages testing.

**Integration tests** occupy the middle layer. They verify that the SQLAlchemy repository implementations correctly translate between domain entities and PostgreSQL rows. These tests require a running database but are still fast enough to run in CI on every push.

**End-to-end tests** sit at the top. They verify that two browser windows connected via WebSocket see the same real-time updates. These tests are expensive to run and maintain, so the project limits them to the critical real-time interaction paths that cannot be verified any other way.

This shape is intentional. When a domain entity's validation logic changes, the unit tests catch it immediately without starting any infrastructure. When a SQL query has an off-by-one error on the censure threshold, the integration tests catch it against a real database. When the WebSocket broadcast fails to reach a second browser, the e2e tests catch it. Each layer tests what only it can test.

### Running the full pyramid

```bash
# Fast feedback: unit tests only (< 2 seconds)
make test

# Include integration tests (requires PostgreSQL via Docker)
make test-integration

# Frontend unit tests (vitest)
make test-frontend

# Everything: unit + integration + frontend + coverage report
make test-all

# End-to-end: real browsers with WebSocket (slowest)
make test-e2e
```

## Backend Testing Strategy

The backend testing strategy directly reflects the four layers of the onion architecture. Each layer has distinct testing rules about what is real, what is faked, and what is off-limits.

### Domain Layer: Pure Unit Tests

The domain layer contains business rules with zero framework dependencies. Domain entities like `Topic` and `Vote`, domain services like `VotingService`, and domain events are all plain Python dataclasses and functions. They have no imports from FastAPI, SQLAlchemy, or any external library.

This purity is the point. Domain tests need no mocks, no patches, no fixtures, and no setup. They instantiate domain objects directly and assert against their behavior:

```python
# tests/unit/pulse_board/domain/entities/test_topic.py
def test_create_valid_topic(self) -> None:
    topic = Topic.create("My topic")

    assert topic.content == "My topic"
    assert isinstance(topic.id, uuid.UUID)
    assert topic.score == 0
```

Domain tests verify validation rules (empty content, maximum length), invariants (new topics start at score zero), and sanitization (HTML escaping to prevent XSS). They are the fastest tests in the suite and the least likely to break for reasons unrelated to a code change.

**What domain tests cover:**
- Entity factory methods and validation logic (`Topic.create`, `Vote.create`)
- Domain service calculations (`VotingService.calculate_delta`, censure threshold checks)
- Domain event construction (`TopicCensuredEvent`)
- Input sanitization (HTML entity encoding)

**What domain tests do not cover:**
- Persistence behavior -- that belongs to integration tests
- HTTP request/response formatting -- that belongs to route tests
- WebSocket message delivery -- that belongs to e2e tests

### Application Layer: Use Case Tests with Fake Repositories

The application layer orchestrates domain logic through use cases like `CastVoteUseCase`, `CreateTopicUseCase`, and `ListTopicsUseCase`. Each use case depends on port interfaces (abstract base classes) defined in the domain layer. In production, these ports are implemented by SQLAlchemy repositories. In tests, they are implemented by in-memory fakes.

The project maintains a shared set of fake implementations in `tests/unit/pulse_board/fakes.py`:

```python
class FakeTopicRepository(TopicRepository):
    """In-memory topic repository for unit tests."""

    def __init__(self) -> None:
        self._topics: dict[uuid.UUID, Topic] = {}

    def create(self, topic: Topic) -> Topic:
        self._topics[topic.id] = topic
        return topic

    def list_active(self) -> list[Topic]:
        return list(self._topics.values())
```

These fakes implement the same `TopicRepository` and `VoteRepository` abstract base classes that the production code uses, which guarantees that the test doubles honor the port contract. If the port interface changes, both the fake and the real implementation must be updated -- the type checker enforces this.

Use case tests follow a setup-execute-assert pattern with a module-level helper function:

```python
# tests/unit/pulse_board/application/use_cases/test_cast_vote.py
def _setup() -> tuple[CastVoteUseCase, FakeVoteRepository, FakeTopicRepository]:
    vote_repo = FakeVoteRepository()
    topic_repo = FakeTopicRepository()
    voting_service = VotingService()
    use_case = CastVoteUseCase(
        vote_repo=vote_repo,
        topic_repo=topic_repo,
        voting_service=voting_service,
    )
    return use_case, vote_repo, topic_repo
```

**Why fakes instead of mocks?** Fakes maintain internal state (an in-memory dictionary), which means the test can call `use_case.execute()` and then verify the side effect by querying the fake repository. This produces tests that read like a description of the use case's behavior rather than a specification of which methods it calls. A mock-based test would assert "the repository's `save` method was called with these arguments." A fake-based test asserts "after executing the use case, the vote exists in the repository." The second style is more resilient to refactoring.

**What use case tests cover:**
- Successful execution paths (create vote, toggle vote, cancel vote)
- Error handling (topic not found raises `EntityNotFoundError`)
- Domain event generation (censure events when score hits threshold)
- Result immutability (the `CastVoteResult` dataclass is frozen)
- Side effects on repositories (vote is persisted, score is updated)

### Presentation Layer: Route Tests with Dependency Overrides

Presentation layer tests verify that FastAPI routes correctly translate HTTP requests into use case calls and format the responses. They use FastAPI's `TestClient` with `dependency_overrides` to swap production dependencies for fakes:

```python
# tests/unit/pulse_board/presentation/api/routes/conftest.py
@pytest.fixture
def client(
    fake_repo: FakeTopicRepository,
    fake_vote_repo: FakeVoteRepository,
    fake_publisher: FakeEventPublisher,
) -> TestClient:
    app = create_app()
    overrides = app.dependency_overrides
    overrides[get_create_topic_use_case] = lambda: CreateTopicUseCase(
        repository=fake_repo
    )
    overrides[get_cast_vote_use_case] = lambda: CastVoteUseCase(
        vote_repo=fake_vote_repo,
        topic_repo=fake_repo,
        voting_service=VotingService(),
    )
    overrides[get_event_publisher] = lambda: fake_publisher
    return TestClient(app)
```

This approach tests the full HTTP layer -- URL routing, request body parsing, Pydantic schema validation, status code selection, and JSON response formatting -- without touching a database. The `TestClient` sends real HTTP requests through the ASGI application, so these tests catch issues like incorrect status codes, missing response fields, and broken request validation.

Route tests also verify event publishing behavior. The `FakeEventPublisher` records every event it receives, which allows the test to assert that voting broadcasts a `score_update` event and that reaching the censure threshold publishes both a `score_update` and a `topic_censured` event:

```python
def test_cast_vote_broadcasts_score_update(
    self,
    client: TestClient,
    fake_publisher: FakeEventPublisher,
) -> None:
    topic_id = _create_topic(client)
    client.post(
        f"/api/topics/{topic_id}/votes",
        json={"fingerprint_id": "user-abc", "direction": "up"},
    )

    assert len(fake_publisher.score_updates) == 1
    assert fake_publisher.score_updates[0]["score"] == 1
```

**What route tests cover:**
- HTTP status codes for success, validation errors, and not-found conditions
- Response body structure and field values
- Request validation (empty fingerprints, invalid vote directions)
- Event publishing side effects (score updates, censure broadcasts)
- Multi-step interactions (vote, toggle, cancel sequences)

### Test File Organization

Test files mirror the source tree exactly. This convention eliminates ambiguity about which test file covers which module:

```
src/pulse_board/                         tests/unit/pulse_board/
  domain/                                  domain/
    entities/topic.py            -->        entities/test_topic.py
    entities/vote.py             -->        entities/test_vote.py
    services/voting_service.py   -->        services/test_voting_service.py
  application/
    use_cases/cast_vote.py       -->      application/use_cases/test_cast_vote.py
    use_cases/create_topic.py    -->      application/use_cases/test_create_topic.py
  presentation/
    api/routes/votes.py          -->      presentation/api/routes/test_votes.py
    api/routes/topics.py         -->      presentation/api/routes/test_topics.py
```

Integration tests follow the same mirroring convention under `tests/integration/`:

```
src/pulse_board/                         tests/integration/pulse_board/
  infrastructure/
    repositories/                          infrastructure/repositories/
      topic_repository.py       -->          test_topic_repository.py
      vote_repository.py        -->          test_vote_repository.py
```

## Frontend Testing Strategy

The frontend follows the MVVM (Model-View-ViewModel) pattern with MobX. In this architecture, the ViewModel contains all state and logic, and React components are thin rendering layers. This separation creates a natural testing boundary: test the ViewModel thoroughly with fast unit tests, and rely on e2e tests for the visual rendering.

### ViewModel Testing with Vitest

The `TopicsViewModel` is the primary unit under test. It manages topic state, WebSocket message handling, vote casting, fingerprint initialization, and error states. Tests use Vitest's `vi.fn()` to create mock implementations of the port interfaces:

```typescript
// Factory for creating mock API ports
function createMockApi(topics: Topic[] = []): TopicApiPort {
  return {
    fetchTopics: vi.fn().mockResolvedValue(topics),
    createTopic: vi.fn().mockImplementation(async (content: string) => ({
      id: "new-id",
      content,
      score: 0,
      created_at: "2026-02-17T12:00:00Z",
    })),
  };
}
```

The frontend port interfaces (`TopicApiPort`, `VoteApiPort`, `WebSocketPort`, `FingerprintPort`) serve the same role as the backend's abstract base classes. The ViewModel depends on these interfaces, and tests provide mock implementations. This keeps the ViewModel testable without a running backend.

### Testing Asynchronous Behavior

The ViewModel's constructor triggers asynchronous data fetching. Tests use a `flushMicrotasks()` helper to wait for these promises to resolve before making assertions:

```typescript
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

it("calls fetchTopics on construction", async () => {
  const api = createMockApi([makeTopic()]);
  new TopicsViewModel(api);
  await flushMicrotasks();

  expect(api.fetchTopics).toHaveBeenCalledTimes(1);
});
```

This pattern is necessary because MobX actions triggered in the constructor schedule microtasks. Without flushing, the test assertions run before the async operations complete.

### Testing WebSocket Message Handling

WebSocket tests capture the message handler registered by the ViewModel and invoke it directly with various payloads. The `createMockWs()` factory returns both the mock port and a reference to the registered handler:

```typescript
function createMockWs(): MockWsResult {
  const messageHandler: { current: WebSocketMessageHandler | null } = {
    current: null,
  };
  const ws: WebSocketPort = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    onMessage: vi.fn((handler) => {
      messageHandler.current = handler;
    }),
    onReconnect: vi.fn((handler) => {
      reconnectHandler.current = handler;
    }),
  };
  return { ws, messageHandler, reconnectHandler };
}
```

Tests then simulate WebSocket messages by calling `messageHandler.current!()` with different payloads (`score_update`, `new_topic`, `topic_censured`) and verifying the ViewModel state changes. This approach is significantly faster than opening real WebSocket connections and covers edge cases like malformed messages, duplicate topics, and message ordering during active votes.

### What ViewModel Tests Cover

- **Data loading**: Initial fetch, error states, loading indicators
- **Topic management**: Submit new topics, handle API failures
- **WebSocket events**: Score updates, new topic broadcasts, censure events, reconnection
- **Vote interactions**: Optimistic updates, preventing WebSocket score overwrites during active votes
- **Sorting**: Computed `sortedTopics` property orders by score then creation date
- **Input validation**: Malformed WebSocket messages are silently ignored
- **Lifecycle**: `dispose()` disconnects the WebSocket

### Why Components Are Not Directly Tested

React components in this project are thin `observer()` wrappers that render based on ViewModel state. They contain no business logic, no conditional branching beyond rendering, and no direct API calls. Testing them with a library like React Testing Library would verify that MobX's `observer()` integration works -- a concern that belongs to the MobX library's own test suite, not this project's. The e2e tests verify the complete rendered UI in a real browser, which catches any component rendering issues that matter.

Run the frontend tests with:

```bash
make test-frontend
```

## End-to-End Testing Strategy

End-to-end tests verify the one thing no other test level can: that two users looking at the same page in different browsers see consistent real-time updates. Pulse Board is fundamentally a multi-user real-time application, and the e2e tests protect the contract that WebSocket broadcasts actually reach connected clients.

### Two-Browser Architecture

Every e2e test runs with two isolated browser contexts (pageA and pageB). A custom Playwright fixture creates both contexts and waits for each page to establish a WebSocket connection before handing control to the test:

```typescript
// tests/e2e/fixtures/app.fixture.ts
export const test = base.extend<AppFixtures>({
  pageA: async ({ contextA }, use) => {
    const page = await contextA.newPage();
    await waitForPageReady(page);
    await use(page);
  },
  pageB: async ({ contextB }, use) => {
    const page = await contextB.newPage();
    await waitForPageReady(page);
    await use(page);
  },
});
```

The `waitForPageReady` function navigates to the app, waits for the topic list to be visible, and then waits for a console message confirming the WebSocket connection. This eliminates race conditions where a test clicks a button before the WebSocket is ready.

### Test Helpers

The e2e test suite uses two categories of helpers to keep spec files focused on behavior rather than mechanics:

**API helpers** (`api.helper.ts`) interact with the backend directly via HTTP to set up test state:
- `resetDatabase()` -- Calls `POST /api/test/reset` to clear all data between tests. This endpoint only exists when `PULSE_BOARD_TEST_MODE=true`.
- `createTopicViaApi(content)` -- Creates a topic without going through the UI, so both browsers start from the same state.
- `castVoteViaApi(topicId, fingerprint, direction)` -- Casts a vote via API to trigger WebSocket broadcasts.

**Wait helpers** (`wait.helper.ts`) encapsulate Playwright's waiting patterns with sensible timeouts:
- `reloadAndWaitForWs(page)` -- Reloads the page and waits for the WebSocket to reconnect (10-second timeout).
- `waitForTopicToAppear(page, content)` -- Waits for a topic with the given text to appear in the topic list (5-second timeout).
- `waitForScoreUpdate(page, topicId, expectedScore)` -- Waits for a specific topic card to display the expected score.
- `waitForTopicToDisappear(page, topicId)` -- Waits for a censured topic to be removed from the DOM.

### What E2E Tests Cover

The e2e test suite consists of five spec files, each verifying a specific real-time scenario:

| Spec File | Scenario |
|-----------|----------|
| `vote-broadcast.spec.ts` | Upvote/downvote in browser A updates score in browser B |
| `topic-broadcast.spec.ts` | New topic created in browser A appears in browser B |
| `censure.spec.ts` | Topic reaching -5 score disappears from both browsers |
| `vote-cancel.spec.ts` | Cancelling a vote updates score across browsers |
| `bidirectional.spec.ts` | Both browsers vote simultaneously and see consistent results |

### Configuration Decisions

The Playwright configuration (`playwright.config.ts`) reflects deliberate trade-offs:

- **Single worker** (`workers: 1`): WebSocket tests share server state. Parallel execution causes race conditions where one test's `resetDatabase()` call wipes another test's setup.
- **Chromium only**: Running a single browser keeps the test suite fast. Cross-browser WebSocket behavior differences are minimal and not worth the execution time.
- **30-second timeout**: WebSocket connections can take several seconds to establish, especially under load. A 30-second timeout prevents flaky failures.
- **No retries locally** (`retries: 0`), **two retries in CI** (`retries: 2`): Retries mask flaky tests during local development but prevent CI pipeline noise from transient failures.
- **Auto-starting servers**: The `webServer` configuration starts both the backend (with `PULSE_BOARD_TEST_MODE=true`) and frontend dev server automatically, so `make test-e2e` requires no manual setup beyond infrastructure.

Run the e2e tests with:

```bash
make test-e2e
```

## Coverage Goals

The project enforces an 80% code coverage threshold via `pytest-cov`. The configuration in `pyproject.toml` defines what is measured and what is excluded:

```toml
[tool.coverage.run]
source = ["pulse_board"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "\\.\\.\\.",
]
```

### What to Cover

Focus coverage on code paths that represent business decisions:
- Domain entity validation (what makes a topic valid or invalid?)
- Use case branching logic (create vs. toggle vs. cancel a vote)
- Censure threshold calculations (when does a topic get removed?)
- Error handling paths (what happens when a topic is not found?)
- Event publishing logic (which events fire under which conditions?)

### What to Exclude

Some code is intentionally excluded from coverage measurement:
- `__init__.py` files -- These are package markers, not behavior.
- Type checking blocks (`if TYPE_CHECKING:`) -- These run only during static analysis.
- Abstract method bodies (`...`) -- Port interfaces define contracts, not implementations.
- Lines marked `pragma: no cover` -- Used sparingly for defensive code that cannot reasonably be triggered in tests (e.g., a catch-all exception handler for an impossible state).

### Viewing Coverage Reports

```bash
# Terminal output with missing line numbers
make test-unit

# Full HTML report with line-by-line highlighting
make test-coverage
# Open htmlcov/index.html in a browser
```

The `make test-all` target also generates the HTML report alongside the terminal output.

## Test Environment

Each test type has different infrastructure requirements. Understanding these requirements helps developers run the right subset of tests for their workflow.

### Unit Tests (No Infrastructure)

Unit tests require only Python and the project dependencies. They run entirely in-memory using fake repositories and mock objects. No database, no network, no Docker.

```bash
# Prerequisites: Python 3.13+, uv package manager
uv sync
make test
```

Unit tests are designed to run in under 2 seconds total, with individual tests completing in milliseconds. Any unit test that approaches the 2-second threshold indicates a design problem -- likely a dependency on I/O that should be faked.

### Frontend Unit Tests (No Infrastructure)

Frontend tests require Node.js v22 and the npm dependencies. They run in Vitest's jsdom environment with mocked ports. No backend, no browser.

```bash
# Prerequisites: Node.js v22 (via nvm), npm
cd frontend && npm install
make test-frontend
```

### Integration Tests (PostgreSQL via Docker)

Integration tests require a running PostgreSQL instance. The project provides this through Docker Compose, and the `make test-integration` target starts it automatically:

```bash
# Starts PostgreSQL in Docker, then runs integration tests
make test-integration
```

The integration test fixtures use session-scoped database setup (tables are created once per test session) and per-test cleanup (each test deletes its data after running). This balances speed with isolation. The default connection string points to `localhost:5433` to avoid conflicts with any locally installed PostgreSQL on the standard port 5432.

### End-to-End Tests (Full Stack)

E2e tests require the complete stack: PostgreSQL, the FastAPI backend, and the Vite frontend dev server. The `make test-e2e` target handles all of this:

```bash
# Starts infrastructure, runs migrations, launches servers, runs Playwright
make test-e2e
```

The backend must start with `PULSE_BOARD_TEST_MODE=true`, which enables the `POST /api/test/reset` endpoint used to clear the database between tests. This endpoint does not exist in production mode, preventing accidental data loss.

Playwright requires browser binaries. Install them once with:

```bash
npx playwright install chromium
```

## Continuous Integration

Tests fit into the CI pipeline in order of increasing cost. Fast tests run first so that failures surface early, and expensive tests only run when the cheap tests pass.

### Recommended CI Pipeline Stages

```
Stage 1: Lint + Type Check          (~15 seconds)
  make lint

Stage 2: Backend Unit Tests         (~2 seconds)
  make test-unit

Stage 3: Frontend Unit Tests        (~5 seconds)
  make test-frontend

Stage 4: Integration Tests          (~30 seconds, requires PostgreSQL service)
  make test-integration

Stage 5: End-to-End Tests           (~2-3 minutes, requires full stack)
  make test-e2e
```

Stages 1 through 3 require no infrastructure and can run in any CI environment with Python 3.13 and Node.js 22. Stage 4 requires a PostgreSQL service container. Stage 5 requires the full application stack plus Playwright's Chromium binary.

### CI-Specific Behavior

The test configuration adapts to CI environments through environment variables:

- **Playwright retries**: `process.env.CI ? 2 : 0` -- Two retries in CI prevent pipeline failures from transient WebSocket timing issues.
- **Playwright reporter**: `process.env.CI ? "html" : "list"` -- CI generates an HTML report artifact; local development uses inline list output.
- **`forbidOnly`**: `!!process.env.CI` -- The `test.only()` marker is forbidden in CI to prevent accidentally running a subset of tests.
- **Server reuse**: `reuseExistingServer: !process.env.CI` -- CI always starts fresh servers; local development reuses running instances for faster iteration.

### Coverage Gate

The CI pipeline should fail if Python coverage drops below 80%. The `make test-unit` target runs with `--cov=pulse_board --cov-report=term-missing`, and the `fail_under = 80` setting in `pyproject.toml` causes pytest to exit with a non-zero code when coverage is insufficient. Treat coverage failures the same as test failures: the build is broken and must be fixed before merging.
