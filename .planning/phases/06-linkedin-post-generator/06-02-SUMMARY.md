---
phase: 06-linkedin-post-generator
plan: "02"
subsystem: content-generation
tags: [python, llm, catalan, language-enforcement, retry, openrouter]

# Dependency graph
requires:
  - phase: 06-linkedin-post-generator
    provides: LinkedIn post generator with two-angle prompts and language enforcement

provides:
  - Negative language constraint for minority/regional languages (GAP-1 closed)
  - Whitespace-aware retry logic stripping LLM responses before char count (GAP-2 closed)
  - Stderr logging when retry fires for operator visibility
  - 6 new gap-closure tests (22 total in generate_posts, 85 total suite)

affects: [06-linkedin-post-generator]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Minority language negative constraint injected into system prompts via helper with prompt-type-specific phrasing
    - Strip-before-measure pattern for LLM response length validation

key-files:
  created: []
  modified:
    - scripts/generate_posts.py
    - tests/test_generate_posts.py

key-decisions:
  - "GAP-1: _negative_language_constraint() takes prompt_type param so technical/business phrasings stay disjoint"
  - "GAP-2: strip() applied to both initial and retry responses to prevent whitespace from masking short posts"
  - "Stderr log placed immediately before retry call so operators can correlate log with subsequent API call"

patterns-established:
  - "Minority language handling: define _MINORITY_LANGUAGES set + _NEGATIVE_CONSTRAINTS map, inject via helper"
  - "LLM response normalization: always strip() before length validation, strip() retry too"

requirements-completed: [POSTS-03, POSTS-04]

# Metrics
duration: 8min
completed: 2026-03-25
---

# Phase 06 Plan 02: GAP-1 Language Drift and GAP-2 Retry Robustness Summary

**Negative language constraints for Catalan (and future minority languages) injected into both system prompts, plus whitespace-aware retry that strips LLM responses before measuring char count**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-25T18:39:47Z
- **Completed:** 2026-03-25T18:47:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- GAP-1 closed: Catalan prompts now explicitly forbid Spanish, Portuguese, French, and Italian via `_negative_language_constraint()` helper with prompt-type-specific phrasing (prevents sentence-set collision)
- GAP-2 closed: `_generate_post()` strips LLM responses before char count check — a 571-char post padded with whitespace to 900 chars now correctly triggers retry
- Retry logs to stderr so operators can confirm it fired in production runs
- 6 new tests in `TestGapClosures` class; all 85 suite tests pass

## Task Commits

1. **Task 1: Fix language drift (GAP-1) and retry robustness (GAP-2)** - `20ec9cc` (fix)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `scripts/generate_posts.py` - Added `_MINORITY_LANGUAGES`, `_NEGATIVE_CONSTRAINTS`, `_negative_language_constraint()`, strip in `_generate_post()`, stderr log
- `tests/test_generate_posts.py` - Added `TestGapClosures` with 6 tests

## Decisions Made

- `_negative_language_constraint()` accepts `prompt_type` ("technical" or "business") so technical uses "Do NOT write in X — write exclusively in Y" while business uses "Avoid X entirely — produce all content in Y". This keeps sentence sets fully disjoint.
- `strip()` applied to both the initial LLM response and the retry response for consistency.
- Stderr log placed just before the retry `_call_openrouter` call per plan spec.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - tests passed on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GAP-1 and GAP-2 are closed; generate_posts.py is ready for Phase 06-03 (GAP-3 closure or verification)
- All 85 tests pass; no regressions

---
*Phase: 06-linkedin-post-generator*
*Completed: 2026-03-25*
