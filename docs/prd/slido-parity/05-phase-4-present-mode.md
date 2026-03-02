# Phase 4: Present Mode & QR Code Display

## Overview

This is a **vertical slice** delivering a full-screen, projection-optimized display mode for events. After this phase, an organizer can open a "Present" view in a new browser window, designed for screen sharing and projection. The view shows the currently active poll results, the top-voted topic feed, and a scannable QR code for participant joining. All content auto-updates in real time via the existing WebSocket infrastructure. No new domain entities are required.

**Gap analysis items addressed**: Present mode (#4), QR code display (#5).

## Dependencies

- Phase 3 (Multiple Choice Polls) of the slido-parity PRD must be complete.
- The existing WebSocket infrastructure (pulse-board Phase 4) must be in place.
- The existing event model with join codes (slido-parity Phase 1) must be in place.

## Non-Functional Requirements

| ID | Requirement | Threshold |
|----|-------------|-----------|
| NFR-4.1 | Minimum body text size in present mode | 24px |
| NFR-4.2 | Minimum heading size in present mode | 36px |
| NFR-4.3 | Minimum QR code rendered size | 200x200px |
| NFR-4.4 | WebSocket update latency in present window | < 200ms end-to-end |
| NFR-4.5 | Supported projector resolutions | 1920x1080 and 1280x720 |
| NFR-4.6 | Readable distance for body text | 3+ meters |

---

## Functional Requirements

### FR-4.1: Present-State Endpoint

**Priority**: P0 -- must have

**Description**: Add a `GET /api/events/{event_id}/present-state` endpoint that returns the combined initial state for the present view in a single response: the currently active poll (with result tallies), and the top 10 topics by score. This avoids multiple round trips when the present window first loads.

**Acceptance Criteria**:

- Given a valid `event_id` and an active poll, When I `GET /api/events/{event_id}/present-state`, Then the response MUST include `{ "active_poll": { ...poll with options and vote counts... }, "top_topics": [ ...up to 10 topics sorted by score desc... ], "participant_count": N, "event": { "id", "title", "code" } }`
- Given a valid `event_id` with no active poll, When I `GET /api/events/{event_id}/present-state`, Then the response MUST include `"active_poll": null` and still return top topics and event metadata
- Given an invalid or unknown `event_id`, When I `GET /api/events/{event_id}/present-state`, Then the response MUST return HTTP 404
- Given the endpoint, When I inspect it in `/docs`, Then it MUST be documented with request and response schemas

### FR-4.2: Present Mode Route

**Priority**: P0 -- must have

**Description**: Add a dedicated frontend route `/events/:code/present` that renders the full-screen present view. This route MUST be self-contained and require no login. It MUST be openable in a separate browser window or tab.

**Acceptance Criteria**:

- Given a valid event code, When I navigate to `/events/ABCD/present`, Then the `PresentModeView` component MUST render without redirecting or showing an error
- Given an invalid event code, When I navigate to `/events/INVALID/present`, Then a user-friendly "Event not found" message MUST be shown
- Given the event board view, When I click "Open Present Mode", Then the URL `/events/:code/present` MUST open in a new browser window (via `window.open`)
- Given the present view is open, When I press F11 in the browser, Then the view MUST remain correctly laid out in full-screen mode

### FR-4.3: PresentModeViewModel (MobX)

**Priority**: P0 -- must have

**Description**: Create a `PresentModeViewModel` using MobX that manages all state for the present view. It MUST subscribe to the existing event-scoped WebSocket channel and update its observables when poll results or topic scores change.

**Acceptance Criteria**:

- Given the ViewModel initializes with a valid event code, When `initialize()` is called, Then it MUST fetch initial state from `GET /api/events/{event_id}/present-state` and populate `activePoll`, `topTopics`, `participantCount`, and `event` observables
- Given the ViewModel is initialized, When a `poll_result_update` WebSocket message arrives for the active poll, Then the ViewModel MUST update the poll option vote counts without a full re-fetch
- Given the ViewModel is initialized, When a `poll_activated` WebSocket message arrives, Then the ViewModel MUST set `activePoll` to the newly activated poll
- Given the ViewModel is initialized, When a `poll_deactivated` WebSocket message arrives, Then the ViewModel MUST set `activePoll` to `null`
- Given the ViewModel is initialized, When a `score_update` WebSocket message arrives, Then the ViewModel MUST update the matching topic's score in `topTopics` and re-sort
- Given the ViewModel is initialized, When a `new_topic` WebSocket message arrives and the new topic score qualifies for top 10, Then the ViewModel MUST insert it at the correct sorted position
- Given the WebSocket disconnects, When reconnection occurs, Then the ViewModel MUST re-fetch present-state to recover any missed updates
- Given the ViewModel, When I inspect its computed properties, Then it MUST expose `sortedTopTopics` (sorted by score desc), `hasPoll` (boolean), and `joinUrl` (string derived from event code)

### FR-4.4: PresentModeView Layout

**Priority**: P0 -- must have

**Description**: Create the `PresentModeView` full-screen React component. The layout MUST be distraction-free, high-contrast, and optimized for projection at 1920x1080 and 1280x720. It MUST render a split-panel layout: active poll results on the left, topic feed on the right, and a persistent header with event title, participant count, and QR code.

**Acceptance Criteria**:

- Given the present view, When rendered at 1920x1080, Then all body text MUST be at minimum 24px and all headings at minimum 36px
- Given the present view, When rendered at 1280x720, Then the layout MUST not overflow and all key information MUST remain visible without scrolling
- Given an active poll, When the view renders, Then the `PresentPollResults` panel MUST occupy the primary content area (left/center)
- Given no active poll, When the view renders, Then the `PresentTopicFeed` MUST expand to fill the full content area
- Given the present view, When I inspect the DOM, Then the root container MUST have `id="present-mode-view"`
- Given the view, When I inspect the header, Then it MUST have `id="present-header"` and display event title and participant count

### FR-4.5: Dark and Light Theme Variants

**Priority**: P1 -- should have

**Description**: The present view MUST support a dark theme (default, high contrast for dimly-lit rooms and projectors) and a light theme (for bright rooms). The active theme MUST be togglable via a keyboard shortcut (`T`) and persisted in `localStorage`.

**Acceptance Criteria**:

- Given the present view in dark theme, When rendered, Then the background MUST be near-black (e.g., `bg-gray-950`) and all text MUST be white or near-white
- Given the present view in light theme, When rendered, Then the background MUST be white or near-white and all text MUST be dark
- Given the user presses `T` while in present view, When the keypress fires, Then the theme MUST toggle between dark and light
- Given a theme preference has been saved to `localStorage`, When the present view opens in a new window, Then it MUST restore the saved theme
- Given the present view, When I inspect it, Then a theme toggle button MUST be accessible via `id="present-theme-toggle"`

### FR-4.6: PresentPollResults Component

**Priority**: P0 -- must have

**Description**: Create a `PresentPollResults` component that renders the active poll as a large, readable horizontal bar chart. Bars MUST animate width transitions as vote counts update in real time. All text MUST meet the minimum size constraints for projection.

**Acceptance Criteria**:

- Given an active poll with options, When rendered, Then the poll question MUST be displayed at minimum 36px and each option label at minimum 24px
- Given a poll option receiving a new vote via WebSocket, When the score updates, Then the bar width MUST animate with a CSS transition (no abrupt jump)
- Given poll options, When rendered, Then each bar MUST display the vote count and percentage (e.g., "12 votes · 48%")
- Given all options have zero votes, When rendered, Then all bars MUST be shown at a minimal width (0% bar is not invisible) with "0 votes · 0%"
- Given the component, When I inspect it, Then it MUST have `id="present-poll-results"`

### FR-4.7: PresentTopicFeed Component

**Priority**: P0 -- must have

**Description**: Create a `PresentTopicFeed` component that shows the top-voted topics as a large-text, high-contrast scrolling list. Each topic card MUST display the topic content, score, and rank position. New topics and score changes MUST be visually indicated.

**Acceptance Criteria**:

- Given the top topics list, When rendered, Then each topic MUST be displayed with rank number, content (minimum 24px), and score
- Given a topic whose score changes via WebSocket, When the update lands, Then the topic card MUST briefly highlight (e.g., a 500ms flash animation) before settling
- Given a newly inserted topic (from `new_topic` WebSocket event), When it enters the top-10 list, Then it MUST animate in (e.g., fade-in) at its sorted position
- Given more than 10 topics, When rendered, Then only the top 10 by score MUST be shown
- Given the component, When I inspect it, Then it MUST have `id="present-topic-feed"` and each topic card MUST have `id="present-topic-{topic_id}"`

### FR-4.8: QRCodeDisplay Component

**Priority**: P0 -- must have

**Description**: Create a `QRCodeDisplay` component that generates and renders a QR code from the event join URL using `qrcode.react`. The QR code MUST be scannable by a smartphone at 3+ meters from a typical projector screen.

**Acceptance Criteria**:

- Given an event with code `ABCD`, When the `QRCodeDisplay` renders, Then the QR code MUST encode the full join URL (e.g., `https://app.example.com/events/ABCD`)
- Given the rendered QR code, When I inspect it, Then its rendered size MUST be at minimum 200x200px
- Given a dark theme, When the QR code renders, Then it MUST use high-contrast colors (e.g., white modules on dark background) to remain scannable
- Given a light theme, When the QR code renders, Then it MUST use dark modules on a light background
- Given the component, When I inspect the DOM, Then it MUST have `id="present-qr-code"`

### FR-4.9: PresentHeader Component

**Priority**: P0 -- must have

**Description**: Create a `PresentHeader` component that displays the event title, live participant count, and the `QRCodeDisplay`. The header MUST be persistently visible in all layout states.

**Acceptance Criteria**:

- Given the present view, When rendered, Then the header MUST show the event title at minimum 36px
- Given the participant count observable updates via WebSocket, When the update fires, Then the displayed count MUST update without a full component re-render
- Given the header, When rendered, Then the `QRCodeDisplay` MUST be visible in the header area
- Given the header, When I inspect it, Then it MUST have `id="present-header"`, title MUST have `id="present-event-title"`, and participant count MUST have `id="present-participant-count"`

### FR-4.10: "Open Present Mode" Button in Event Board View

**Priority**: P0 -- must have

**Description**: Add an "Open Present Mode" button to the existing event board admin view. Clicking it MUST open `/events/:code/present` in a new browser window.

**Acceptance Criteria**:

- Given the event board view for an organizer, When I inspect the page, Then an "Open Present Mode" button MUST be visible
- Given the button, When clicked, Then `window.open('/events/:code/present', '_blank')` MUST be called, opening the present view in a new window
- Given the button, When I inspect it, Then it MUST have `id="open-present-mode-btn"`
- Given the present mode window is already open, When the button is clicked again, Then a new window MUST open (no focus-or-open behavior required)

---

## Testing Requirements

### Unit Tests

**TR-4.U1: PresentModeViewModel state management**

- Test that `initialize()` populates `activePoll`, `topTopics`, `participantCount`, and `event` from a mocked API response.
- Test that receiving a `poll_result_update` WebSocket message updates the correct option's vote count without mutating unrelated state.
- Test that receiving `poll_activated` sets `activePoll` to the new poll object.
- Test that receiving `poll_deactivated` sets `activePoll` to `null`.
- Test that receiving `score_update` updates the correct topic score in `topTopics` and re-sorts `sortedTopTopics`.
- Test that `hasPoll` computed property returns `true` when `activePoll` is non-null and `false` when null.
- Test that `joinUrl` computed property constructs the correct URL from the event code.
- Test that theme toggle action switches `currentTheme` between `"dark"` and `"light"` and writes to `localStorage`.
- Test that on initialization the theme is read from `localStorage` when present.

File path: `frontend/src/presentation/components/present-mode/PresentModeViewModel.test.ts`

**TR-4.U2: QRCodeDisplay component**

- Test that the component renders a `<canvas>` or `<svg>` element when given a valid URL.
- Test that the `data-join-url` attribute (or equivalent accessible label) reflects the event join URL.
- Test that the rendered element has minimum dimensions of 200x200px.

File path: `frontend/src/presentation/components/present-mode/QRCodeDisplay.test.tsx`

**TR-4.U3: PresentPollResults component**

- Test that option labels and vote counts render for each option.
- Test that percentage calculation is correct (votes / total_votes * 100, rounded).
- Test that zero-vote options render a visible bar (not hidden).

File path: `frontend/src/presentation/components/present-mode/PresentPollResults.test.tsx`

**TR-4.U4: PresentTopicFeed component**

- Test that only the top 10 topics are rendered when more than 10 are provided.
- Test that topics are rendered in score-descending order.
- Test that each topic card has the expected `id="present-topic-{topic_id}"` attribute.

File path: `frontend/src/presentation/components/present-mode/PresentTopicFeed.test.tsx`

### Integration Tests

**TR-4.I1: Present-state endpoint**

- Test that `GET /api/events/{valid_id}/present-state` returns HTTP 200 with the correct shape including `active_poll`, `top_topics`, `participant_count`, and `event`.
- Test that when no poll is active, `active_poll` is `null` in the response.
- Test that `top_topics` is limited to at most 10 entries, sorted by score descending.
- Test that `GET /api/events/{invalid_id}/present-state` returns HTTP 404.

File path: `tests/integration/presentation/api/routes/present_state_tests.py`

**TR-4.I2: Present mode frontend loads correct event data**

- Test that navigating to `/events/ABCD/present` renders the event title matching the test event.
- Test that the QR code element is present in the DOM.
- Test that poll results render when an active poll exists on the event.

File path: `tests/integration/presentation/present_mode_load_tests.py`

### End-to-End Tests

**TR-4.E1: Open present mode, create poll, verify real-time update**

- Step 1: Open the event board admin view in Tab A.
- Step 2: Click "Open Present Mode" button; verify a new window (Tab B) opens at `/events/:code/present`.
- Step 3: In Tab A, activate a multiple-choice poll.
- Step 4: In Tab B (present window), verify that `#present-poll-results` appears without manual refresh.
- Step 5: In another participant tab (Tab C), submit a vote on the poll.
- Step 6: In Tab B, verify that the poll bar for the voted option updates width and vote count in real time.

File path: `tests/e2e/present_mode_realtime_tests.spec.ts`

**TR-4.E2: QR code visible and correct URL**

- Step 1: Open `/events/:code/present`.
- Step 2: Verify `#present-qr-code` is present in the DOM.
- Step 3: Verify the encoded URL contains the event join code.

File path: `tests/e2e/present_mode_realtime_tests.spec.ts` (same file, separate test)

### Visual Regression Tests

**TR-4.V1: Present mode layout at 1920x1080**

- Capture a screenshot of the present view with an active poll and topic feed at 1920x1080 viewport.
- Capture a screenshot with no active poll (topic feed expands to full width) at 1920x1080.
- Store reference screenshots; fail on visual diff exceeding 1% of pixels.
- Repeat both captures at 1280x720.

Tool: Playwright visual comparison (`expect(page).toHaveScreenshot()`).
File path: `tests/e2e/present_mode_visual_tests.spec.ts`

---

## Documentation Deliverables

**DD-4.1: User guide — present mode usage**

- Create `docs/user-guides/present-mode.md` covering:
  - How to open present mode from the event board ("Open Present Mode" button).
  - What is displayed in each panel (poll results, topic feed, QR code).
  - How to toggle between dark and light themes (keyboard shortcut `T`).
  - How attendees can join using the displayed QR code.
  - Recommended browser and display settings for projector use (full-screen via F11, recommended resolution).

**DD-4.2: Screenshot examples in user guide**

- Include at minimum two annotated screenshots in `docs/user-guides/present-mode.md`:
  - Dark theme with an active poll visible.
  - Light theme with the topic feed expanded (no active poll).

**DD-4.3: API documentation**

- The `GET /api/events/{event_id}/present-state` endpoint MUST be documented in the FastAPI auto-docs (`/docs`) with a clear description, all response fields explained, and example responses for both the "poll active" and "no poll" cases.

**DD-4.4: Component docstrings / JSDoc**

- `PresentModeViewModel`: JSDoc block describing observable properties, computed properties, and public actions.
- `QRCodeDisplay`: JSDoc block describing props (`joinUrl`, `size`, `theme`).
- `PresentPollResults`: JSDoc block describing props (`poll`, `theme`).
- `PresentTopicFeed`: JSDoc block describing props (`topics`, `theme`).
- `PresentHeader`: JSDoc block describing props (`event`, `participantCount`, `theme`).

---

## Non-Goals for This Phase

- **30+ display themes**: Only dark and light themes are delivered. Additional theme palettes are a future phase.
- **Custom branding or logo**: No custom logos or organizational colors in the present view.
- **Presenter controls inside the present view**: The host manages polls and topics from the admin board view, not from the present window.
- **Embedded presenter notes**: No speaker notes or off-screen prompt panel.
- **Automatic content cycling**: The view does not auto-cycle between poll, topics, and QR code panels on a timer. Active content determines which panel is primary.
- **Word cloud visualization in present mode**: Word cloud polls (future slido-parity phase) are not displayed yet; if a word cloud poll were somehow active, the present view SHOULD show a fallback message.
- **Quiz leaderboard in present mode**: Quiz mode (future slido-parity phase) leaderboard display is not in scope.
- **iframe / embeddable present view**: Embedding the present view in third-party sites is not in scope.

---

## Technical Notes

### Backend

- The `GET /api/events/{event_id}/present-state` endpoint SHOULD be implemented as a thin presentation-layer route delegating to a new `GetPresentStateUseCase` in the application layer. The use case queries the existing event, poll, and topic repositories; no new domain entities are required.
- Participant count MAY be derived from the active WebSocket connection count for the event's channel, or from a simple counter tracked in the `ConnectionManager`. If no reliable real-time count is available, return the total historical participant count from the event record as a fallback.
- The endpoint MUST return `top_topics` sorted by score descending, limited to 10 entries. This limit is enforced in the use case, not in the repository query, to keep repository methods general.

### Frontend

- Install `qrcode.react` via `npm install qrcode.react`. This is a zero-backend, client-side QR code renderer. No backend involvement is needed for QR code generation.
- `PresentModeViewModel` MUST reuse the existing event-scoped WebSocket subscription (established in earlier slido-parity phases). It MUST NOT open a second independent WebSocket connection.
- The present view MUST be a standalone route that does NOT depend on being opened from the admin board view. It MUST bootstrap its own state via `initialize()` using the event code from the URL params.
- Font size constraints (24px body, 36px heading) MUST be enforced via explicit Tailwind classes (e.g., `text-2xl` = 24px, `text-4xl` = 36px or larger), not via browser zoom or CSS `zoom` property.
- The "Open Present Mode" button MUST use `window.open` with `'_blank'` target. Do NOT use React Router navigation for this action, as it must open a new window.
- Theme state MUST be stored in `PresentModeViewModel` as an observable string (`"dark"` | `"light"`) and applied as a Tailwind class on the root container (`dark` class on `<html>` or the root `div`).
- The component folder structure MUST follow the project convention:
  ```
  frontend/src/presentation/components/present-mode/
    PresentModeView.tsx
    PresentModeViewModel.ts
    PresentHeader.tsx
    PresentPollResults.tsx
    PresentTopicFeed.tsx
    QRCodeDisplay.tsx
    index.ts
  ```
- All interactive and key structural elements MUST include `id` attributes following the convention `{component}-{element}-{optional-identifier}`.

### WebSocket Message Types Consumed

This phase consumes the following WebSocket message types (already defined in earlier phases) scoped to the event channel:

| Message type | Trigger | ViewModel action |
|---|---|---|
| `poll_activated` | Host activates a poll | Set `activePoll` |
| `poll_deactivated` | Host deactivates a poll | Set `activePoll = null` |
| `poll_result_update` | Participant votes on poll | Update option vote count |
| `score_update` | Topic vote cast | Update topic score, re-sort |
| `new_topic` | New topic submitted | Insert into `topTopics` if qualifies |
| `participant_joined` | New participant connects to event WebSocket channel | Update `participantCount` |

---

## Validation Checklist

Before marking this phase complete, verify each item:

**Functional**
- [ ] `GET /api/events/{event_id}/present-state` returns correct combined state
- [ ] `/events/:code/present` route renders without error for valid event codes
- [ ] "Open Present Mode" button opens the route in a new window
- [ ] `PresentModeViewModel` populates all observables from initial fetch
- [ ] Active poll results update in real time via WebSocket (no manual refresh)
- [ ] Topic feed updates score and re-sorts in real time via WebSocket
- [ ] QR code renders and encodes the correct join URL
- [ ] QR code is minimum 200x200px
- [ ] Dark and light themes both render correctly
- [ ] Theme persists to `localStorage` and restores on window open
- [ ] Theme toggles on `T` keypress

**Non-Functional**
- [ ] Body text is minimum 24px across all present view components
- [ ] Heading text is minimum 36px across all present view components
- [ ] Layout is correct at 1920x1080 viewport (no overflow)
- [ ] Layout is correct at 1280x720 viewport (no overflow)
- [ ] WebSocket-driven updates arrive within 200ms

**Testing**
- [ ] All unit tests pass (`PresentModeViewModel`, `QRCodeDisplay`, `PresentPollResults`, `PresentTopicFeed`)
- [ ] All integration tests pass (`present-state` endpoint, frontend load)
- [ ] E2E test passes: open present mode, activate poll, vote in participant tab, verify real-time update in present window
- [ ] Visual regression screenshots captured at 1920x1080 and 1280x720

**Code Quality**
- [ ] `uv run ruff format . --check` passes
- [ ] `uv run ruff check .` passes with no errors
- [ ] `uv run pyright` passes with no type errors
- [ ] `npm run lint` passes with no errors
- [ ] All new components have JSDoc blocks
- [ ] `GET /api/events/{event_id}/present-state` is documented in `/docs` with example responses

**Architecture**
- [ ] `GetPresentStateUseCase` lives in the application layer; no business logic in the route handler
- [ ] `PresentModeViewModel` contains all state and logic; React components are dumb renderers
- [ ] No second WebSocket connection opened by present view (reuses event-scoped channel)
- [ ] QR code generation is entirely client-side (`qrcode.react`); no backend involvement
- [ ] Domain layer has no new framework imports

**Documentation**
- [ ] `docs/user-guides/present-mode.md` created with usage instructions
- [ ] At least two annotated screenshots included in the user guide
- [ ] API endpoint documented in FastAPI auto-docs with example responses
