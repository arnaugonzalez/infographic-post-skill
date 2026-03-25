---
phase: 06-linkedin-post-generator
verified: 2026-03-25T18:55:00Z
status: passed
score: 9/9 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: "6/6 (initial truths, but 3 live-testing gaps logged)"
  gaps_closed:
    - "GAP-1: Language drift on minority languages (Catalan) — negative constraint added to both prompts"
    - "GAP-2: Retry not triggering on whitespace-padded short posts — strip() added before char count"
    - "GAP-3: Token budget warning printed to stdout — redirected to stderr in read_codebase.py"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run python3 scripts/generate_posts.py . --language es with valid INFG_OPENROUTER_API_KEY"
    expected: "Two posts on stdout in Spanish (800-1600 chars each), linkedin_posts.md written to cwd"
    why_human: "Requires live OpenRouter API key and real LLM call"
  - test: "Inspect generated posts for hook line, no placeholder tokens, appropriate LinkedIn tone"
    expected: "Both posts read as publication-ready with clearly distinct technical vs business angles"
    why_human: "LLM output quality and tone are subjective"
  - test: "Run with --language ca on English codebase, inspect for language drift"
    expected: "Both posts entirely in Catalan with no Spanish, Portuguese, or French sentences"
    why_human: "Requires live LLM run and human language assessment"
---

# Phase 6: LinkedIn Post Generator Verification Report

**Phase Goal:** Build a LinkedIn post generator that reads a codebase and produces two angles (technical + business) in the user's chosen language.
**Verified:** 2026-03-25T18:55:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plans 06-02 and 06-03 addressed GAP-1, GAP-2, GAP-3)

## Goal Achievement

### Observable Truths

Must-haves sourced from all three plan frontmatter files (06-01-PLAN.md, 06-02-PLAN.md, 06-03-PLAN.md).

| #  | Truth                                                                                                                              | Status     | Evidence                                                                                                  |
|----|------------------------------------------------------------------------------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------------------------|
| 1  | User can run `python scripts/generate_posts.py <dir>` and receive two posts labeled `--- TECHNICAL POST ---` and `--- BUSINESS POST ---` on stdout | ✓ VERIFIED | `_write_output` prints both separators; `test_stdout_contains_separators_and_char_counts` passes; CLI `--help` confirms positional `directory` arg |
| 2  | User can pass `--language es` and receive posts with Spanish language instruction in the system prompt                              | ✓ VERIFIED | Both system prompt builders inject `LANG_NAMES[language]`; `test_language_in_system_prompt_with_closing_repetition` confirms Spanish appears >= 2 times |
| 3  | Invalid `--language zh` causes argparse error exit before any LLM call                                                             | ✓ VERIFIED | `choices=SUPPORTED_LANGUAGES` on argparse (line 269); subprocess returns code 2 with argparse error message; `test_invalid_language_exits_with_error` passes |
| 4  | Posts outside 800-1600 chars trigger exactly one retry with length-correction instruction                                           | ✓ VERIFIED | `_generate_post` boundary check at line 186; `TestCharacterRetry` all 4 tests pass; retry prompt injects char count and "1,600 characters" |
| 5  | Technical and business system prompts are structurally distinct (no shared sentences)                                               | ✓ VERIFIED | `test_prompts_are_structurally_distinct` passes — sentence set intersection is empty for both `en` and `ca` variants |
| 6  | Both posts are written to `linkedin_posts.md` in cwd, overwriting any prior content                                                | ✓ VERIFIED | `_write_output` uses `write_text(..., encoding="utf-8")` (mode "w" by default); `test_file_overwritten_not_appended` passes |
| 7  | Catalan prompt includes explicit negative constraint forbidding Spanish, Portuguese, French, Italian                                | ✓ VERIFIED | `_negative_language_constraint("ca", "technical")` returns "Do NOT write in Spanish, Portuguese, French, Italian — write exclusively in Catalan"; `test_minority_language_negative_constraint` passes |
| 8  | Retry fires correctly for whitespace-padded LLM responses (strip before measuring)                                                  | ✓ VERIFIED | `post = post.strip()` at lines 184 and 195 in `_generate_post`; `test_retry_fires_with_whitespace_padded_response` passes (571-char content padded to 900 triggers retry) |
| 9  | Token budget warning goes to stderr, not stdout                                                                                     | ✓ VERIFIED | `read_codebase.py` lines 386 and 389 use `file=sys.stderr`; `test_budget_warning_goes_to_stderr_not_stdout` passes; live Python check confirmed budget in stderr only |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact                        | Expected                                                | Status     | Details                                                                                                                                                           |
|---------------------------------|---------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `scripts/generate_posts.py`     | LinkedIn post generator CLI, min 120 lines, contains `_call_openrouter` | ✓ VERIFIED | 279 lines; contains `_call_openrouter`, `_build_technical_system_prompt`, `_build_business_system_prompt`, `_negative_language_constraint`, `_generate_post`, `_write_output`, `main` |
| `tests/test_generate_posts.py`  | Unit tests, min 80 lines, contains `TestOutputFormat`  | ✓ VERIFIED | 292 lines; contains `TestOutputFormat`, `TestLanguageValidation`, `TestCharacterRetry`, `TestSystemPrompts`, `TestGapClosures` (22 tests, all pass) |
| `scripts/read_codebase.py`      | Budget warning redirected to stderr, contains `file=sys.stderr` | ✓ VERIFIED | Lines 386 and 389 both use `file=sys.stderr` in the `budget_excluded` block |
| `tests/test_read_codebase.py`   | Updated test assertions for stderr budget warnings      | ✓ VERIFIED | `test_budget_warning_goes_to_stderr_not_stdout` present at line 275; `captured.err` assertions at lines 271, 283-284; 35 tests all pass |

### Key Link Verification

| From                             | To                                               | Via                                          | Status     | Details                                                                                      |
|----------------------------------|--------------------------------------------------|----------------------------------------------|------------|----------------------------------------------------------------------------------------------|
| `scripts/generate_posts.py`      | `scripts/read_codebase.py`                       | `from read_codebase import read_codebase`    | ✓ WIRED    | Line 70; `read_codebase(args.directory)` called in `main()` line 243                        |
| `scripts/generate_posts.py`      | `https://openrouter.ai/api/v1/chat/completions`  | `_requests_lib.post` with system+user msgs   | ✓ WIRED    | `_requests_lib.post(...)` at lines 95-100; `{"role": "system", "content": system_prompt}` at line 91 |
| `tests/test_generate_posts.py`   | `scripts/generate_posts.py`                      | `from scripts.generate_posts import`         | ✓ WIRED    | Import pattern used across all 5 test classes; `patch("scripts.generate_posts._call_openrouter")` for LLM mocking |
| `_build_technical_system_prompt` | `_negative_language_constraint`                  | Direct call at line 142                      | ✓ WIRED    | `negative_constraint = _negative_language_constraint(language, "technical")` embedded at line 153 |
| `_build_business_system_prompt`  | `_negative_language_constraint`                  | Direct call at line 161                      | ✓ WIRED    | `negative_constraint = _negative_language_constraint(language, "business")` embedded at line 171 |
| `scripts/read_codebase.py`       | `sys.stderr`                                     | `print(..., file=sys.stderr)` in budget block | ✓ WIRED   | Lines 386 and 389 confirmed; `test_budget_warning_goes_to_stderr_not_stdout` verifies stdout is clean |

### Data-Flow Trace (Level 4)

Not applicable — `generate_posts.py` is a CLI script writing to a file and stdout, not a UI component rendering from a store. The data flow is: codebase directory argument → `read_codebase()` → `summary_text` → LLM system+user prompts → LLM response text → `linkedin_posts.md` file + stdout. LLM calls are fully mocked in all 22 unit tests; live end-to-end requires a real API key (see Human Verification).

### Behavioral Spot-Checks

| Behavior                                                        | Command                                                              | Result                                                                                          | Status   |
|-----------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|----------|
| CLI shows `directory` positional + `--language {en,es,fr,de,pt,it,ca}` | `python3 scripts/generate_posts.py --help`                  | Shows both; default `en`; Catalan (`ca`) included                                              | ✓ PASS   |
| Invalid `--language zh` exits with argparse code 2              | `python3 scripts/generate_posts.py --language zh /tmp`               | returncode=2; stderr shows "invalid choice: 'zh' (choose from 'en', 'es', 'fr', 'de', 'pt', 'it', 'ca')" | ✓ PASS   |
| Valid `--language es` + no API key exits with code 1 (not 2)    | subprocess with empty `INFG_OPENROUTER_API_KEY`                      | returncode=1; stdout "Set INFG_OPENROUTER_API_KEY in .env or environment"                       | ✓ PASS   |
| All 22 generate_posts unit tests pass                           | `python3 -m pytest tests/test_generate_posts.py -q`                  | `22 passed in 0.86s`                                                                            | ✓ PASS   |
| Full test suite passes with no regressions                      | `python3 -m pytest -q`                                               | `86 passed, 1 warning in 12.99s`                                                                | ✓ PASS   |
| Catalan technical prompt contains negative constraint           | Python: `"Do NOT write in" in _build_technical_system_prompt("ca")`  | `True`; Spanish, Portuguese, Catalan all present                                                | ✓ PASS   |
| Budget warning goes to stderr not stdout                        | Python: redirect stderr + call `read_codebase('.', 1)`               | `"Token budget" in err_output: True`; stdout clean                                              | ✓ PASS   |
| `strip()` present in `_generate_post` (both responses)         | `grep -n 'post = post.strip()' scripts/generate_posts.py`            | Lines 184 and 195                                                                               | ✓ PASS   |

### Requirements Coverage

Requirement IDs sourced from: `06-01-PLAN.md` (`[POSTS-01, POSTS-02, POSTS-03, POSTS-04]`), `06-02-PLAN.md` (`[POSTS-03, POSTS-04]`), `06-03-PLAN.md` (`[POSTS-01, POSTS-02]`).

| Requirement | Source Plans  | Description                                                                                                  | Status      | Evidence                                                                                                                             |
|-------------|---------------|--------------------------------------------------------------------------------------------------------------|-------------|--------------------------------------------------------------------------------------------------------------------------------------|
| POSTS-01    | 06-01, 06-03  | User can generate two LinkedIn posts (technical + business) from a codebase in one command                   | ✓ SATISFIED | `main()` makes two `_generate_post` calls; `_write_output` writes both with separators; `test_both_posts_written_to_file` passes. GAP-3 closed — `read_codebase()` budget warnings no longer contaminate stdout. |
| POSTS-02    | 06-01, 06-03  | User can select the output language; validated at runtime before any LLM call                                | ✓ SATISFIED | `--language` argparse flag with `choices=SUPPORTED_LANGUAGES, default="en"`; `zh` exits code 2; `TestLanguageValidation` 3 tests pass; Catalan (`ca`) added to supported languages. |
| POSTS-03    | 06-01, 06-02  | Generated posts are formatted for LinkedIn (hook line, correct character length, ready-to-paste)             | ✓ SATISFIED | Character target "800 to 1,600 characters" in both system prompts; `_generate_post` retries once if outside range; `post.strip()` before measurement (GAP-2 closed); `TestCharacterRetry` 4 tests + `test_retry_fires_with_whitespace_padded_response` all pass. |
| POSTS-04    | 06-01, 06-02  | Output language enforced in system prompt to prevent English drift when code context is English              | ✓ SATISFIED | Language directive in opening of both prompts; CRITICAL REMINDER/FINAL NOTE closing line repeats language name; `test_language_in_system_prompt_with_closing_repetition` confirms >= 2 occurrences. Catalan drift prevented by negative constraint (GAP-1 closed). |

**Orphaned requirements check:** REQUIREMENTS.md maps POSTS-01 through POSTS-04 to Phase 6 exclusively. POSTS-EXT-01 and POSTS-EXT-02 are explicitly future extensions. The traceability table (lines 82-85) lists all four as Phase 6. No orphaned requirements — all four IDs are covered by at least one plan's `requirements` frontmatter field.

### Anti-Patterns Found

| File                        | Line | Pattern                                                                              | Severity | Impact                                                                              |
|-----------------------------|------|--------------------------------------------------------------------------------------|----------|-------------------------------------------------------------------------------------|
| `scripts/generate_posts.py` | 277  | `_build_parser().parse_args()` result is discarded; `main()` (line 232) calls it again — argv is parsed twice | Warning  | No functional impact (argparse is deterministic for same argv; `main()` uses the result). Dead code from copy-paste artifact. Does not block the phase goal. |

No blocker anti-patterns found.

### Human Verification Required

#### 1. End-to-End Live API Run

**Test:** Run `python3 scripts/generate_posts.py . --language es` from the repo root with a valid `.env` containing `INFG_OPENROUTER_API_KEY` and `INFG_LLM_MODEL` (e.g., `google/gemini-2.0-flash-001`).
**Expected:** Two posts appear on stdout labeled `--- TECHNICAL POST ---` and `--- BUSINESS POST ---`, each in Spanish, each between 800-1600 characters, and `linkedin_posts.md` is written to the working directory.
**Why human:** Requires a live OpenRouter API key and makes real LLM calls. Cannot be tested programmatically without credentials.

#### 2. Post Quality Assessment

**Test:** Inspect the generated posts for readability — hook line in first sentence, no unfilled `[PLACEHOLDER]`-style template tokens, writing style appropriate for LinkedIn.
**Expected:** Both posts read as publication-ready LinkedIn content with clearly distinct angles (engineering detail vs. business outcome).
**Why human:** LLM output quality and tone are subjective; no programmatic check can assess whether the hook is compelling or the content is genuinely publication-ready.

#### 3. Catalan Language Drift Resistance (Live Run)

**Test:** Run with `--language ca` on a codebase with English identifiers and comments. Inspect both generated posts.
**Expected:** Both posts are entirely in Catalan with no Spanish, Portuguese, or French sentences. The negative constraint ("Do NOT write in Spanish, Portuguese, French, Italian") should prevent drift.
**Why human:** Requires a live LLM run and human language assessment; automated tests mock the LLM.

### Gaps Summary

All three gaps from the previous verification are closed. No new gaps introduced.

- **GAP-1 closed (language drift on Catalan):** `_negative_language_constraint()` helper injected into both prompt builders with prompt-type-specific phrasing to maintain sentence-set disjointness. `_MINORITY_LANGUAGES = {"ca"}` and `_NEGATIVE_CONSTRAINTS` map define the framework for adding future minority languages. 6 tests in `TestGapClosures` cover this. Commits: `f07180a`, `2943dcc`.
- **GAP-2 closed (retry not firing on whitespace-padded responses):** `post = post.strip()` applied to both initial and retry LLM responses before char count measurement. Retry logs to stderr. Commit: `f07180a`.
- **GAP-3 closed (budget warning contaminating stdout):** `read_codebase.py` budget_excluded block uses `print(..., file=sys.stderr)` for both lines. `test_budget_warning_goes_to_stderr_not_stdout` verifies stdout is clean. Commits: `b6256d9`, `051cbc2`.

Test suite grew from 79 to 86 tests (all passing). No regressions.

---

_Verified: 2026-03-25T18:55:00Z_
_Verifier: Claude (gsd-verifier)_
