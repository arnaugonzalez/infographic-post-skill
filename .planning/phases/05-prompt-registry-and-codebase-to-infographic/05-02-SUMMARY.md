---
phase: 05-prompt-registry-and-codebase-to-infographic
plan: "02"
subsystem: cli
tags: [python, argparse, codebase-reader, infographic, arch-diagram, tdd]

# Dependency graph
requires:
  - phase: 05-01
    provides: _PROMPT_STRATEGIES registry, _get_strategy(), _model_family() (implemented as prereq in this plan)
  - phase: 04-codebase-reader-foundation
    provides: read_codebase() function returning CodebaseReport dict with layers/summary_text/connections
provides:
  - "--codebase <dir> CLI flag in generate_pretty.py wired to read_codebase()"
  - "_config_from_codebase_report(report, title, subtitle, author, cta) -> (config, viz_type)"
  - "Title derivation from directory name when --title is the argparse default"
  - "viz_type forced to 'arch' for codebase infographics"
  - "tests/test_generate_pretty.py with TestPromptRegistry (8 tests) + TestCodebaseFlag (4 tests)"
affects: [05-03, skill-md-update, downstream-cli-users]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CodebaseReport-to-config mapping via dedicated _config_from_codebase_report() function"
    - "viz_type override pattern: codebase branch returns 'arch' tuple, other branches use args.type"
    - "Title derivation: Path(root).name.replace('-',' ').replace('_',' ').title()"

key-files:
  created:
    - tests/test_generate_pretty.py
  modified:
    - scripts/generate_pretty.py

key-decisions:
  - "D-05: viz_type always 'arch' for codebase infographics — _config_from_codebase_report returns tuple (config, 'arch')"
  - "D-06: report['summary_text'] maps to config['description'] (not report['summary'] which doesn't exist)"
  - "D-07: title derived from Path(root).name when title == 'System Architecture' (argparse default)"
  - "D-08: from read_codebase import read_codebase inside elif branch (lazy import via existing sys.path)"
  - "Implemented 05-01 registry prerequisite in same plan execution due to parallel worktree isolation"

patterns-established:
  - "Parallel executor pattern: implement missing prerequisite work within the dependent plan when worktrees are isolated"
  - "CLI elif chain: each branch sets viz_type variable, final call uses viz_type not args.type"

requirements-completed: [PROMPTREG-01]

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 05 Plan 02: Codebase-to-Infographic CLI Flag Summary

**`--codebase <dir>` flag wired into generate_pretty.py with CodebaseReport mapping, title derivation from directory name, and arch viz_type enforcement**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T12:56:44Z
- **Completed:** 2026-03-25T13:00:17Z
- **Tasks:** 2 (RED + GREEN, TDD)
- **Files modified:** 2

## Accomplishments

- Created `tests/test_generate_pretty.py` with 12 tests: 8 for TestPromptRegistry (05-01 prereq) + 4 for TestCodebaseFlag
- Implemented `_config_from_codebase_report()` function mapping CodebaseReport to (config, viz_type) tuple
- Added `--codebase <dir>` argparse flag wired to `read_codebase()` via lazy import (D-08)
- Title derivation from directory name when user doesn't set `--title` (D-07)
- viz_type forced to `"arch"` for all codebase infographics (D-05)
- Full test suite: 63 tests passing with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Create failing tests for --codebase flag** - `53a4e82` (test)
2. **Prereq: 05-01 registry implementation** - `cdeaac5` (feat)
3. **Task 2: GREEN — Implement --codebase flag and CodebaseReport mapping** - `fa33f05` (feat)

_Note: TDD tasks have test commit then implementation commit._

## Files Created/Modified

- `tests/test_generate_pretty.py` - New test file with TestPromptRegistry (8 tests) and TestCodebaseFlag (4 tests)
- `scripts/generate_pretty.py` - Added _model_family(), _PROMPT_STRATEGIES registry, _get_strategy(), _warn_if_stale(), _config_from_codebase_report(), --codebase argparse flag, elif args.codebase branch

## Decisions Made

- **Prereq implementation inline:** The 05-01 registry changes (deleting `_supports_icons`, adding `_PROMPT_STRATEGIES`) were not present in this worktree due to parallel execution. Implemented them as a prerequisite within this plan's execution to unblock the TestPromptRegistry GREEN requirement.
- **Tuple return signature:** `_config_from_codebase_report` returns `(config, viz_type)` tuple so the caller receives the forced `"arch"` value cleanly without needing the caller to override.
- **viz_type variable flow:** Added `viz_type = args.type` for config/layers branches (text branch already sets it). The final `generate_pretty()` call uses `viz_type` instead of `args.type` to support the codebase override.

## Deviations from Plan

None - plan executed exactly as written (with the addition of 05-01 prereq work which was missing from this worktree due to parallel execution).

## Issues Encountered

This worktree (agent-a75f562f) is running as a parallel executor alongside agent-ab832c4a which is executing 05-01. Since git worktrees are isolated, the 05-01 registry changes hadn't landed in this branch. The plan acceptance criteria requires "Plan 01's 8 TestPromptRegistry tests remain GREEN", so the prerequisite registry changes were implemented here as well. Both plans implement the same registry changes; the final merge will produce a clean unified diff.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `--codebase <dir>` flag is fully functional; users can run `python generate_pretty.py --codebase ./my-project` to generate architecture infographics from a codebase directory
- TestCodebaseFlag tests (4) + TestPromptRegistry tests (8) are Green
- Full suite 63 tests passing
- Next: any downstream consumers (SKILL.md documentation update, LinkedIn post generator) can rely on CodebaseReport-to-config mapping being available

---
*Phase: 05-prompt-registry-and-codebase-to-infographic*
*Completed: 2026-03-25*
