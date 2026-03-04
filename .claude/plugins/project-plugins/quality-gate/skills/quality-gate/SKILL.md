---
name: quality-gate
description: >-
  This skill should be used when the user asks to "run quality checks",
  "run the quality gate", "check code quality", "make sure everything passes",
  "run all checks", "validate the build", "pre-PR checks", "ensure tests pass",
  "run lint and tests", "quality assurance pass", or any request involving
  running linting, testing, and end-to-end validation with automated repair.
  Also trigger when the user uses "/quality-gate" or asks to "fix all failing checks".
---

# Quality Gate

Run all project quality checks in sequence, automatically diagnosing and repairing failures before proceeding. The gate repeats until every check passes cleanly with no errors or warnings.

## Quality Check Sequence

Execute these checks in strict order. After each check, evaluate the output before proceeding.

1. **Lint** - `make lint` (ruff check, ruff format, pyright, eslint)
2. **Unit Tests** - `make test` (Python unit tests with coverage)
3. **All Tests** - `make test-all` (unit + integration + frontend tests)
4. **E2E Tests** - `make test-e2e` (Playwright end-to-end tests)

## Core Workflow

### Phase 1: Sequential Check with Stop-on-Failure

Run each check in sequence. **Stop immediately when a check fails** - do not continue to the next check.

```text
for each check in [lint, test, test-all, test-e2e]:
    run the check
    if errors or warnings found:
        enter Repair Phase for this check
        restart from the first check (lint)
    if clean:
        proceed to next check
```

### Phase 2: Repair Loop

When a check fails:

1. **Diagnose** - Launch the `root-cause-analyst` agent to analyze the failure output and identify the true root cause
2. **Navigate** - Use LSP to understand the failing code before making changes:
   - `goToDefinition` to inspect the source of failing symbols
   - `findReferences` to assess impact before modifying any signature or type
   - `hover` to verify types at error locations
   - `incomingCalls`/`outgoingCalls` to trace call graphs when failures span multiple files
   - `documentSymbol` to understand file structure before editing
3. **Fix** - Use the appropriate sub-agent to implement the repair:
   - Lint/format issues: Fix directly or use `python-expert` agent for Python, handle frontend ESLint issues directly
   - Python test failures: Use `python-expert` agent
   - Frontend test failures: Fix directly with knowledge of React/TypeScript/Vitest patterns
   - E2E test failures: Fix directly with knowledge of Playwright patterns
   - Architecture issues: Use `system-architect` agent for design-level problems
   - If a referenced agent is unavailable, perform the diagnosis or repair directly without delegation
4. **Re-run from start** - After any repair, restart the entire check sequence from `make lint`. Do not skip ahead.

### Phase 3: Clean Pass Verification

After all four checks pass without errors or warnings:

- If **no edits were made** during this quality gate session: sign off as complete
- If **any edits were made** to fix issues:
  1. Run the `/simplify` command on the modified code
  2. Run one final pass of all four quality checks
  3. If the final pass is clean: sign off as complete
  4. If the final pass has failures: re-enter the Repair Loop

## Execution Rules

### Stop-on-Failure
Never skip a failing check to run later ones. Each check must pass before moving to the next. When a failure is repaired, always restart from the beginning of the sequence.

### Track Edits
Maintain awareness of whether any files were modified during the quality gate session. This determines whether the `/simplify` + final pass is needed.

### Warnings Are Failures
Treat warnings the same as errors. The quality gate passes only when output is completely clean.

### Repair Attempt Limits
If the same check fails 3 times consecutively with the same root cause after attempted repairs, stop and report the issue to the user rather than looping indefinitely. Present the diagnosis, attempted fixes, and ask for guidance.

### Infrastructure Requirements
Some checks require Docker infrastructure (`make test-all`, `make test-e2e`). If infrastructure is not running, `make` targets handle starting it automatically. If Docker is unavailable, report which checks could not run.

## Output Format

After completion, provide a summary:

```text
Quality Gate: PASSED

Checks completed:
  - lint:     PASS
  - test:     PASS
  - test-all: PASS
  - test-e2e: PASS

Repairs made: [number of repair cycles, or "none"]
Simplify pass: [yes/no]
```

If the gate cannot pass after repair attempts:

```text
Quality Gate: BLOCKED

Failing check: [check name]
Root cause: [diagnosis summary]
Attempted fixes: [list of what was tried]
Action needed: [what the user should do]
```
