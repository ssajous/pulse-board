# ADR 003: Browser Fingerprinting -- FingerprintJS v5 for Anonymous User Identification

## Status

Accepted

## Date

2024-12-01

## Context and Problem Statement

The Community Pulse Board allows users to upvote and downvote topics. Without user accounts or authentication, the system needs a mechanism to identify returning visitors so that each person can cast only one vote per topic. The identification method must work without requiring login, be resistant to casual manipulation (clearing cookies, using incognito mode), and respect user privacy by not collecting personally identifiable information.

## Decision Drivers

- **No authentication required**: The platform must be usable immediately without sign-up, login, or any account creation flow
- **Vote manipulation resistance**: The identification mechanism must survive cookie clearing, incognito browsing, and basic evasion attempts
- **Privacy preservation**: The system must not collect PII (names, emails, IP addresses) or enable cross-site tracking
- **Identification accuracy**: The mechanism must reliably identify returning visitors to enforce one-vote-per-topic rules
- **Integration simplicity**: The solution must work as a client-side library with minimal backend changes
- **Performance**: Fingerprint generation must complete fast enough to not block the voting interaction

## Considered Options

1. FingerprintJS v5 (open-source, client-side browser fingerprinting)
2. Cookie-based tracking (first-party cookies with unique identifiers)
3. IP-based tracking (server-side identification by client IP address)
4. Required authentication (email/password or OAuth sign-in)

## Decision Outcome

We chose **Option 1: FingerprintJS v5** because it identifies returning visitors with approximately 99.5% accuracy without requiring cookies, user accounts, or server-side IP logging. The library generates a `visitorId` hash from browser attributes (canvas rendering, WebGL, audio context, installed fonts, screen properties) that persists across sessions and incognito mode. The fingerprint is computed client-side, cached in the `FingerprintService` (see `frontend/src/infrastructure/fingerprint/fingerprintService.ts`), and sent with each vote request as the voter identifier.

### Consequences

- **Good**: Users can vote immediately on their first visit -- no registration wall, no cookie consent banner for tracking cookies.
- **Good**: The fingerprint survives cookie clearing and incognito mode, making casual vote manipulation significantly harder than cookie-based approaches.
- **Good**: The `visitorId` is a one-way hash that cannot be reversed to identify a specific person or their browsing habits.
- **Good**: The `FingerprintPort` interface in the domain layer (see `frontend/src/domain/ports/FingerprintPort.ts`) decouples the application from the FingerprintJS implementation, allowing substitution for testing or future migration.
- **Good**: The fingerprint is cached after first computation (`this.cachedId` in `FingerprintService`), so subsequent votes do not re-run the fingerprinting algorithm.
- **Bad**: Browser updates, OS upgrades, or significant hardware changes can alter the fingerprint, causing a user to appear as a new visitor and potentially allowing duplicate votes.
- **Bad**: Privacy-focused browsers (Brave, Firefox with enhanced tracking protection) may interfere with fingerprinting signals, reducing accuracy for those users.
- **Bad**: Users on shared computers (libraries, labs) may be unable to vote independently if their browser configurations produce identical fingerprints.
- **Neutral**: The open-source FingerprintJS v5 provides client-side identification only; server-side identification and higher accuracy would require the commercial FingerprintJS Pro service.

## Pros and Cons of the Options

### Option 1: FingerprintJS v5 (Open Source)

- **Good**: Approximately 99.5% identification accuracy for returning visitors across sessions.
- **Good**: Works without cookies -- survives cookie clearing and private browsing modes.
- **Good**: Client-side only -- no additional backend infrastructure required beyond accepting the fingerprint ID in vote requests.
- **Good**: Open source (MIT license) with no per-request pricing.
- **Good**: Integrates as an npm dependency (`@fingerprintjs/fingerprintjs ^5.0.1`) with a simple async API: `FingerprintJS.load()` then `fp.get()`.
- **Bad**: Fingerprint stability depends on browser environment consistency -- changes in browser version, OS, or hardware may generate a new ID.
- **Bad**: Cannot distinguish between different users on the same browser/device combination.
- **Bad**: Some ad blockers and privacy tools may block the fingerprinting scripts or degrade signal quality.
- **Neutral**: The `visitorId` is deterministic for a given browser configuration, meaning it does not change between visits but may change after updates.

### Option 2: Cookie-Based Tracking

- **Good**: Simple to implement -- set a UUID cookie on first visit and read it on subsequent requests.
- **Good**: Well-understood mechanism with universal browser support.
- **Good**: No external library dependency.
- **Bad**: Trivially defeated by clearing cookies, using incognito/private browsing, or switching browsers.
- **Bad**: Requires a cookie consent banner in jurisdictions governed by GDPR, ePrivacy Directive, or similar regulations.
- **Bad**: Provides no resistance against intentional vote manipulation -- any technically literate user can vote multiple times.
- **Neutral**: Cookies have a configurable expiration, allowing some control over session duration.

### Option 3: IP-Based Tracking

- **Good**: No client-side code required -- identification happens entirely on the server.
- **Good**: Cannot be cleared or manipulated by the user without network-level changes.
- **Bad**: NAT, VPNs, and corporate proxies cause many unrelated users to share the same IP address, resulting in false positives that block legitimate votes.
- **Bad**: Mobile users frequently change IP addresses as they switch between cellular and Wi-Fi networks, creating false negatives.
- **Bad**: Logging IP addresses raises privacy concerns and may require compliance with data protection regulations.
- **Bad**: Highly inaccurate as a user identification mechanism -- both over-counts (different users same IP) and under-counts (same user different IP).

### Option 4: Required Authentication

- **Good**: Definitive user identification -- each authenticated account maps to exactly one person.
- **Good**: Prevents all forms of anonymous vote manipulation (assuming email verification or OAuth).
- **Good**: Enables additional features like vote history, user profiles, and moderation tools.
- **Bad**: Introduces a registration barrier that dramatically reduces participation in a community engagement tool designed for low-friction interaction.
- **Bad**: Requires implementing and maintaining an authentication system (password hashing, session management, password reset, OAuth flows).
- **Bad**: Requires collecting and securely storing PII (email addresses, passwords), introducing data protection compliance obligations.
- **Bad**: Contradicts the core product requirement of immediate, anonymous participation.

## More Information

- [FingerprintJS open-source documentation](https://github.com/nicedaycode/FingerprintJS)
- Fingerprint port interface: `frontend/src/domain/ports/FingerprintPort.ts`
- Fingerprint service implementation: `frontend/src/infrastructure/fingerprint/fingerprintService.ts`
- Vote casting with fingerprint: `frontend/src/presentation/view-models/TopicsViewModel.ts` (see `castVote` method, which passes `this.fingerprintId` to the vote API)
- Backend vote endpoint receives the fingerprint as the voter identifier in the request body
