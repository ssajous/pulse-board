# ADR 005: State Management -- MobX with MVVM Pattern

## Status

Accepted

## Date

2024-12-01

## Context and Problem Statement

The Community Pulse Board frontend must manage several interconnected pieces of reactive state: the list of topics with live-updating scores, per-user vote tracking (via browser fingerprint), optimistic vote updates with server reconciliation, WebSocket message handling for real-time broadcasts, toast notifications, and loading/error states. React components should remain focused on rendering and user interaction, while all state logic, side effects, and computed derivations are handled in a centralized, testable layer. We need a state management approach that enforces this separation.

## Decision Drivers

- **Separation of concerns**: Business logic and state management must be fully decoupled from React component rendering
- **Reactivity**: State changes must automatically propagate to dependent computed values and subscribed components without manual wiring
- **Testability**: State logic must be testable in isolation, without rendering React components or mocking the DOM
- **Minimal boilerplate**: The solution should require less ceremony than action creators, reducers, and selectors for straightforward state operations
- **Computed properties**: Derived state (sorted topics, voting eligibility, empty state) should be declarative and automatically cached
- **Compatibility with React 19**: The solution must integrate cleanly with React 19's rendering model and concurrent features

## Considered Options

1. MobX with MVVM pattern (ViewModels as observable classes)
2. Redux Toolkit (RTK) with slices and thunks
3. Zustand (lightweight store with hooks)
4. React Context + `useReducer` (built-in React primitives)

## Decision Outcome

We chose **Option 1: MobX with MVVM pattern** because it provides transparent reactive state management through observable classes that map directly to the ViewModel concept. The `TopicsViewModel` (see `frontend/src/presentation/view-models/TopicsViewModel.ts`) is a single MobX-observable class that owns all application state, exposes computed properties (`sortedTopics`, `isEmpty`, `canVote`), and contains all side-effect-producing methods (`fetchTopics`, `castVote`, `submitTopic`, WebSocket message handling). React components observe this ViewModel via `mobx-react-lite`'s `observer()` wrapper and re-render only when the specific observable properties they access change.

### Consequences

- **Good**: The `TopicsViewModel` is a plain TypeScript class with no React dependencies -- it can be instantiated and tested with simple unit tests (see `frontend/src/presentation/view-models/__tests__/TopicsViewModel.test.ts`) using mock port implementations.
- **Good**: `makeAutoObservable(this, {}, { autoBind: true })` automatically makes all properties observable, all getters computed, and all methods actions, eliminating per-property decorators.
- **Good**: Computed properties like `sortedTopics` and `canVote` are automatically cached and only recompute when their underlying observables change, preventing unnecessary sorting and filtering on every render.
- **Good**: Optimistic updates (immediate UI feedback during vote casting with server reconciliation on response) are expressed naturally through sequential observable mutations within a single method.
- **Good**: The ViewModel receives dependencies (API ports, fingerprint port, WebSocket port) through constructor injection, enforcing the onion architecture's dependency inversion principle.
- **Good**: React components are thin observers -- for example, `TopicCard` reads `viewModel.getUserVote(topicId)` and `viewModel.isTopicVoting(topicId)` without managing any local state.
- **Bad**: MobX's proxy-based reactivity can produce unexpected behavior if observable objects are destructured outside of `observer()` components or `runInAction()` blocks.
- **Bad**: Debugging MobX state requires MobX DevTools; standard React DevTools do not show observable state natively.
- **Neutral**: The team must understand MobX's reactivity rules (e.g., `runInAction()` for async state updates, observable collections for `Map` and `Set`) to avoid common pitfalls.

## Pros and Cons of the Options

### Option 1: MobX with MVVM Pattern

- **Good**: ViewModels are framework-agnostic TypeScript classes -- they can be reused if the rendering layer changes.
- **Good**: Fine-grained reactivity -- `observer()` components re-render only when the specific observables they read change, not on any store update.
- **Good**: Computed properties (`get sortedTopics()`, `get isEmpty()`, `get canVote()`) are automatically memoized and only recalculated when dependencies change.
- **Good**: `observable.map()` and `observable.set()` provide reactive collection types for `userVotes` and `isVoting`, with automatic change detection on add/delete operations.
- **Good**: Minimal boilerplate -- a single `makeAutoObservable` call replaces all decorators, action wrappers, and selector definitions.
- **Good**: Constructor dependency injection enables easy mocking in tests and enforces the port/adapter pattern from the onion architecture.
- **Bad**: Learning curve for developers unfamiliar with MobX's proxy-based reactivity model.
- **Bad**: `runInAction()` is required for state mutations inside async callbacks, which is easy to forget and produces silent bugs.
- **Bad**: Smaller community than Redux, resulting in fewer tutorials, Stack Overflow answers, and third-party integrations.
- **Neutral**: MobX 6.15+ is stable and well-maintained, with active development and TypeScript-first design.

### Option 2: Redux Toolkit (RTK)

- **Good**: Largest state management ecosystem in React with extensive documentation, DevTools, and middleware.
- **Good**: Predictable state updates through pure reducer functions -- every state change is traceable.
- **Good**: RTK Query provides built-in data fetching, caching, and cache invalidation.
- **Good**: Time-travel debugging via Redux DevTools for diagnosing state issues.
- **Bad**: Significant boilerplate even with RTK's `createSlice` -- requires slices, reducers, selectors, thunks, and typed hooks.
- **Bad**: Computed/derived state requires `createSelector` with explicit memoization configuration, whereas MobX computes it automatically.
- **Bad**: All state updates flow through a single dispatch mechanism, making it harder to express complex multi-step operations (like optimistic voting with rollback) as straightforward imperative code.
- **Bad**: Components must use `useSelector` with careful memoization to avoid unnecessary re-renders, adding cognitive overhead.

### Option 3: Zustand

- **Good**: Minimal API surface -- a single `create()` function defines the entire store.
- **Good**: No provider wrappers required -- stores are accessed via hooks directly.
- **Good**: Lightweight bundle size (~1KB gzipped).
- **Good**: Supports middleware (persist, devtools, immer) for common patterns.
- **Bad**: No built-in computed property concept -- derived state must be manually memoized with `useMemo` or external selectors.
- **Bad**: Store logic is defined inside the `create()` callback, mixing state definition with action implementation in a flat structure that becomes unwieldy for complex state.
- **Bad**: Does not enforce a ViewModel pattern -- state and rendering concerns can easily bleed together.
- **Neutral**: Zustand is hook-based, which works naturally with React but ties the state management approach to the React framework.

### Option 4: React Context + `useReducer`

- **Good**: Zero additional dependencies -- uses only built-in React APIs.
- **Good**: Simple mental model for developers already familiar with React.
- **Good**: `useReducer` provides predictable state transitions similar to Redux.
- **Bad**: Context causes all consumers to re-render when any part of the context value changes, regardless of which property they access, leading to performance problems with frequently updating state (live vote scores).
- **Bad**: No built-in computed property caching -- derived values must be wrapped in `useMemo` with explicit dependency arrays.
- **Bad**: Complex state logic (async operations, optimistic updates, WebSocket handling) requires custom hooks that grow unwieldy and become difficult to test independently of React.
- **Bad**: Does not scale well -- as state complexity grows, the context and reducer become monolithic and hard to decompose.

## More Information

- [MobX documentation](https://mobx.js.org/)
- [mobx-react-lite documentation](https://github.com/mobxjs/mobx/tree/main/packages/mobx-react-lite)
- Topics ViewModel: `frontend/src/presentation/view-models/TopicsViewModel.ts`
- ViewModel context provider: `frontend/src/presentation/view-models/TopicsViewModelContext.ts`
- ViewModel unit tests: `frontend/src/presentation/view-models/__tests__/TopicsViewModel.test.ts`
- Domain ports (injected into ViewModel): `frontend/src/domain/ports/`
- Infrastructure adapters (concrete implementations): `frontend/src/infrastructure/`
