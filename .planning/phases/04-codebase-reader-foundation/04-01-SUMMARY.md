---
phase: 04-codebase-reader-foundation
plan: 01
subsystem: codebase-reader
tags: [pathspec, gitignore, credential-safety, noise-filter, binary-detection, redaction]

# Dependency graph
requires: []
provides:
  - read_codebase() function with noise-filtered directory walk
  - DEFAULT_SKIP_DIRS constant (22 artifact/tool directories)
  - DEFAULT_CREDENTIAL_FILES constant (.env, credentials.json, service_account.json)
  - CREDENTIAL_EXTENSIONS constant (.pem, .key, .p12, .pfx, .jks)
  - _SECRET_PATTERNS for 5 key families (AIza, sk-or-v1, sk-, ghp_, generic api_key=value)
  - pathspec gitignore integration with graceful degradation when unavailable
  - 18 passing unit tests for CODEBASE-01 and CODEBASE-03
affects: [04-02, 04-03, 05-linkedin-post-generator]

# Tech tracking
tech-stack:
  added: [pathspec>=0.12.1]
  patterns:
    - Try-import with _PATHSPEC_OK flag for optional dependency graceful degradation
    - Module-level _SECRET_PATTERNS list of compiled re.compile() patterns
    - In-place os.walk dirnames[:] pruning for early directory skip
    - <file path="rel_path"> delimiters in summary_text for structured LLM context

key-files:
  created:
    - scripts/read_codebase.py
    - tests/test_read_codebase.py
  modified:
    - requirements.txt

key-decisions:
  - "Use 'gitignore' pattern type (not deprecated 'gitwildmatch') for pathspec.PathSpec.from_lines"
  - "Credential files unconditionally skipped (not just redacted) — safety-first approach"
  - "Secret patterns defined independently in read_codebase.py (not imported from generate_pretty.py) — avoids coupling"
  - "service_account*.json matched via name.startswith() + suffix check, not glob — explicit > magic"
  - "Stub layers/connections as empty lists — populated in Plan 02"

patterns-established:
  - "Noise filter: prune dirs in-place via dirnames[:] before os.walk descends"
  - "Credential check: exact name match OR extension match OR name prefix match (.startswith)"
  - "Binary check: read first 1024 bytes, look for null byte b'\\x00'"
  - "Content redaction: apply all _SECRET_PATTERNS sequentially at read time, before accumulating"

requirements-completed: [CODEBASE-01, CODEBASE-03]

# Metrics
duration: 3min
completed: 2026-03-25
---

# Phase 4 Plan 01: Codebase Reader Foundation Summary

**Noise-filtered codebase reader with unconditional credential skip, 5-pattern content redaction, and pathspec gitignore support — all 18 safety tests passing.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T10:36:48Z
- **Completed:** 2026-03-25T10:40:10Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 3

## Accomplishments

- Built `read_codebase()` with os.walk + in-place directory pruning for 22 skip dirs
- Implemented credential safety: unconditional skip of `.env`, `credentials.json`, `.pem`/`.key`/etc., `service_account*.json`
- Added 5 _SECRET_PATTERNS (Google AIza, OpenRouter sk-or-v1, sk-, GitHub ghp_, generic api_key=value) applied at read time
- Integrated pathspec gitignore support with try-import graceful degradation
- All 18 new tests pass; all 35 tests in the suite green

## Task Commits

Each task was committed atomically:

1. **Task 1: Setup + RED — Failing tests and stub** - `efea225` (test)
2. **Task 2: GREEN — Full implementation** - `3935f1b` (feat)

## Files Created/Modified

- `scripts/read_codebase.py` - Core reader: noise filter, binary detection, credential skip, content redaction, pathspec gitignore, CLI entry point
- `tests/test_read_codebase.py` - 18 unit tests: TestNoiseFilter (6), TestBinaryFilter (3), TestCredentialSkip (4), TestContentRedaction (5)
- `requirements.txt` - Added `pathspec>=0.12.1`

## Decisions Made

- Used `'gitignore'` pattern type instead of deprecated `'gitwildmatch'` in `pathspec.PathSpec.from_lines()` — eliminates DeprecationWarning in pathspec 1.0+
- Defined `_SECRET_PATTERNS` independently in `read_codebase.py` rather than importing from `generate_pretty.py` — avoids coupling between modules; each module owns its safety contracts
- `layers` and `connections` returned as empty lists — Plan 02 will populate these with AST analysis

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pathspec DeprecationWarning**
- **Found during:** Task 2 (GREEN phase, running full test suite)
- **Issue:** `pathspec.PathSpec.from_lines("gitwildmatch", ...)` triggers DeprecationWarning in pathspec 1.0+ — correct type is `"gitignore"`
- **Fix:** Changed pattern type string from `"gitwildmatch"` to `"gitignore"` in `_build_noise_filter()`
- **Files modified:** `scripts/read_codebase.py`
- **Verification:** Full test suite runs with 0 pathspec warnings
- **Committed in:** `3935f1b` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug)
**Impact on plan:** Fix was necessary; pattern type was documented as deprecated and would fail in future pathspec versions.

## Issues Encountered

None — TDD flow worked cleanly. RED phase had 7 failures (correct), GREEN phase passed all 18 on first run.

## User Setup Required

None — pathspec is installed via `pip install pathspec>=0.12.1` (or `requirements.txt`). No external API keys or services required.

## Next Phase Readiness

- `read_codebase()` is the foundation for Plan 02 (token budgeting + AST-based layers/connections)
- Exports `read_codebase`, `DEFAULT_SKIP_DIRS`, `DEFAULT_CREDENTIAL_FILES` — all referenced in Plan 02
- Full test suite green — safe to build on

---
*Phase: 04-codebase-reader-foundation*
*Completed: 2026-03-25*
