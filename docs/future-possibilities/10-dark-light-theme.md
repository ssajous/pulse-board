# 10: Dark/Light Theme Toggle

## Category

Accessibility & UX

## Complexity

Small

## Overview

Implement a dark/light theme toggle that allows users to switch between color schemes. The theme preference is persisted in `localStorage` and respects the operating system's `prefers-color-scheme` setting as the default. Tailwind CSS's built-in dark mode support makes this a straightforward enhancement.

## Problem Statement

The current board uses a single color scheme. Users who prefer dark mode for reduced eye strain, better visibility in low-light environments, or personal preference have no way to customize the appearance. Dark mode has become a baseline UX expectation for modern web applications.

## User Stories

1. **As a user**, I want to toggle between dark and light themes so I can choose the appearance that's most comfortable for my environment.
2. **As a user**, I want the board to default to my OS theme preference so it matches my system settings on first visit.
3. **As a returning user**, I want my theme preference to persist across sessions so I don't have to toggle it every time.

## Design Considerations

### Tailwind CSS Dark Mode

Tailwind CSS supports dark mode via the `class` strategy (recommended over `media` for manual toggle support):

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  // ...
}
```

When the `dark` class is present on the `<html>` element, all `dark:` variant utilities activate:

```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
```

### Color Palette

| Element | Light | Dark |
|---------|-------|------|
| Background | `white` | `gray-900` |
| Card background | `gray-50` | `gray-800` |
| Primary text | `gray-900` | `gray-100` |
| Secondary text | `gray-600` | `gray-400` |
| Border | `gray-200` | `gray-700` |
| Accent (upvote) | `green-600` | `green-400` |
| Accent (downvote) | `red-600` | `red-400` |
| Input background | `white` | `gray-800` |
| Input border | `gray-300` | `gray-600` |

### Frontend Architecture

**Theme Toggle Component**:
- Sun/moon icon button in the `Header`
- Toggles `dark` class on `<html>` element
- Simple, accessible button with `aria-label="Toggle dark mode"`

**Theme Management**:
- Store preference in `localStorage` under key `pulse-board-theme`
- On initial load:
  1. Check `localStorage` for saved preference
  2. If none, check `window.matchMedia('(prefers-color-scheme: dark)')`
  3. Apply the resolved theme before first render (avoid flash of wrong theme)

**ViewModel Integration**:
- `ThemeViewModel` (lightweight, could be part of a root AppViewModel):
  - `theme: 'light' | 'dark'` observable
  - `toggleTheme()` action
  - `isDark: boolean` computed
  - Initializer reads from `localStorage` / system preference

**Flash Prevention**:
Add a script in `index.html` `<head>` (before React mounts) to apply the theme class immediately:

```html
<script>
  (function() {
    const saved = localStorage.getItem('pulse-board-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (saved === 'dark' || (!saved && prefersDark)) {
      document.documentElement.classList.add('dark');
    }
  })();
</script>
```

### Component Updates

All existing components need `dark:` variants added to their Tailwind classes. Key components:

- `Header`: background, text color, border
- `TopicCard`: card background, text, vote button colors
- `TopicForm`: input background, border, placeholder text
- `Toast`: background, text, border
- `TopicListEmpty`: text and icon colors

### Transition Animation

Smooth theme transitions using CSS:

```css
html {
  transition: background-color 0.2s ease, color 0.2s ease;
}
```

Respect `prefers-reduced-motion` by disabling the transition.

## Dependencies

- Phase 1 (Project Foundation) -- Tailwind CSS already configured
- No backend changes required

## Open Questions

1. Should the toggle be a button (icon only) or a switch component?
2. Should there be a "system" option in addition to light/dark (three-way toggle)?
3. Should the theme preference sync across tabs using `localStorage` events?
