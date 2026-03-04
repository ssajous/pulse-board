---
description: "Run all quality checks (lint, test, test-all, test-e2e) with automated repair"
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - LSP
  - Agent
  - Skill
---

Run the full quality gate workflow. Execute all quality checks in strict sequence, automatically diagnosing and repairing any failures before proceeding.

## Quality Check Sequence

Execute in this order, stopping on the first failure:

1. **Lint** — `make lint`
2. **Unit Tests** — `make test`
3. **All Tests** — `make test-all`
4. **E2E Tests** — `make test-e2e`

## Workflow

### Step 1: Run checks sequentially with stop-on-failure

Run each check one at a time. If a check fails (errors or warnings), stop immediately — do not continue to the next check. Proceed to Step 2.

If all four checks pass cleanly, skip to Step 4.

### Step 2: Diagnose and repair

1. Launch the `root-cause-analyst` agent to analyze the failure output and identify the root cause
2. Use the appropriate sub-agent to fix:
   - Lint/format issues: Fix directly or use `python-expert` agent for Python
   - Python test failures: Use `python-expert` agent
   - Frontend test/lint failures: Fix directly
   - E2E test failures: Fix directly
   - Architecture issues: Use `system-architect` agent
   - If a sub-agent is unavailable, perform the repair directly

### Step 3: Restart from the beginning

After any repair, go back to Step 1 and re-run all checks from `make lint`. Do not skip ahead.

If the same check fails 3 times with the same root cause, stop and report the issue to the user.

### Step 4: Clean pass verification

After all four checks pass:

- If **no edits were made** during this session: report success
- If **any edits were made**:
  1. Run `/simplify` on the modified code
  2. Run one final pass of all four checks (Steps 1-3)
  3. Report success when clean

### Step 5: Report results

Provide a summary:

```text
Quality Gate: PASSED

Checks completed:
  - lint:     PASS
  - test:     PASS
  - test-all: PASS
  - test-e2e: PASS

Repairs made: [count or "none"]
Simplify pass: [yes/no]
```

Or if blocked:

```text
Quality Gate: BLOCKED

Failing check: [name]
Root cause: [diagnosis]
Attempted fixes: [what was tried]
Action needed: [guidance for user]
```
