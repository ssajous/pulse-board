# Test Conventions

Reference for all testing conventions, patterns, and standards in the Pulse Board project. Use this document when writing new tests or reviewing existing ones.

**Test stack**: pytest (backend), Vitest (frontend unit), Playwright (E2E)

## File Organization

### Backend Tests

Test files mirror the source tree under `tests/`. Each test file maps 1:1 to a source file.

| Source file | Test file |
|---|---|
| `src/pulse_board/domain/entities/topic.py` | `tests/unit/pulse_board/domain/entities/test_topic.py` |
| `src/pulse_board/domain/services/voting_service.py` | `tests/unit/pulse_board/domain/services/test_voting_service.py` |
| `src/pulse_board/application/use_cases/create_topic.py` | `tests/unit/pulse_board/application/use_cases/test_create_topic.py` |
| `src/pulse_board/presentation/api/routes/topics.py` | `tests/unit/pulse_board/presentation/api/routes/test_topics.py` |
| `src/pulse_board/infrastructure/repositories/topic_repository.py` | `tests/integration/pulse_board/infrastructure/repositories/test_topic_repository.py` |

**Naming rules**:

- Prefix test files with `test_` (e.g., `test_topic.py`, not `topic_test.py`).
- Place unit tests under `tests/unit/`.
- Place integration tests under `tests/integration/`.
- Maintain `__init__.py` files at every directory level in the test tree.

### Frontend Tests

Frontend unit tests use the `__tests__/` folder convention, colocated with the source.

| Source file | Test file |
|---|---|
| `frontend/src/presentation/view-models/TopicsViewModel.ts` | `frontend/src/presentation/view-models/__tests__/TopicsViewModel.test.ts` |

**Naming rules**:

- Use `.test.ts` suffix for unit test files.
- Place tests in a `__tests__/` directory alongside the module under test.

### E2E Tests

E2E tests live in `tests/e2e/` with supporting fixtures and helpers in subdirectories.

```
tests/e2e/
  fixtures/
    app.fixture.ts          # Custom Playwright fixtures (pageA, pageB)
  helpers/
    api.helper.ts           # Direct HTTP API calls for test setup
    wait.helper.ts          # Polling helpers for WebSocket-driven UI updates
  vote-broadcast.spec.ts    # Spec files use .spec.ts suffix
  censure.spec.ts
  bidirectional.spec.ts
```

**Naming rules**:

- Use `.spec.ts` suffix for E2E spec files.
- Name helper files with a `.helper.ts` suffix.
- Name fixture files with a `.fixture.ts` suffix.

## Python Test Conventions

### Test Classes

Group related tests in classes named `TestXxx`. Name each class after the unit under test and the behavior group.

```python
class TestTopicCreate:
    """Tests for Topic.create factory method."""

class TestTopicSanitization:
    """Tests for HTML sanitization in Topic.create."""

class TestCastVoteUseCase:
    """Tests for CastVoteUseCase."""

class TestCreateTopicRoute:
    """Tests for POST /api/topics."""
```

Class-level docstrings describe what the class covers. Every test class must have a docstring.

### Test Methods

- Prefix all methods with `test_`.
- Use descriptive `snake_case` names that state the expected behavior.
- Return type annotation `-> None` on every test method.
- Every test method has a one-line docstring describing expected behavior.

```python
def test_create_valid_topic(self) -> None:
    """Should create a topic with the given content."""
    topic = Topic.create("My topic")

    assert topic.content == "My topic"
    assert isinstance(topic.id, uuid.UUID)
    assert topic.score == 0
    assert isinstance(topic.created_at, datetime)
```

### Arrange-Act-Assert Pattern

Separate the three phases with blank lines. This visual structure makes each test scannable.

```python
def test_create_topic_persists_to_repo(self) -> None:
    """Should persist the topic in the repository."""
    # Arrange
    repo = FakeTopicRepository()
    use_case = CreateTopicUseCase(repository=repo)

    # Act
    result = use_case.execute("Persisted topic")

    # Assert
    saved = repo.get_by_id(result.id)
    assert saved is not None
    assert saved.content == "Persisted topic"
```

Do not use comments like `# Arrange`, `# Act`, `# Assert`. Blank lines convey the structure.

### Exception Testing

Use `pytest.raises` as a context manager. Include `match` for specific error messages when the exception type is shared across multiple validation paths.

```python
def test_create_empty_content_raises(self) -> None:
    """Should raise ValidationError for empty content."""
    with pytest.raises(ValidationError):
        Topic.create("")

def test_cast_vote_raises_not_found_for_missing_topic(self) -> None:
    """Should raise EntityNotFoundError for nonexistent topic."""
    with pytest.raises(EntityNotFoundError, match="Topic not found"):
        use_case.execute(missing_id, FINGERPRINT, UPVOTE)
```

### Module-Level Constants

Define reusable test values as module-level constants in `UPPER_SNAKE_CASE`.

```python
FINGERPRINT = "test-fingerprint-abc"
TOPIC_ID = uuid.uuid4()
```

### Helper Functions

Prefix private helper functions with `_`. Include a docstring and type annotations.

```python
def _create_topic(
    topic_repo: FakeTopicRepository,
    score: int = 0,
) -> Topic:
    """Create and persist a topic with a given initial score."""
    topic = Topic.create("Test topic")
    topic.score = score
    return topic_repo.create(topic)
```

For integration tests, use `_make_` prefixed factory helpers:

```python
def _make_topic(
    content: str = "Test topic",
    score: int = 0,
) -> Topic:
    """Create a Topic entity with optional overrides."""
    return Topic(
        id=uuid.uuid4(),
        content=content,
        score=score,
        created_at=datetime.now(UTC),
    )
```

### Performance Constraints

- No unit test runs longer than 2 seconds. Most run in a few milliseconds.
- Unit tests must not produce side effects: no database records, no messages on queues, no network calls.

## Test Doubles

### Fakes (Preferred for Ports)

Fakes are in-memory implementations of domain port interfaces (ABCs). They live in `tests/unit/pulse_board/fakes.py` and are shared across all unit tests.

Each fake implements the corresponding port from `src/pulse_board/domain/ports/`:

| Port (ABC) | Fake implementation |
|---|---|
| `TopicRepository` | `FakeTopicRepository` |
| `VoteRepository` | `FakeVoteRepository` |
| `EventPublisher` | `FakeEventPublisher` |

Fakes use simple in-memory data structures and contain no assertion logic.

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

    def get_by_id(self, id: uuid.UUID) -> Topic | None:
        return self._topics.get(id)
```

`FakeEventPublisher` records published events in lists for post-hoc assertion:

```python
class FakeEventPublisher(EventPublisher):
    """In-memory event publisher that records published events for assertions."""

    def __init__(self) -> None:
        self.score_updates: list[dict[str, Any]] = []
        self.censured_events: list[dict[str, Any]] = []
        self.new_topic_events: list[dict[str, Any]] = []

    async def publish_score_update(self, topic_id: uuid.UUID, score: int) -> None:
        self.score_updates.append({"topic_id": topic_id, "score": score})
```

### When to Use Fakes vs. Mocks

| Scenario | Use | Reason |
|---|---|---|
| Repository/service port in unit tests | Fake | Fakes implement the full port interface and can verify state |
| Event publisher in unit tests | Fake | Record events in lists; assert on the list after the action |
| Database port with simple boolean | Inline fake class | Trivial one-method port (see health check example below) |
| External dependencies in frontend tests | `vi.fn()` | TypeScript ports are interfaces, not ABCs; vi.fn() is idiomatic |

Inline fakes for trivial ports:

```python
class FakeDatabaseConnected(DatabasePort):
    def is_connected(self) -> bool:
        return True
```

### No External Mocking Libraries

The backend does not use `unittest.mock`, `pytest-mock`, or any patching. All test isolation is achieved through dependency injection and fake implementations of port interfaces.

## Fixtures

### conftest.py Hierarchy

Fixtures are scoped to the test directory where they are needed. Each `conftest.py` serves a specific layer.

| File | Scope | Purpose |
|---|---|---|
| `tests/conftest.py` | Root | Shared fixtures across all tests (currently minimal) |
| `tests/integration/conftest.py` | Integration | Database engine, session factory, table cleanup |
| `tests/unit/pulse_board/presentation/api/routes/conftest.py` | Route unit tests | FastAPI `TestClient` with dependency overrides |

### Integration Test Fixtures

Integration fixtures use session-scoped resources for the database engine and per-test cleanup for data isolation.

```python
@pytest.fixture(scope="session")
def integration_engine() -> Engine:
    """Create a test database engine."""
    url = os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)
    return create_engine(url)

@pytest.fixture(scope="session")
def create_tables(integration_engine: Engine) -> None:
    """Create all tables for the test session."""
    Base.metadata.create_all(integration_engine)

@pytest.fixture(scope="session")
def integration_session_factory(
    integration_engine: Engine, create_tables: None
) -> sessionmaker:
    """Provide a session factory bound to the test engine."""
    return sessionmaker(bind=integration_engine)
```

Cleanup fixtures run after each test. Delete in foreign-key order.

```python
@pytest.fixture
def cleanup_votes(integration_session_factory: sessionmaker):
    """Delete all votes and topics after each test."""
    yield
    with integration_session_factory() as session:
        session.execute(text("DELETE FROM votes"))
        session.execute(text("DELETE FROM topics"))
        session.commit()
```

Integration test files compose these fixtures locally:

```python
@pytest.fixture
def repo(
    integration_session_factory: sessionmaker,
    cleanup_topics: None,
) -> SQLAlchemyTopicRepository:
    """Create repository using the integration session factory."""
    return SQLAlchemyTopicRepository(session_factory=integration_session_factory)
```

### Route Test Fixtures (TestClient)

Route-level unit tests use FastAPI `TestClient` with `app.dependency_overrides` to inject fakes.

```python
@pytest.fixture
def fake_repo() -> FakeTopicRepository:
    """Provide a fresh in-memory topic repository."""
    return FakeTopicRepository()

@pytest.fixture
def client(
    fake_repo: FakeTopicRepository,
    fake_vote_repo: FakeVoteRepository,
    fake_publisher: FakeEventPublisher,
) -> TestClient:
    """Provide a test client wired to fake repositories and publisher."""
    app = create_app()
    overrides = app.dependency_overrides
    overrides[get_create_topic_use_case] = lambda: CreateTopicUseCase(
        repository=fake_repo
    )
    overrides[get_list_topics_use_case] = lambda: ListTopicsUseCase(
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

Route tests can inject both the `client` and the individual fakes to inspect internal state:

```python
def test_create_topic_broadcasts_new_topic(
    self,
    client: TestClient,
    fake_publisher: FakeEventPublisher,
) -> None:
    """Creating a topic should publish a new_topic event."""
    response = client.post("/api/topics", json={"content": "Broadcast me"})
    body = response.json()

    assert len(fake_publisher.new_topic_events) == 1
    event = fake_publisher.new_topic_events[0]
    assert str(event["topic_id"]) == body["id"]
```

### setup_method for Domain Services

Domain service tests that need a fresh service per test use `setup_method` instead of fixtures:

```python
class TestProcessVoteCreateNew:
    """Tests for creating a new vote when no existing vote."""

    def setup_method(self) -> None:
        """Create a fresh VotingService for each test."""
        self.service = VotingService()
```

## Frontend Test Conventions

### Imports

Always import test utilities from `vitest` explicitly:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
```

### Structure

Use nested `describe` blocks. The outer block names the class or module, inner blocks group by method or behavior.

```typescript
describe("TopicsViewModel", () => {
  describe("constructor", () => {
    it("calls fetchTopics on construction", async () => { ... });
  });

  describe("handleScoreUpdate (via WebSocket)", () => {
    it("updates score for an existing topic", async () => { ... });
  });

  describe("submitTopic", () => {
    it("adds topic from API response without calling fetchTopics again", async () => { ... });
  });
});
```

### Factory Functions

Create factory functions for test data and mock implementations. Name them `makeTopic`, `createMockApi`, etc.

```typescript
function makeTopic(overrides: Partial<Topic> = {}): Topic {
  return {
    id: "t1",
    content: "Test topic",
    score: 0,
    created_at: "2026-02-17T10:00:00Z",
    ...overrides,
  };
}
```

Mock factories return objects that implement domain port interfaces:

```typescript
function createMockApi(topics: Topic[] = []): TopicApiPort {
  return {
    fetchTopics: vi.fn().mockResolvedValue(topics),
    createTopic: vi
      .fn()
      .mockImplementation(async (content: string) => ({
        id: "new-id",
        content,
        score: 0,
        created_at: "2026-02-17T12:00:00Z",
      })),
  };
}

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

### Async Testing with MobX

MobX actions that trigger async operations require flushing microtasks before assertions. Use the `flushMicrotasks()` helper.

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

### Assertions

Use strict equality with `toBe` for primitives, `toEqual` for objects/arrays, and specific matchers for presence checks.

| Assertion | Use for |
|---|---|
| `expect(x).toBe(5)` | Primitives (numbers, strings, booleans) |
| `expect(x).toEqual({...})` | Object/array deep equality |
| `expect(x).toHaveLength(2)` | Array/string length |
| `expect(fn).toHaveBeenCalledTimes(1)` | Mock call count |
| `expect(fn).toHaveBeenCalledWith("arg")` | Mock call arguments |
| `expect(x).toBeDefined()` | Not undefined |
| `expect(x).toBeNull()` | Null check |

### Running Frontend Tests

```bash
make test-frontend
```

## E2E Test Conventions

### Custom Fixtures

E2E tests extend Playwright's `test` object with custom fixtures defined in `tests/e2e/fixtures/app.fixture.ts`. The fixtures provide two independent browser contexts (`pageA`, `pageB`) for testing multi-user WebSocket scenarios.

```typescript
export const test = base.extend<AppFixtures>({
  contextA: async ({ browser }, use) => {
    const context = await browser.newContext();
    await use(context);
    await context.close();
  },
  pageA: async ({ contextA }, use) => {
    const page = await contextA.newPage();
    await waitForPageReady(page);
    await use(page);
  },
  // pageB follows the same pattern with contextB
});
```

Import `test` and `expect` from the fixture file, not from `@playwright/test`:

```typescript
import { test, expect } from "./fixtures/app.fixture";
```

### Helper Modules

**`api.helper.ts`** -- Direct HTTP calls to the backend for test setup, bypassing the UI.

| Function | Purpose |
|---|---|
| `resetDatabase()` | POST to `/api/test/reset` to clear all data |
| `createTopicViaApi(content)` | POST to `/api/topics` |
| `castVoteViaApi(topicId, fingerprintId, direction)` | POST to `/api/topics/{id}/votes` |

**`wait.helper.ts`** -- Polling helpers that wait for WebSocket-driven UI updates.

| Function | Purpose |
|---|---|
| `reloadAndWaitForWs(page)` | Reload the page and wait for WebSocket connection |
| `waitForTopicToAppear(page, content)` | Wait for topic text to appear in `#topic-list` |
| `waitForScoreUpdate(page, topicId, expectedScore)` | Wait for score to update on `#topic-card-{id}` |
| `waitForTopicToDisappear(page, topicId)` | Wait for topic card to become invisible |

### Database Reset

Every E2E test calls `resetDatabase()` in `beforeEach` to guarantee a clean slate. This hits the `/api/test/reset` endpoint, which is only available when `PULSE_BOARD_TEST_MODE=true`.

```typescript
test.describe("Vote broadcast", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("upvote in Browser A updates score in Browser B", async ({ pageA, pageB }) => {
    const topic = await createTopicViaApi("Vote Test Topic");
    await reloadAndWaitForWs(pageA);
    await reloadAndWaitForWs(pageB);
    // ...
  });
});
```

### Element Selectors

Use element IDs following the `{component}-{element}-{optional-identifier}` convention.

| Selector | Element |
|---|---|
| `#topic-list` | Container for all topic cards |
| `#topic-card-${id}` | Individual topic card |
| `#topic-upvote-${id}` | Upvote button for a topic |
| `#topic-downvote-${id}` | Downvote button for a topic |

Use `page.locator()` with these selectors:

```typescript
await pageA.click(`#topic-upvote-${topic.id}`);
await waitForScoreUpdate(pageB, topic.id, 1);
```

### Playwright Configuration

Key settings in `playwright.config.ts`:

| Setting | Value | Reason |
|---|---|---|
| `workers` | `1` | Sequential execution for WebSocket state consistency |
| `fullyParallel` | `false` | Tests depend on shared server state |
| `timeout` | `30_000` | Allow time for server startup and WebSocket operations |
| `expect.timeout` | `5_000` | Default assertion timeout |
| `retries` | `2` (CI only) | Handle flaky WebSocket timing in CI |
| `baseURL` | `http://localhost:5173` | Frontend dev server |

Playwright manages both servers via `webServer` config. The backend starts with `PULSE_BOARD_TEST_MODE=true`.

### Running E2E Tests

```bash
make test-e2e
```

This starts infrastructure, runs database migrations, then executes Playwright tests.

## Adding New Tests

### Domain Entity Test

1. Create `tests/unit/pulse_board/domain/entities/test_<entity>.py`.
2. Add a `__init__.py` if the directory is new.
3. Write a test class per factory method or behavior group.
4. Test validation rules, default values, boundary conditions, and reconstitution.
5. Run: `make test-unit`.

### Use Case Test

1. Create `tests/unit/pulse_board/application/use_cases/test_<use_case>.py`.
2. Import fakes from `tests/unit/pulse_board/fakes.py`.
3. Instantiate the use case with fakes in each test (or in a `_setup()` helper).
4. Test the happy path, validation errors, persistence side effects, and return value immutability.
5. Verify the repository is not touched when validation fails.
6. Run: `make test-unit`.

### Route Test

1. Create `tests/unit/pulse_board/presentation/api/routes/test_<route>.py`.
2. Use the `client` fixture from `conftest.py` (it wires fakes automatically).
3. Request a second fixture (e.g., `fake_publisher`) to inspect side effects.
4. Test status codes, response body shape, and event publishing.
5. Run: `make test-unit`.

### Integration Test (Repository)

1. Create `tests/integration/pulse_board/infrastructure/repositories/test_<repo>.py`.
2. Use `integration_session_factory` and the appropriate `cleanup_*` fixture.
3. Create a local `repo` fixture composing the session factory and cleanup.
4. Test CRUD operations, boundary conditions, and empty-state behavior.
5. Run: `make test-integration` (requires infrastructure: `make infra-up`).

### Frontend ViewModel Test

1. Create `frontend/src/presentation/view-models/__tests__/<ViewModel>.test.ts`.
2. Create factory functions for the domain entities and mock port implementations.
3. Use `flushMicrotasks()` after constructing the ViewModel.
4. Test observable state changes, WebSocket message handling, error states, and disposal.
5. Run: `make test-frontend`.

### E2E Test

1. Create `tests/e2e/<feature>.spec.ts`.
2. Import `test` from `./fixtures/app.fixture`.
3. Call `resetDatabase()` in `beforeEach`.
4. Set up test data via `api.helper.ts` functions (not through the UI).
5. Use `wait.helper.ts` functions for WebSocket-dependent assertions.
6. Run: `make test-e2e`.

### New Fake Implementation

When adding a new domain port:

1. Define the port as an ABC in `src/pulse_board/domain/ports/`.
2. Add the fake to `tests/unit/pulse_board/fakes.py`.
3. Implement every abstract method with in-memory data structures.
4. Wire the fake into the route `conftest.py` via `app.dependency_overrides`.

## Anti-Patterns

### Tests

| Anti-pattern | Correct approach |
|---|---|
| Test without a docstring | Every test method has a one-line docstring |
| Missing `-> None` return annotation | All test methods annotate `-> None` |
| Using `unittest.mock.patch` or `@mock.patch` | Use fake implementations injected via constructors |
| Testing private methods directly | Test through the public API |
| Assertions without AAA separation | Use blank lines between arrange, act, and assert |
| Multiple actions in a single test | One action per test; use separate tests for each scenario |
| Tests that depend on execution order | Each test must be independently runnable |
| `sleep()` in unit tests | Only acceptable for timestamp-difference tests with `sleep(0.001)` |
| Hardcoded database URLs in test files | Use `os.environ.get()` with a fallback default |

### Fakes

| Anti-pattern | Correct approach |
|---|---|
| Using `MagicMock` for repository ports | Write a `FakeXxxRepository` that implements the ABC |
| Assertion logic inside a fake | Fakes store data; tests perform assertions |
| Fakes that don't implement the full interface | Implement every abstract method, even if some are no-ops |
| Duplicating fakes across test files | Centralize in `tests/unit/pulse_board/fakes.py` |

### Fixtures

| Anti-pattern | Correct approach |
|---|---|
| Session-scoped data fixtures | Use session scope only for engine/factory; per-test for data |
| Missing cleanup fixtures in integration tests | Always attach a `cleanup_*` fixture that runs after yield |
| Cleanup that ignores foreign key order | Delete child records before parent records |
| Overly broad `conftest.py` | Place fixtures in the narrowest `conftest.py` that needs them |

### E2E

| Anti-pattern | Correct approach |
|---|---|
| Setting up test data through the UI | Use `api.helper.ts` for setup; test only the behavior under test |
| Fixed `sleep()` waits | Use `wait.helper.ts` polling functions or Playwright auto-wait |
| Running tests in parallel | Keep `workers: 1` and `fullyParallel: false` for WebSocket consistency |
| Selectors using CSS classes or tag names | Use element IDs following `{component}-{element}-{id}` convention |
| Skipping `resetDatabase()` in `beforeEach` | Always reset to avoid test pollution |
