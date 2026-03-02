# Slido Feature Gap Analysis for Pulse Board

## Executive Summary

**Slido** is a mature live audience interaction platform (now owned by Cisco) that provides Q&A, live polls, quizzes, word clouds, surveys, and analytics for meetings and events. Its free tier supports up to 100 participants per event with unlimited Q&A, 3 polls, 1 quiz, 30+ presentation themes, and basic integrations.

**Pulse Board** is a real-time community engagement platform focused on anonymous topic submission, up/down voting, and live score updates via WebSockets. It uses browser fingerprinting for vote-per-person enforcement without requiring accounts.

The two platforms share a conceptual foundation -- both enable anonymous audience participation and real-time feedback -- but differ significantly in scope. Slido is a full-featured audience interaction suite covering polls, quizzes, Q&A, analytics, and integrations, while Pulse Board is a focused topic-voting board. This document identifies the specific feature gaps and provides prioritized recommendations for closing them.

---

## Slido Free Tier Overview

### Capacity and Limits

| Limit | Free Tier Value |
|-------|----------------|
| Participants per event | 100 (cumulative) |
| Polls per event | 3 |
| Quizzes per event | 1 |
| Q&A | Unlimited |
| Events | Unlimited (one at a time) |
| Members/admins | 1 |

### Core Features Included in Free Tier

**Q&A (Audience Questions)**
- Anonymous or named question submission
- Question upvoting by other participants
- Real-time question feed
- Automatic saving of questions for later review
- Advance question collection via shareable link
- No downloads or accounts required for participants
- Questions sorted by popularity (upvotes)

**Polling (3 polls per event)**
- Multiple choice polls
- Word cloud polls (visual display of popular answers)
- Rating polls (quick feedback collection)
- Open text polls (free-form responses)
- Ranking polls (prioritize items)
- Real-time result display

**Quizzes (1 quiz per event)**
- Multiple choice quiz questions (up to 30 questions per quiz)
- Speed and accuracy scoring
- Leaderboard with Top 5 winners
- Timer per question for urgency
- Gamification elements

**Presentation and Display**
- Present mode (separate display window for screen sharing)
- 30+ color themes for present mode
- QR code display for participant joining
- Participant view (what attendees see on their devices)
- Host view (admin/management interface)

**Event Management**
- Unique event code for participant joining
- Passcode protection for events
- Event date scheduling
- Image and GIF library for polls
- Automatic data saving

**Integrations (Basic, included in free tier)**
- PowerPoint add-in
- Google Slides integration
- Microsoft Teams integration
- Zoom integration (via marketplace app)
- Webex integration

### Features Requiring Paid Plans

| Feature | Plan Required |
|---------|---------------|
| Unlimited polls | Engage ($15/mo) |
| Question moderation (review before display) | Professional ($60/mo) |
| Custom branding (logo, colors) | Professional ($60/mo) |
| Data export (Excel, Google Sheets, PDF) | Engage ($15/mo) |
| Advanced analytics and sentiment analysis | Professional ($60/mo) |
| Multiple rooms within an event | Professional ($60/mo) |
| Organization-level analytics | Professional ($60/mo) |
| SSO (Single Sign-On) | Enterprise ($150/mo) |
| 200+ participants | Engage ($15/mo) |
| 1,000+ participants | Professional ($60/mo) |

---

## Current Pulse Board Features

Based on codebase analysis (backend: `src/pulse_board/`, frontend: `frontend/src/`):

### Implemented Features

| Feature | Status | Description |
|---------|--------|-------------|
| Topic submission | Implemented | Anonymous 255-character text submissions |
| Up/downvoting | Implemented | Toggle voting with cancel and switch behavior |
| Real-time updates | Implemented | WebSocket push for score changes, new topics, censure |
| Anonymous fingerprinting | Implemented | FingerprintJS v5 for vote-per-browser enforcement |
| Vote censure | Implemented | Topics auto-removed at score -5 |
| Score-based sorting | Implemented | Topics sorted by score, then by creation date |
| Optimistic UI updates | Implemented | Instant vote feedback with server reconciliation |
| Toast notifications | Implemented | Success/error feedback messages |
| Health check API | Implemented | Database connectivity verification |
| Docker deployment | Implemented | Docker Compose for dev and production |
| Database migrations | Implemented | Alembic for PostgreSQL schema management |
| CORS/Origin validation | Implemented | WebSocket origin checking |

### Architecture Strengths

- Clean onion architecture (domain, application, infrastructure, presentation)
- MVVM pattern with MobX on the frontend
- WebSocket real-time infrastructure already in place
- Browser fingerprinting infrastructure for anonymous identity
- PostgreSQL with proper migration tooling
- Comprehensive test suite (unit, integration, E2E)

### Documented Future Plans (Not Yet Implemented)

The `docs/future-possibilities/` directory outlines 11 planned features:
- Trending and smart sort algorithms
- Emoji reactions beyond binary voting
- Topic expiration and pulse cycles
- Community pulse analytics dashboard
- Topic search and text filtering
- Accessibility and keyboard navigation
- Anonymous sentiment clustering
- Duplicate detection and topic merging
- Real-time activity pulse indicator
- Dark/light theme toggle
- Topic bookmarking and personal feed

---

## Feature Gap Analysis

### Category 1: Question and Content Types

Slido supports multiple distinct content types (Q&A, polls, word clouds, quizzes, surveys), while Pulse Board supports only one type: text topics with voting.

- [ ] **Multiple choice polls** -- Allow event creators to define a question with predefined answer options; participants select one or more. Results display in real-time as bar charts or pie charts.
- [ ] **Word cloud polls** -- Participants submit short (1-3 word) text responses to a prompt. Responses are visualized as a word cloud where popular answers appear larger. Slido displays the top 50 responses.
- [ ] **Rating polls** -- Participants rate on a numeric scale (e.g., 1-5 stars). Results show average rating and distribution. Useful for quick feedback on sessions or proposals.
- [ ] **Open text polls** -- Free-form text responses to a question, distinct from topics. Useful for surveys and feedback collection where responses are read rather than voted on.
- [ ] **Ranking polls** -- Participants rank a set of predefined items by priority. Aggregate rankings reveal group consensus on priority ordering.
- [ ] **Quiz/trivia mode** -- Timed multiple-choice questions with correct answers. Participants scored on accuracy and speed. Leaderboard displays top performers. Gamification through competition.
- [ ] **Surveys** -- Collections of multiple poll types (multiple choice, rating, open text) combined into a multi-question form for structured feedback collection.

### Category 2: Q&A / Question Management

Slido's Q&A system is substantially richer than Pulse Board's topic submission.

- [ ] **Question upvoting without downvoting** -- Slido's Q&A uses upvote-only to surface popular questions, different from Pulse Board's up/down model. Consider adding a Q&A-specific interaction mode.
- [ ] **Question moderation (pre-display review)** -- Host reviews incoming questions before they become visible to all participants. Prevents irrelevant or inappropriate content from appearing. (Note: Slido free tier does NOT include moderation; it requires Professional plan.)
- [ ] **Question status tracking** -- Mark questions as "answered," "highlighted," or "archived" so presenters can manage the flow of a live Q&A session.
- [ ] **Advance question collection** -- Allow participants to submit questions before an event starts via a shareable link. Questions accumulate and are available when the session begins.
- [ ] **Question pinning/highlighting** -- Host can pin important questions to the top of the feed, independent of vote count.
- [ ] **Named vs. anonymous toggle** -- Allow participants to optionally attach a name to their submission. Slido supports both modes; Pulse Board is anonymous-only.

### Category 3: Event and Session Management

Pulse Board operates as a single persistent board. Slido is organized around discrete events with codes, dates, and lifecycle management.

- [ ] **Event/session creation** -- Create discrete events with a start and end date. Each event gets its own polls, Q&A, and quiz instances. Enables recurring use for different meetings.
- [ ] **Event join codes** -- Generate unique short codes (e.g., "3847") that participants enter to join a specific event. Simpler than sharing URLs.
- [ ] **Event passcode protection** -- Optional passcode layer on top of the join code for restricted events.
- [ ] **Multiple rooms within an event** -- Parallel tracks or breakout sessions, each with their own polls and Q&A. Participants can switch between rooms. (Note: requires Slido Professional plan.)
- [ ] **Event scheduling and lifecycle** -- Events with defined date ranges. Automatically open and close participation. Archive past events.
- [ ] **Shareable event links** -- Direct URLs that open the participant view for a specific event without needing to enter a code.
- [ ] **Co-host / collaborator access** -- Invite others to help manage an event's polls and Q&A. (Note: requires Slido Engage plan for multiple members.)

### Category 4: Presentation and Display

Slido includes a dedicated presentation mode for screen sharing during meetings. Pulse Board has a single view.

- [ ] **Present mode (separate display window)** -- A dedicated, visually polished view designed for screen sharing. Shows current poll results, active Q&A, or quiz leaderboard in a format optimized for projection.
- [ ] **Host/admin mode** -- A separate interface for the event organizer showing all controls: poll activation, question moderation, participant count, and real-time management tools.
- [ ] **Participant mode** -- A streamlined mobile-first view for attendees focused on submitting responses, asking questions, and voting.
- [ ] **30+ display themes** -- Pre-built color themes for the presentation display. Slido free tier includes all themes.
- [ ] **QR code display** -- Show a QR code on the presentation screen that attendees can scan to instantly join the event on their phones.
- [ ] **Image and GIF support in polls** -- Attach images or GIFs to poll options to make them more engaging and visual.

### Category 5: Analytics and Reporting

Pulse Board has no analytics. Slido provides engagement metrics, sentiment analysis, and data export.

- [ ] **Event analytics dashboard** -- Aggregate metrics: total participants, questions asked, votes cast, poll participation rates. Visual charts and graphs.
- [ ] **Question/topic sentiment analysis** -- AI-driven classification of submissions as positive, negative, or neutral. Trend analysis over time.
- [ ] **Engagement scoring** -- Numeric engagement scores per event measuring participant interaction levels. Compare across events.
- [ ] **Data export** -- Export poll results, Q&A questions, and analytics to Excel, Google Sheets, or PDF. (Note: requires Slido Engage plan.)
- [ ] **Result image/screenshot download** -- Download poll results or word clouds as shareable images. Copy results to clipboard.
- [ ] **Organization-level analytics** -- Track engagement trends across all events in an organization. Compare meeting effectiveness. (Note: requires Slido Professional plan.)

### Category 6: Integrations

Pulse Board is a standalone web application. Slido integrates directly into major meeting and presentation platforms.

- [ ] **PowerPoint add-in** -- Embed polls and Q&A directly into PowerPoint slides. Results display within the presentation without switching apps.
- [ ] **Google Slides integration** -- Similar to PowerPoint; embed interactive elements into Google Slides presentations.
- [ ] **Microsoft Teams integration** -- Add Slido as a tab or app within Teams meetings. Participants interact directly from the Teams interface.
- [ ] **Zoom integration** -- Slido available as a Zoom Marketplace app. Polls and Q&A accessible from the Zoom meeting sidebar.
- [ ] **Webex integration** -- Native Slido integration within Webex meetings and webinars.
- [ ] **Embeddable widget** -- Embed polls or Q&A into external websites or apps via iframe or JavaScript widget.

### Category 7: Participant Experience

- [ ] **No-download, no-account participation** -- Slido participants join via code or link with zero friction. Pulse Board already supports anonymous access, but lacks the event-code-based join flow.
- [ ] **Mobile-optimized participant view** -- Responsive design specifically tuned for phone-sized screens during live events. Pulse Board has some responsiveness but is not event-participant-optimized.
- [ ] **Multi-device support** -- Participants can switch devices mid-event without losing context. Slido uses session-based tracking.
- [ ] **Emoji responses in word clouds** -- Participants can submit emoji as word cloud responses for fun, expressive engagement.

### Category 8: Branding and Customization

- [ ] **Custom logo upload** -- Display organization logo on the event page and present mode. (Note: requires Slido Professional plan.)
- [ ] **Custom color scheme** -- Set brand colors for the event interface and present mode. (Note: requires Slido Professional plan.)
- [ ] **Custom background image** -- Upload a background image for the present mode display. (Note: requires Slido Professional plan.)

### Category 9: Security and Privacy

- [ ] **Participant data privacy controls** -- Configure what participant data is collected and retained. GDPR compliance features.
- [ ] **SSO (Single Sign-On) for admins** -- Enterprise authentication for event organizers. (Note: requires Slido Enterprise plan.)
- [ ] **Advanced privacy settings** -- Control whether participant names are visible, whether results are shown in real-time, etc. (Note: requires Slido Professional plan.)

---

## Prioritized Feature Recommendations

Features are ranked by a combination of impact (how much value they add for users) and effort (development complexity). Priority tiers:

### Tier 1: High Impact, Low-Medium Effort (Recommended First)

These features close the most significant gaps with reasonable development effort and align well with Pulse Board's existing architecture.

| # | Feature | Impact | Effort | Rationale |
|---|---------|--------|--------|-----------|
| 1 | Event/session creation | High | Medium | Transforms Pulse Board from a single board into a reusable event tool. Foundation for many other features. |
| 2 | Event join codes | High | Low | Simple UX improvement that makes event-based participation intuitive. Depends on event creation. |
| 3 | Multiple choice polls | High | Medium | Most requested interactive feature. Broadens use cases beyond topic voting. |
| 4 | Present mode | High | Medium | Essential for use in meetings and events. Separate window with clean display for screen sharing. |
| 5 | QR code display | Medium | Low | Low-effort addition to present mode that significantly reduces friction for joining. |
| 6 | Rating polls | Medium | Low-Medium | Simple to implement given poll infrastructure. Useful for session feedback. |

### Tier 2: Medium Impact, Medium Effort (Build Next)

These features add significant value and differentiate Pulse Board from a basic voting tool.

| # | Feature | Impact | Effort | Rationale |
|---|---------|--------|--------|-----------|
| 7 | Word cloud polls | Medium | Medium | Visually distinctive feature. Requires text aggregation and dynamic visualization. |
| 8 | Host/admin mode | Medium | Medium | Separates organizer and participant views. Foundation for moderation. |
| 9 | Event analytics dashboard | Medium | Medium-High | Valuable for event organizers. Partially planned in future-possibilities docs. |
| 10 | Question status tracking | Medium | Low | Mark topics as answered/highlighted. Simple state addition to existing topic entity. |
| 11 | Named vs. anonymous toggle | Medium | Low | Allow optional name attachment. Minor entity change. |
| 12 | Open text polls | Medium | Low-Medium | Free-form responses without voting. Builds on poll infrastructure. |

### Tier 3: Medium Impact, Higher Effort (Strategic Features)

These features require more substantial development but provide important capabilities.

| # | Feature | Impact | Effort | Rationale |
|---|---------|--------|--------|-----------|
| 13 | Quiz/trivia mode | Medium | High | Requires timer, scoring, leaderboard. High engagement value but complex. |
| 14 | Display themes (5-10 themes) | Medium | Medium | Visual polish for present mode. CSS/design work rather than backend logic. |
| 15 | Ranking polls | Medium | Medium | Drag-and-drop UI complexity. Aggregation logic for rank scoring. |
| 16 | Data export (CSV/Excel) | Medium | Medium | Export poll results and topics. File generation and download infrastructure. |
| 17 | Advance question collection | Medium | Low | Allow submissions before event start. Mostly a scheduling concern. |
| 18 | Event passcode protection | Low-Medium | Low | Simple authentication layer on event join. |
| 19 | Surveys (multi-question forms) | Medium | High | Combines multiple poll types into a single flow. Requires form builder UI. |

### Tier 4: Lower Priority / Paid-Tier Parity (Future Consideration)

These features match Slido's paid plans and can be considered as Pulse Board matures.

| # | Feature | Impact | Effort | Rationale |
|---|---------|--------|--------|-----------|
| 20 | Question moderation | Low-Medium | Medium | Pre-display review queue. Useful for large events. Slido requires Professional plan. |
| 21 | Sentiment analysis | Low-Medium | High | AI/NLP feature. Valuable but complex. Already in Pulse Board future plans. |
| 22 | Multiple rooms | Low-Medium | High | Parallel tracks within events. Significant architectural complexity. |
| 23 | PowerPoint/Slides integration | Low | Very High | Platform-specific plugins. Major development investment. |
| 24 | Teams/Zoom/Webex integration | Low | Very High | Marketplace app development for each platform. |
| 25 | Custom branding | Low | Medium | Logo, colors, background. Design system work. Slido requires Professional plan. |
| 26 | Embeddable widget | Low-Medium | Medium | iframe/JS embed. Requires isolated rendering context. |
| 27 | Image/GIF in polls | Low | Medium | Media upload and storage infrastructure. |
| 28 | SSO for admins | Low | High | Enterprise auth. Slido requires Enterprise plan. |
| 29 | Organization-level analytics | Low | High | Multi-event aggregate analytics. Slido requires Professional plan. |
| 30 | Co-host / collaborator access | Low-Medium | Medium | Multi-user event management. Requires user model. |

---

## Implementation Notes

### Event/Session Creation (Tier 1, #1)

**Backend changes:**
- New `Event` domain entity with fields: `id`, `title`, `code`, `passcode` (optional), `start_date`, `end_date`, `created_at`, `status`
- New `EventRepository` port and PostgreSQL implementation
- New `CreateEventUseCase`, `JoinEventUseCase`, `ListEventsUseCase`
- Associate existing `Topic` entity with an `event_id` foreign key
- Migration to add `events` table and `event_id` column to `topics`

**Frontend changes:**
- Event creation form component
- Event join page (enter code)
- Event context provider wrapping existing topic views
- Route structure: `/events/:code` for participant view

### Event Join Codes (Tier 1, #2)

- Generate 4-6 digit numeric codes or short alphanumeric slugs
- Validate uniqueness at creation time
- Simple lookup endpoint: `GET /api/events/join/:code`
- Landing page with code input field

### Multiple Choice Polls (Tier 1, #3)

**Backend changes:**
- New `Poll` domain entity with fields: `id`, `event_id`, `question`, `poll_type`, `options` (JSON), `is_active`, `created_at`
- New `PollResponse` entity for participant answers
- `CreatePollUseCase`, `ActivatePollUseCase`, `SubmitResponseUseCase`
- WebSocket events for poll activation and result updates

**Frontend changes:**
- Poll creation form (question + options)
- Poll participation component (radio/checkbox selection)
- Real-time results display (bar chart using existing Tailwind CSS)
- Poll management in host view

### Present Mode (Tier 1, #4)

- New route: `/present/:eventCode` that opens in a new window
- Full-screen, distraction-free layout optimized for projection
- Shows active poll results, current Q&A, or quiz leaderboard
- Auto-updates via existing WebSocket infrastructure
- Dark/light theme variants (aligns with existing future-possibilities plan)

### QR Code Display (Tier 1, #5)

- Use a lightweight QR code library (e.g., `qrcode.react` for frontend)
- Generate QR code from the event join URL
- Display in present mode and host view
- No backend changes required

### Word Cloud Polls (Tier 2, #7)

- Frontend visualization using a word cloud library (e.g., `react-wordcloud` or `d3-cloud`)
- Backend aggregation: group identical/similar short responses, count frequency
- Real-time updates as new responses arrive
- Display top 50 responses (matching Slido behavior)
- Consider text normalization (lowercase, trim) for better aggregation

### Quiz/Trivia Mode (Tier 3, #13)

- New `Quiz` domain entity with ordered questions, correct answers, and time limits
- `QuizSession` entity tracking participant scores (accuracy + speed)
- Real-time leaderboard calculation and WebSocket broadcast
- Timer synchronization between host and participants
- Scoreboard/leaderboard component showing top 5

### Data Export (Tier 3, #16)

- Server-side CSV/Excel generation using `openpyxl` or `csv` module
- Export endpoints: `GET /api/events/:id/export` with format parameter
- Include: all topics/questions, vote counts, poll results, timestamps
- Consider PDF generation for formatted reports (using `weasyprint` or similar)

---

## Appendix: Feature Comparison Matrix

| Feature | Slido Free | Slido Paid | Pulse Board | Gap? |
|---------|-----------|-----------|-------------|------|
| Text topic submission | -- | -- | Yes | No |
| Up/downvoting | -- | -- | Yes | No |
| Real-time updates (WebSocket) | Yes | Yes | Yes | No |
| Anonymous participation | Yes | Yes | Yes | No |
| Browser fingerprinting | -- | -- | Yes | No (PB advantage) |
| Vote censure (auto-removal) | -- | -- | Yes | No (PB unique) |
| Q&A with upvoting | Yes | Yes | Partial* | Yes |
| Multiple choice polls | Yes | Yes | No | **Yes** |
| Word cloud polls | Yes | Yes | No | **Yes** |
| Rating polls | Yes | Yes | No | **Yes** |
| Open text polls | Yes | Yes | No | **Yes** |
| Ranking polls | Yes | Yes | No | **Yes** |
| Quizzes with leaderboard | Yes (1/event) | Yes | No | **Yes** |
| Surveys (multi-question) | Yes | Yes | No | **Yes** |
| Event/session management | Yes | Yes | No | **Yes** |
| Event join codes | Yes | Yes | No | **Yes** |
| Passcode protection | Yes | Yes | No | **Yes** |
| Present mode | Yes | Yes | No | **Yes** |
| 30+ display themes | Yes | Yes | No | **Yes** |
| QR code for joining | Yes | Yes | No | **Yes** |
| Image/GIF in polls | Yes | Yes | No | **Yes** |
| Question moderation | No | Yes | No | Yes (paid) |
| Custom branding | No | Yes | No | Yes (paid) |
| Data export | No | Yes | No | Yes (paid) |
| Analytics dashboard | Basic | Full | No | **Yes** |
| Sentiment analysis | No | Yes | No | Yes (paid) |
| Multiple rooms | No | Yes | No | Yes (paid) |
| PowerPoint integration | Yes | Yes | No | **Yes** |
| Google Slides integration | Yes | Yes | No | **Yes** |
| Teams integration | Yes | Yes | No | **Yes** |
| Zoom integration | Yes | Yes | No | **Yes** |
| Webex integration | Yes | Yes | No | **Yes** |
| SSO | No | Yes | No | Yes (paid) |

*Pulse Board's topic submission with voting is conceptually similar to Q&A but lacks upvote-only mode, question status tracking, and advance collection.

---

## Sources

- [Slido Pricing Page](https://www.slido.com/pricing)
- [Slido Product Features](https://www.slido.com/product)
- [Slido Live Q&A Features](https://www.slido.com/features-live-qa)
- [Slido Analytics Features](https://www.slido.com/features-analytics)
- [Slido Word Cloud Features](https://www.slido.com/features-word-cloud)
- [Slido Integrations](https://www.slido.com/features-integrations)
- [Slido Community: Free Plan Details](https://community.slido.com/slido-for-powerpoint-74/what-included-in-the-free-plan-6781)
- [Slido Community: Present Mode](https://community.slido.com/frequently-asked-questions-70/what-are-different-modes-in-slido-417)
- [Slido Community: Multiple Rooms](https://community.sli.do/setting-up-a-slido-event-82/set-up-multiple-rooms-in-your-event-412)
- [Slido Community: Event Codes](https://community.slido.com/creating-testing-your-slido-208/what-is-a-slido-code-and-how-to-change-it-406)
- [Slido Pricing Analysis (Wooclap)](https://www.wooclap.com/en/blog/slido-pricing/)
- [Slido Reviews on G2](https://www.g2.com/products/slido/reviews)
- [Slido on Capterra](https://www.capterra.com/p/154051/Slido/)
