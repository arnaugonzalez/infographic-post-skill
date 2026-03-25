---
phase: 06-linkedin-post-generator
plan: "03"
subsystem: testing
tags: [stderr, stdout, token-budget, capsys, gap-closure]

# Dependency graph
requires:
  - phase: 04-codebase-reader-foundation
    provides: scripts/read_codebase.py with token budget enforcement
provides:
  - GAP-3 closed: token budget warning redirected from stdout to stderr in read_codebase.py
affects: [any consumer calling read_codebase() that captures stdout, generate_posts.py CLI JSON output]

# Tech tracking
tech-stack:
  added: []
  patterns: [print to sys.stderr for diagnostic messages, capsys.readouterr().err for stderr assertions]

key-files:
  created: []
  modified:
    - scripts/read_codebase.py
    - tests/test_read_codebase.py

key-decisions:
  - "GAP-3 resolved: budget warning uses file=sys.stderr so stdout remains clean for machine-parseable JSON output"
  - "Phase 04 decision revised: original capsys capture rationale works equally well with stderr via capsys.readouterr().err"

patterns-established:
  - "Diagnostic/warning print calls use file=sys.stderr to keep stdout clean for data output"

requirements-completed: [POSTS-01, POSTS-02]

# Metrics
duration: 5min
completed: 2026-03-25
---

# Phase 06 Plan 03: GAP-3 Budget Warning Stderr Redirect Summary

**Token budget exclusion warnings redirected from stdout to stderr in read_codebase.py, closing GAP-3 and ensuring clean stdout for machine-parseable JSON output**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-25T18:36:00Z
- **Completed:** 2026-03-25T18:41:49Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Redirected both print() calls in the budget_excluded block to use `file=sys.stderr`
- Updated existing test `test_budget_exclusion_message_printed` to assert `captured.err` instead of `captured.out`
- Added new explicit test `test_budget_warning_goes_to_stderr_not_stdout` verifying stdout is clean
- Full test suite: 80 tests pass (up from 79)

## Task Commits

Each task was committed atomically:

1. **Task 1: Redirect budget warning to stderr and update tests** - `5304ba0` (fix)

## Files Created/Modified

- `scripts/read_codebase.py` - Two print() calls in budget_excluded block now use `file=sys.stderr`
- `tests/test_read_codebase.py` - Updated existing test + added new GAP-3 explicit test

## Decisions Made

- GAP-3 closed: budget warning uses `file=sys.stderr` so stdout remains clean for machine-parseable JSON output from CLI consumers
- Phase 04 decision revised: original rationale (stdout for capsys capture) no longer valid — capsys captures stderr equally well via `capsys.readouterr().err`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GAP-3 closed: stdout is now clean for any consumer of read_codebase()
- generate_posts.py CLI JSON output will not be contaminated by budget warnings
- All 3 gap-closure plans (GAP-1, GAP-2, GAP-3) are complete

## Self-Check

- [x] `scripts/read_codebase.py` contains `file=sys.stderr` (2 occurrences in budget_excluded block)
- [x] `tests/test_read_codebase.py` contains `test_budget_warning_goes_to_stderr_not_stdout`
- [x] Commit `5304ba0` exists
- [x] 80 tests pass

---
*Phase: 06-linkedin-post-generator*
*Completed: 2026-03-25*
