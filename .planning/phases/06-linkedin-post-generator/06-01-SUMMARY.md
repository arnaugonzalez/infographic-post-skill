---
phase: 06-linkedin-post-generator
plan: "01"
subsystem: content-generation
tags: [openrouter, requests, linkedin, tdd, argparse, language]

# Dependency graph
requires:
  - phase: 04-codebase-reader-foundation
    provides: read_codebase() function returning CodebaseReport with summary_text
provides:
  - scripts/generate_posts.py — LinkedIn post generator CLI using OpenRouter
  - tests/test_generate_posts.py — 16-test suite covering POSTS-01 through POSTS-04
affects: [07-oss-quality-audit, 08-skill-md-update]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED/GREEN cycle: stub raises NotImplementedError, tests fail, then full implementation"
    - "Structurally distinct system prompts: no shared sentence sets enforced by test"
    - "Language enforcement via dual injection: opening directive + closing CRITICAL REMINDER"
    - "_load_dotenv pattern: reads .env from _SKILL_DIR, uses os.environ.setdefault"
    - "Character retry: single retry with count injected into user prompt"

key-files:
  created:
    - scripts/generate_posts.py
    - tests/test_generate_posts.py
  modified: []

key-decisions:
  - "System prompt sentence sets must be fully disjoint — sharing even language/char-count lines fails the test; resolved by using different phrasing per prompt"
  - "Language enforcement uses two distinct phrases per prompt (opening + closing) to satisfy D-03 repetition requirement without creating shared sentences between prompts"

patterns-established:
  - "generate_posts.py: argparse with choices=SUPPORTED_LANGUAGES for language validation"
  - "Retry logic in _generate_post: single retry, char count injected into user_prompt not system_prompt"

requirements-completed: [POSTS-01, POSTS-02, POSTS-03, POSTS-04]

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 06 Plan 01: LinkedIn Post Generator Summary

**TDD-built LinkedIn post generator using OpenRouter with structurally distinct technical/business prompts, language enforcement with closing-line repetition, and single-retry length correction**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T16:35:36Z
- **Completed:** 2026-03-25T16:39:17Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 2

## Accomplishments

- 16 unit tests across 4 classes (TestOutputFormat, TestLanguageValidation, TestCharacterRetry, TestSystemPrompts) covering POSTS-01 through POSTS-04
- `_call_openrouter()` with 401/402/other HTTP error handling and 120s timeout
- Two structurally distinct system prompts with no shared sentences, both enforcing language via opening + closing repetition
- `_generate_post()` retries once when response is outside 800-1600 characters, injecting original char count into retry prompt
- `_write_output()` writes `linkedin_posts.md` (overwrite mode) and prints separators with char counts to stdout
- `main()` with env var validation, `read_codebase()` integration, and dual post generation
- Full test suite 79/79 passing (16 new + 63 existing)

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Write failing tests for generate_posts.py** - `fcaa06d` (test)
2. **Task 2: GREEN — Implement generate_posts.py to pass all tests** - `e862a16` (feat)

_Note: TDD tasks committed as separate RED/GREEN phases per plan specification_

## Files Created/Modified

- `/home/eager-eagle/code/infographic-skill/infographic-skill/scripts/generate_posts.py` — LinkedIn post generator CLI (174 lines): _call_openrouter, _build_technical_system_prompt, _build_business_system_prompt, _generate_post, _write_output, main
- `/home/eager-eagle/code/infographic-skill/infographic-skill/tests/test_generate_posts.py` — 16-test suite covering all 4 POSTS requirements

## Decisions Made

- Sentence-disjoint system prompts: The test `test_prompts_are_structurally_distinct` splits on `.` and checks for zero shared sentences. The initial implementation shared language enforcement and character target sentences between both prompts. Resolved by using entirely different phrasing in each prompt (e.g., "Language directive: respond exclusively in {lang}" vs "Output language: write the entire post in {lang}"; "Target length: 800 to 1,600 characters" vs "Character range: aim for 800 to 1,600 characters").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Shared sentences between technical and business system prompts**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Both prompts used identical language enforcement lines and character target sentences, causing `test_prompts_are_structurally_distinct` to fail (4 shared sentences detected)
- **Fix:** Rewrote both prompts with unique sentence phrasing for language directive, character target, and closing reminder — all semantically equivalent but lexically distinct
- **Files modified:** scripts/generate_posts.py
- **Verification:** `test_prompts_are_structurally_distinct` passes; `test_language_in_system_prompt_with_closing_repetition` still passes (Spanish appears 2+ times)
- **Committed in:** e862a16 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in prompt implementation)
**Impact on plan:** Required only sentence-level rewording with no structural changes. Both prompts remain semantically correct per D-03/D-07/D-08.

## Issues Encountered

None beyond the auto-fixed deviation above.

## User Setup Required

None — no external service configuration required by this plan. (OpenRouter API key and model must be set in `.env` as pre-existing `INFG_OPENROUTER_API_KEY` and `INFG_LLM_MODEL` — documented in existing `.env.example`.)

## Next Phase Readiness

- LinkedIn post generator is complete and tested; ready to wire into SKILL.md in Phase 08
- Phase 07 (OSS quality audit) has no dependency on this plan

## Self-Check: PASSED

- scripts/generate_posts.py: FOUND
- tests/test_generate_posts.py: FOUND
- SUMMARY.md: FOUND
- Commit fcaa06d (test/RED): VERIFIED
- Commit e862a16 (feat/GREEN): VERIFIED

---
*Phase: 06-linkedin-post-generator*
*Completed: 2026-03-25*
