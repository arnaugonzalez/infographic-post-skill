---
phase: 01-provider-resolution-infrastructure
plan: 01
subsystem: api
tags: [python, gemini, openrouter, env-vars, cli, argparse, provider-routing]

# Dependency graph
requires: []
provides:
  - Provider resolver function (_resolve_llm_provider) with CLI > env var > gemini precedence
  - Module-level env var reads for INFG_LLM_PROVIDER, INFG_LLM_MODEL, INFG_LLM_API_KEY, INFG_OPENROUTER_API_KEY, INFG_IMAGE_MODEL
  - generate_pretty() with llm_provider and llm_model kwargs
  - Provider dispatch block (gemini path, openrouter stub, unknown provider exit)
  - --llm-provider and --llm-model CLI flags
  - INFG_IMAGE_MODEL override logic (only when --model not explicitly set)
  - .env.example Option C section for multi-provider env vars
affects:
  - 02-openrouter-http-adapter (uses _resolve_llm_provider and openrouter dispatch stub)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Provider resolver pattern with CLI flag > env var > default precedence
    - Provider dispatch if/elif block inside generate_pretty() for text path
    - NotImplementedError stub for unimplemented provider (openrouter) with Phase 2 note

key-files:
  created: []
  modified:
    - scripts/generate_pretty.py
    - .env.example

key-decisions:
  - "Renamed _call_text_mode to _call_gemini_text_mode to make provider explicit in function name"
  - "INFG_IMAGE_MODEL override only applies when --model is at its default value, per PROV-05"
  - "OpenRouter stub raises NotImplementedError (not sys.exit) so Phase 2 can distinguish from auth errors"
  - "Provider dispatch re-raises NotImplementedError before the generic credential error handler"

patterns-established:
  - "Provider resolver: (getattr(args, flag) or env_var or default).lower() precedence chain"
  - "Image model override: only substitute env var when CLI flag is at its default, not explicitly set"

requirements-completed: [PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, OROUTER-05]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 01 Plan 01: Provider Resolution Infrastructure Summary

**Provider resolver, env var reads, CLI flags, and function rename wired into generate_pretty.py with OpenRouter stub and .env.example Option C section**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-23T20:21:02Z
- **Completed:** 2026-03-23T20:23:46Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added 5 new module-level env var reads (INFG_LLM_PROVIDER, INFG_LLM_MODEL, INFG_LLM_API_KEY, INFG_OPENROUTER_API_KEY, INFG_IMAGE_MODEL) after `_load_dotenv()` call
- Renamed `_call_text_mode` to `_call_gemini_text_mode` with all call sites updated (definition + call site in HTML path)
- Added `_resolve_llm_provider(args)` function with CLI > env var > "gemini" default precedence
- Extended `generate_pretty()` with `llm_provider` and `llm_model` kwargs
- Wired provider dispatch block (gemini path active, openrouter raises NotImplementedError stub, unknown provider exits)
- Added `--llm-provider` and `--llm-model` CLI flags to argparse block
- Wired `_resolve_llm_provider` and `INFG_IMAGE_MODEL` override logic at `__main__` call site
- Added Option C section to .env.example with all 5 new env vars documented including OpenRouter key link

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire provider resolver infrastructure into generate_pretty.py** - `d9fd0ff` (feat)
2. **Task 2: Update .env.example with new provider env var entries** - `73f603a` (chore)

**Plan metadata:** (docs commit — see final commit below)

## Files Created/Modified

- `scripts/generate_pretty.py` - Added env var reads, resolver, renamed function, extended signature, provider dispatch, CLI flags, __main__ wiring
- `.env.example` - Added Option C section with 5 new multi-provider env vars

## Decisions Made

- Renamed `_call_text_mode` to `_call_gemini_text_mode` to make the provider explicit in the function name, preparing for Phase 2 additions
- `INFG_IMAGE_MODEL` env var only applies when `--model` CLI flag is at its default value (not explicitly set) per PROV-05
- OpenRouter stub uses `raise NotImplementedError` (not `sys.exit`) so the `except NotImplementedError: raise` guard ensures it propagates cleanly before the credential error handler catches it
- Provider dispatch placed inside the `try/except` block with explicit `except NotImplementedError: raise` to prevent the credential error handler from swallowing it

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added `except NotImplementedError: raise` guard in try/except block**

- **Found during:** Task 1 (provider dispatch wiring)
- **Issue:** Plan's dispatch block wraps `NotImplementedError` inside the existing `try/except Exception as e: _handle_credential_error(e)` block. The `_handle_credential_error` function checks if `exc` is an auth error — if not, it silently returns without re-raising, which would cause `raw_html` to be unbound on the next line when openrouter is set.
- **Fix:** Added `except NotImplementedError: raise` before `except Exception as e: _handle_credential_error(e); raise` so the stub error propagates cleanly. Also added explicit `raise` after `_handle_credential_error(e)` (the existing handler only exits on auth errors, returning None for non-auth — the original code would silently fail).
- **Files modified:** scripts/generate_pretty.py
- **Verification:** Module imports cleanly, `--help` runs without errors
- **Committed in:** d9fd0ff (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical error propagation)
**Impact on plan:** Auto-fix necessary for correctness — without it, setting `INFG_LLM_PROVIDER=openrouter` would crash with `UnboundLocalError: raw_html` instead of the clean NotImplementedError message.

## Issues Encountered

None — all changes applied cleanly.

## User Setup Required

None — no external service configuration required for this plan.
New env vars are all optional and additive; existing users see no behavior change.

## Next Phase Readiness

- Provider dispatch infrastructure complete: Phase 2 (OpenRouter HTTP adapter) can replace the `elif llm_provider == "openrouter":` stub with a real HTTP call
- `_resolve_llm_provider()` returns `(provider, model)` — Phase 2 only needs to implement the openrouter branch
- All env var reads in place: `_LLM_API_KEY` and `_OPENROUTER_API_KEY` are available for Phase 2 to use for authentication
- No blockers

---
*Phase: 01-provider-resolution-infrastructure*
*Completed: 2026-03-23*
