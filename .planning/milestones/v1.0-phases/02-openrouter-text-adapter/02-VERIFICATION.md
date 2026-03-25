---
phase: 02-openrouter-text-adapter
verified: 2026-03-23T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 02: OpenRouter Text Adapter Verification Report

**Phase Goal:** Users can generate infographics via the HTML-output path using any LLM on OpenRouter, with clear errors and token cost reporting
**Verified:** 2026-03-23
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                              | Status     | Evidence                                                                                      |
|----|----------------------------------------------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------------|
| 1  | User can generate infographics via HTML path with INFG_LLM_PROVIDER=openrouter and a valid key    | ✓ VERIFIED | `_call_openrouter_text_mode` at line 752 calls openrouter.ai endpoint; wired at dispatch line 961 |
| 2  | User with invalid key sees '401 -- check INFG_OPENROUTER_API_KEY' message, not a traceback        | ✓ VERIFIED | Line 774: `"❌  OpenRouter API key is invalid (401) — check INFG_OPENROUTER_API_KEY in your .env"` + `sys.exit(1)` |
| 3  | User with insufficient credits sees '402 -- add credits at openrouter.ai/credits' message         | ✓ VERIFIED | Line 777: `"❌  OpenRouter account has insufficient credits (402) — add credits at openrouter.ai/credits"` + `sys.exit(1)` |
| 4  | User with model missing slash sees validation error with 'openai/gpt-4o' example before any API call | ✓ VERIFIED | Lines 947-952: slash check fires in dispatch block before `_call_openrouter_text_mode` is invoked; spot-check confirmed |
| 5  | User sees input/output token counts after successful OpenRouter run                                | ✓ VERIFIED | Lines 974-975: `print(f"  Input tokens:  {or_usage['input_tokens']}")` and `print(f"  Output tokens: {or_usage['output_tokens']}")` |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact                         | Expected                                          | Status     | Details                                                                                   |
|----------------------------------|---------------------------------------------------|------------|-------------------------------------------------------------------------------------------|
| `scripts/generate_pretty.py`     | `def _call_openrouter_text_mode` function         | ✓ VERIFIED | Line 752 — full implementation, not a stub                                                |
| `scripts/generate_pretty.py`     | `_REQUESTS_OK` import guard                       | ✓ VERIFIED | Lines 143-149 — mirrors `_GENAI_OK` pattern exactly                                      |
| `scripts/generate_pretty.py`     | Model slash validation                            | ✓ VERIFIED | Lines 947-952 — `"OpenRouter model must include provider prefix"` with `'openai/gpt-4o'` example |
| `requirements.txt`               | `requests>=2.28` declared dependency              | ✓ VERIFIED | Line 4: `requests>=2.28`                                                                  |
| `tests/test_openrouter.py`       | Unit tests for OpenRouter adapter                 | ✓ VERIFIED | 143 lines, 4 test classes, 8 tests — all pass                                             |
| `tests/__init__.py`              | Package marker                                    | ✓ VERIFIED | File exists                                                                               |

### Key Link Verification

| From                                       | To                                            | Via                                      | Status     | Details                                                     |
|--------------------------------------------|-----------------------------------------------|------------------------------------------|------------|-------------------------------------------------------------|
| `generate_pretty.py` openrouter branch     | `_call_openrouter_text_mode()`                | `elif llm_provider == "openrouter"` at line 961 | ✓ WIRED    | Dispatch at line 961: `raw_html, or_usage = _call_openrouter_text_mode(prompt, effective_model, or_api_key)` |
| `_call_openrouter_text_mode()`             | `https://openrouter.ai/api/v1/chat/completions` | `_requests_lib.post()` at line 759       | ✓ WIRED    | Lines 759-770: `requests.post` with headers, json body, 120s timeout |
| OpenRouter dispatch branch                 | stdout token report                           | `print()` calls at lines 974-975         | ✓ WIRED    | Lines 971-978: provider-conditional report prints `Input tokens:` and `Output tokens:` |

### Data-Flow Trace (Level 4)

| Artifact                     | Data Variable | Source                                      | Produces Real Data     | Status      |
|------------------------------|---------------|---------------------------------------------|------------------------|-------------|
| `generate_pretty.py` (openrouter dispatch) | `raw_html, or_usage` | `_call_openrouter_text_mode()` → `_requests_lib.post()` → OpenRouter API | Yes — live HTTP POST, parses `choices[0].message.content` and `usage` from API JSON | ✓ FLOWING   |
| `_call_openrouter_text_mode` | `html_text`   | `data["choices"][0]["message"]["content"]`  | Yes — extracted from API response | ✓ FLOWING   |
| `_call_openrouter_text_mode` | `usage`       | `data.get("usage", {})` with graceful 0-defaults | Yes — extracted from API, defaults to 0 on missing key | ✓ FLOWING   |

### Behavioral Spot-Checks

| Behavior                                               | Command                                                                           | Result                                            | Status   |
|--------------------------------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------|----------|
| Module imports cleanly                                 | `python3 -c "import scripts.generate_pretty"`                                     | Exit 0, only matplotlib Axes3D warning (unrelated) | ✓ PASS   |
| Model without slash fires validation error             | `python3 scripts/generate_pretty.py --text "Test" --llm-provider openrouter --llm-model badmodel --output /tmp/t.html` | Exit 1, stdout: `"OpenRouter model must include provider prefix: 'openai/gpt-4o', got 'badmodel'"` | ✓ PASS   |
| Model with slash passes to key check                   | Same with `openai/gpt-4o`, no API key env vars                                    | Exit 1, stdout: `"OpenRouter requires an API key"` — no "provider prefix" | ✓ PASS   |
| All 8 pytest unit tests pass                           | `python3 -m pytest tests/test_openrouter.py -x -q`                               | `8 passed, 1 warning in 6.73s`                    | ✓ PASS   |

### Requirements Coverage

| Requirement  | Source Plan | Description                                                                                         | Status        | Evidence                                                                                  |
|--------------|-------------|-----------------------------------------------------------------------------------------------------|---------------|-------------------------------------------------------------------------------------------|
| OROUTER-01   | 02-01-PLAN  | User can generate infographics via HTML-output path using any LLM on OpenRouter                     | ✓ SATISFIED   | `_call_openrouter_text_mode` implemented and wired in dispatch; `TestOpenRouterSuccess` class passes |
| OROUTER-02   | 02-01-PLAN  | User sees clear actionable error for 401 (invalid key) and 402 (insufficient credits)               | ✓ SATISFIED   | Lines 773-778 in function; `TestOpenRouterHTTPErrors` tests mock both and confirm `sys.exit(1)` |
| OROUTER-03   | 02-01-PLAN  | User sees validation error with correct format example if model name is missing `provider/model` format before any API call | ✓ SATISFIED   | Lines 947-952 in dispatch; spot-check confirmed validation fires before HTTP call        |
| OROUTER-04   | 02-01-PLAN  | User sees token usage counts (input/output tokens) after successful run in cost report              | ✓ SATISFIED   | Lines 971-978 print `Input tokens:` and `Output tokens:`; `TestTokenCostReport` verifies source |

**Note on OROUTER-05:** This requirement (CLI flags `--llm-provider` and `--llm-model` override env vars) is marked Phase 1 in REQUIREMENTS.md and was NOT claimed by the Phase 02 PLAN. It is covered by Phase 01 work. No orphaned requirements for Phase 02.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No stubs, placeholders, or `NotImplementedError` references found for the OpenRouter path. The previous Phase 1 stub (`NotImplementedError("OpenRouter support coming in Phase 2")`) is fully removed. The string `"gray placeholders"` on line 338 is inside an LLM system prompt string, not a code placeholder.

The `_GENAI_OK` guard is correctly restructured at lines 864-895: OpenRouter sets `client = None`, `backend = None` and skips the `google-genai` check entirely. The image path at line 899 is gated with `llm_provider != "openrouter"`.

### Human Verification Required

#### 1. End-to-end generation with live OpenRouter API key

**Test:** Set `INFG_LLM_PROVIDER=openrouter`, `INFG_OPENROUTER_API_KEY=<valid key>`, `INFG_LLM_MODEL=openai/gpt-4o` and run `python3 scripts/generate_pretty.py --text "Q3 Revenue" --output /tmp/out.html`
**Expected:** HTML file generated, stdout shows `Input tokens: N` and `Output tokens: M` with non-zero values
**Why human:** Requires a live OpenRouter API key and real HTTP call; no mock can verify the full end-to-end path including HTML write and optional Playwright screenshot

#### 2. Playwright screenshot integration with OpenRouter path

**Test:** With Playwright installed and a valid OpenRouter key, run generation targeting a PNG output path
**Expected:** PNG file created at the output path; no errors in stdout
**Why human:** Requires Playwright installed and a live API key to exercise the HTML-to-PNG handoff from the OpenRouter path

### Gaps Summary

No gaps. All five observable truths are verified. All required artifacts exist and are substantive (not stubs). All three key links are wired. All four OROUTER requirements claimed by the phase plan are satisfied. Behavioral spot-checks pass 4/4. The only items routed to human verification require live external credentials and cannot be checked programmatically.

---

_Verified: 2026-03-23_
_Verifier: Claude (gsd-verifier)_
