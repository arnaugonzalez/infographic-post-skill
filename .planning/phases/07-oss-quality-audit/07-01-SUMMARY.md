---
phase: 07-oss-quality-audit
plan: 01
subsystem: testing
tags: [coverage, flake8, ast, audit, quality]

# Dependency graph
requires: []
provides:
  - oss_audit.py with five core data-collection functions (_run_coverage, _check_docstrings, _check_oss_files, _run_flake8, _branch_complexity)
  - .coveragerc scoping coverage to scripts/
  - requirements-audit.txt listing audit-only dependencies
  - tests/test_oss_audit.py with 9 tests covering AUDIT-01, AUDIT-02, AUDIT-03
affects:
  - 07-02 (report generation uses these functions as data layer)
  - 07-03 (CLI entry point calls these functions)

# Tech tracking
tech-stack:
  added: [coverage>=7.0, flake8>=6.0]
  patterns:
    - subprocess.run with capture_output=True (never check=True) for graceful degradation
    - ast.walk + isinstance for Python AST analysis without external tools
    - graceful-degrade pattern: return empty container when tool missing, not exception

key-files:
  created:
    - oss_audit.py
    - tests/test_oss_audit.py
    - .coveragerc
    - requirements-audit.txt
  modified: []

key-decisions:
  - "Audit-only deps (coverage, flake8) in requirements-audit.txt, not requirements.txt"
  - "All five functions return empty containers (not exceptions) when tools missing"
  - "flake8 --select=F via subprocess; ast branch-node counter for complexity (avoids radon/mccabe)"
  - "coverage run invoked via subprocess.run in project_root cwd to pick up .coveragerc automatically"

patterns-established:
  - "Pattern 1: Tool-optional subprocess wrapper — check stderr for 'No module named'; return {} on failure"
  - "Pattern 2: AST traversal — ast.parse + ast.walk + isinstance check + ast.get_docstring for docstring detection"
  - "Pattern 3: TDD with mocked subprocess — patch subprocess.run with side_effect writing fixture files"

requirements-completed: [AUDIT-01, AUDIT-02, AUDIT-03]

# Metrics
duration: 2min
completed: 2026-03-25
---

# Phase 7 Plan 01: OSS Audit Core Functions Summary

**Five AST+subprocess audit functions with TDD: coverage measurement, docstring gap detection, OSS file presence, flake8 F-code parsing, and branch complexity counting via ast.walk**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T19:18:06Z
- **Completed:** 2026-03-25T19:20:28Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 4

## Accomplishments

- `_run_coverage`: Runs `python3 -m coverage run+json`, parses percent_covered per module, cleans up coverage.json, returns {} when coverage missing
- `_check_docstrings`: ast.walk over FunctionDef/AsyncFunctionDef/ClassDef nodes, flags missing docstrings with qualified name and line number
- `_check_oss_files`: Dict comprehension checking presence of README.md, LICENSE, .env.example, CHANGELOG.md, CHANGELOG
- `_run_flake8`: Subprocess flake8 --select=F, parses colon-delimited output, returns [] when flake8 not installed
- `_branch_complexity`: ast.walk counts branch nodes (If/For/While/Try/ExceptHandler/With) per function, flags above COMPLEXITY_THRESHOLD=5
- All 9 tests pass; full suite at 95/95 (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Config files and test scaffold (RED phase)** - `99c99e0` (test)
2. **Task 2: Implement all five core functions (GREEN phase)** - `103c035` (feat)

**Plan metadata:** (docs commit, pending)

_Note: TDD tasks have two commits — test (RED) then feat (GREEN)_

## Files Created/Modified

- `oss_audit.py` - Five core audit functions with graceful degradation
- `tests/test_oss_audit.py` - 9 tests: TestCoverage (2), TestDocstringCoverage (2), TestOSSFiles (1), TestFlake8 (2), TestComplexity (2)
- `.coveragerc` - `source = scripts` to scope coverage measurement
- `requirements-audit.txt` - `coverage>=7.0`, `flake8>=6.0` (audit-only, not in requirements.txt)

## Decisions Made

- Audit-only dependencies kept in `requirements-audit.txt` to avoid polluting the main requirements.txt for normal skill users
- All functions return empty containers (not exceptions) when tools are missing — audit script should always complete, even on minimal installs
- `flake8 --select=F` restricts to import/undefined-name errors (actionable) rather than style warnings
- Coverage invoked via subprocess in project_root cwd so `.coveragerc source = scripts` applies automatically

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All five data-collection functions ready for use by 07-02 (report generation)
- Functions return typed, structured data suitable for formatting into QUALITY_AUDIT.md
- COMPLEXITY_THRESHOLD exported for use in report thresholds

---
*Phase: 07-oss-quality-audit*
*Completed: 2026-03-25*
