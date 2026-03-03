# ADR 001: Frontend Technology Stack -- React + TypeScript + Vite + Tailwind CSS

## Status

Accepted

## Date

2024-12-01

## Context and Problem Statement

The Community Pulse Board requires a modern frontend capable of rendering a real-time, interactive topic voting interface. The UI must handle live score updates via WebSocket, optimistic vote interactions, animated list reordering, and responsive layouts across desktop and mobile devices. We need a technology stack that enables fast development iteration, strong type safety across the codebase, and a styling approach that scales without CSS conflicts.

## Decision Drivers

- **Developer experience**: Fast feedback loops during development (hot module replacement, clear error messages)
- **Build performance**: Sub-second HMR and fast production builds for a single-page application
- **Type safety**: Compile-time guarantees across component props, API response types, and domain entities
- **Styling flexibility**: Utility-first CSS that avoids naming collisions and works well with component composition
- **Ecosystem maturity**: Access to well-maintained libraries for animations (motion), icons (lucide-react), state management (MobX), and browser fingerprinting (FingerprintJS)
- **Long-term maintainability**: Widely adopted tools with large communities and stable release cycles

## Considered Options

1. React 19 + TypeScript + Vite + Tailwind CSS v4
2. Vue 3 + Nuxt 3 + TypeScript
3. Angular 17+ with built-in SSR
4. Svelte 5 + SvelteKit + TypeScript

## Decision Outcome

We chose **Option 1: React 19 + TypeScript + Vite + Tailwind CSS v4** because it provides the best combination of ecosystem breadth, type safety, and development speed for our use case. React 19's rendering model pairs naturally with MobX observables for reactive state management (see ADR 005). Vite delivers sub-second HMR through native ES module serving, and Tailwind CSS v4 eliminates the need for a separate PostCSS configuration while providing utility-first styling that keeps component files self-contained.

### Consequences

- **Good**: React's component model maps directly to our MVVM architecture -- components observe ViewModel state and re-render automatically via `mobx-react-lite`.
- **Good**: TypeScript catches type mismatches between API response schemas, domain entities, and component props at compile time, reducing runtime errors.
- **Good**: Vite's dev server starts in under 200ms and applies changes without full page reloads, enabling rapid iteration.
- **Good**: Tailwind CSS v4's `@tailwindcss/vite` plugin integrates as a first-class Vite plugin, simplifying the build pipeline.
- **Good**: The React ecosystem provides direct access to FingerprintJS v5, MobX, motion (Framer Motion), and lucide-react without compatibility wrappers.
- **Bad**: React 19 is newer and some third-party libraries may lag behind in full compatibility.
- **Bad**: Tailwind's utility classes can produce verbose JSX when many styles are applied to a single element.
- **Neutral**: TypeScript adds a compilation step, but Vite handles this transparently during development and the `tsc -b && vite build` production build (defined in `package.json`) ensures type checking before bundling.

## Pros and Cons of the Options

### Option 1: React 19 + TypeScript + Vite + Tailwind CSS v4

- **Good**: Largest ecosystem of any frontend framework -- libraries like MobX, FingerprintJS, motion, and lucide-react all provide first-class React support.
- **Good**: TypeScript is deeply integrated with React's type system (`React.FC`, generic hooks, discriminated union props).
- **Good**: Vite provides native ES module serving during development and Rollup-based optimized bundling for production.
- **Good**: Tailwind CSS v4 removes the need for `tailwind.config.js` and PostCSS configuration, using a Vite plugin instead.
- **Good**: React's `memo()`, `forwardRef`, and concurrent rendering features support fine-grained performance optimization.
- **Bad**: React's JSX abstraction adds a layer of indirection compared to template-based frameworks.
- **Bad**: Requires additional libraries for state management (MobX) and routing, whereas some frameworks include these out of the box.
- **Neutral**: React's unidirectional data flow requires explicit patterns for state management, which we address with MobX MVVM (ADR 005).

### Option 2: Vue 3 + Nuxt 3 + TypeScript

- **Good**: Vue's Single File Components combine template, script, and style in one file, improving co-location.
- **Good**: Nuxt provides built-in SSR, routing, and auto-imports, reducing boilerplate.
- **Good**: Vue's reactivity system is built-in, reducing the need for external state management in simpler cases.
- **Bad**: Smaller ecosystem compared to React -- fewer compatible libraries for browser fingerprinting and animation.
- **Bad**: TypeScript support in Vue templates has historically been less mature than in JSX, though it has improved significantly.
- **Bad**: MobX does not have an official Vue integration, which would require us to adopt a different state management approach (Pinia) and redesign the MVVM architecture.
- **Neutral**: Nuxt's SSR capabilities are unnecessary for this single-page application.

### Option 3: Angular 17+

- **Good**: Batteries-included framework with built-in dependency injection, routing, forms, and HTTP client.
- **Good**: Strong TypeScript integration as a first-class language.
- **Good**: Angular's dependency injection aligns conceptually with the onion architecture's inversion of control.
- **Bad**: Significantly heavier framework with a steeper learning curve and more boilerplate.
- **Bad**: Angular's change detection model is less compatible with MobX's observable-based reactivity.
- **Bad**: Smaller pool of contributors familiar with Angular compared to React, increasing hiring and onboarding costs.
- **Neutral**: Angular's opinionated structure enforces consistency but reduces flexibility in architectural choices.

### Option 4: Svelte 5 + SvelteKit + TypeScript

- **Good**: Compiler-based approach produces smaller bundles with no runtime framework overhead.
- **Good**: Svelte's reactivity syntax (`$state`, `$derived`) is concise and intuitive.
- **Good**: SvelteKit provides file-based routing and SSR out of the box.
- **Bad**: Smallest ecosystem of the four options -- limited library support for FingerprintJS, animations, and icon sets.
- **Bad**: No established MobX integration; would require a fundamentally different state management approach.
- **Bad**: Fewer developers with Svelte experience, which affects team scalability.
- **Neutral**: Svelte 5's runes system is a major API change, and the ecosystem is still adapting.

## More Information

- [React 19 documentation](https://react.dev/)
- [Vite documentation](https://vite.dev/)
- [Tailwind CSS v4 documentation](https://tailwindcss.com/docs)
- [TypeScript handbook](https://www.typescriptlang.org/docs/)
- Frontend entry point: `frontend/src/main.tsx`
- Vite configuration: `frontend/vite.config.ts`
- Tailwind integration via `@tailwindcss/vite` plugin in `frontend/package.json`
