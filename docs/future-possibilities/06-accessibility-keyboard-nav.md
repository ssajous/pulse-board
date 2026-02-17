# 06: Accessibility & Keyboard Navigation

## Category

Accessibility & UX

## Complexity

Medium

## Overview

Implement comprehensive accessibility support including full keyboard navigation, ARIA attributes, screen reader compatibility, focus management, and high-contrast support. This ensures Pulse Board is usable by everyone regardless of ability and brings the application into compliance with WCAG 2.1 AA standards.

## Problem Statement

The current board relies primarily on mouse interaction. Users who navigate with keyboards, screen readers, or other assistive technologies cannot fully interact with the board. This excludes a significant portion of potential users and may create legal compliance issues for organizations required to meet accessibility standards (Section 508, ADA, EN 301 549).

Accessibility is not a feature -- it is a baseline requirement for any public-facing web application.

## User Stories

1. **As a keyboard-only user**, I want to navigate between topics using Tab/Arrow keys so I can browse the board without a mouse.
2. **As a screen reader user**, I want all interactive elements to have appropriate ARIA labels so I understand what each element does.
3. **As a keyboard user**, I want to submit topics and cast votes using keyboard shortcuts so I have full board functionality.
4. **As a user with low vision**, I want the board to support high-contrast mode so I can distinguish UI elements.
5. **As a user with motion sensitivity**, I want to disable animations so the interface doesn't cause discomfort.

## Design Considerations

### WCAG 2.1 AA Compliance Areas

**Perceivable**:
- All images and icons have `alt` text or `aria-label`
- Color is not the only means of conveying information (vote state uses icons + color)
- Text meets minimum contrast ratio (4.5:1 for normal text, 3:1 for large text)
- Content is readable at 200% zoom

**Operable**:
- All functionality available via keyboard
- No keyboard traps
- Focus indicators visible on all interactive elements
- Skip navigation link to jump past the header

**Understandable**:
- Form inputs have associated labels
- Error messages are descriptive and programmatically associated
- Consistent navigation patterns across the board

**Robust**:
- Valid HTML semantics (proper heading hierarchy, landmark regions)
- ARIA roles and properties used correctly
- Compatible with major screen readers (NVDA, JAWS, VoiceOver)

### Keyboard Navigation Map

| Key | Action |
|-----|--------|
| `Tab` | Move focus to next interactive element |
| `Shift+Tab` | Move focus to previous interactive element |
| `Enter` / `Space` | Activate focused button (submit, vote) |
| `Arrow Up/Down` | Navigate between topic cards |
| `/` or `Ctrl+K` | Focus search bar (if feature 05 is implemented) |
| `Escape` | Close modals, clear search, unfocus |
| `?` | Show keyboard shortcut help overlay |

### Frontend Architecture

**Component Changes**:
- Add `role`, `aria-label`, `aria-live`, `aria-describedby` attributes to all interactive components
- `TopicCard`: `role="article"`, `aria-label="Topic: {text}, Score: {score}"`
- Vote buttons: `aria-label="Upvote topic"` / `aria-label="Downvote topic"`, `aria-pressed="true/false"`
- `TopicForm`: proper `<label>` elements, `aria-required`, `aria-invalid`
- Score updates: `aria-live="polite"` region for real-time score changes
- Toast notifications: `role="alert"` for screen reader announcement

**Focus Management**:
- Custom focus ring styles (visible on keyboard nav, hidden on mouse click using `:focus-visible`)
- Focus trap in modal dialogs (if any are added)
- Return focus to trigger element when modal closes
- Auto-focus on the topic input when the form is expanded

**Skip Navigation**:
- Hidden "Skip to main content" link that becomes visible on focus
- Allows keyboard users to bypass the header and jump to the topic list

**Reduced Motion**:
- Respect `prefers-reduced-motion` media query
- Disable CSS transitions and animations when enabled
- Provide static alternatives for any animated UI elements

### Testing Approach

- Automated: axe-core integration in unit tests and E2E tests
- Manual: keyboard-only navigation testing
- Screen reader: test with VoiceOver (macOS) at minimum
- Contrast: verify with browser DevTools contrast checker

## Dependencies

- Phase 1 (Project Foundation) -- base component structure
- Phase 2 (Topic Management) -- topic list and form components

## Open Questions

1. Should keyboard shortcuts be configurable by the user?
2. Should the board support a "high contrast" theme separate from dark/light mode (feature 10)?
3. What is the testing budget for screen reader compatibility across NVDA, JAWS, and VoiceOver?
