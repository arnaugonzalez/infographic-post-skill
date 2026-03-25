---
phase: 02-openrouter-text-adapter
plan: "01"
subsystem: scripts/generate_pretty.py
tags: [openrouter, llm-adapter, requests, pytest, provider-dispatch]
dependency_graph:
  requires: [01-01]
  provides: [openrouter-text-adapter, openrouter-unit-tests]
  affects: [scripts/generate_pretty.py, requirements.txt, tests/]
tech_stack:
  added: [requests>=2.28]
  patterns: [conditional-import-guard, provider-dispatch, status-first-error-handling, mock-http-tests]
key_files:
  created:
    - tests/__init__.py
    - tests/test_openrouter.py
  modified:
    - scripts/generate_pretty.py
    - requirements.txt
decisions:
  - "Used _requests_lib alias to avoid shadowing local variables; mirrors _GENAI_OK pattern"
  - "Model slash validation placed in dispatch branch before API call — fires even without a key"
  - "or_usage variable scoped to openrouter branch; usage scoped to gemini branch"
  - "_GENAI_OK guard and client build wrapped in non-openrouter branch to avoid requiring google-genai for OpenRouter users"
  - "Image path gated with llm_provider != 'openrouter' — OpenRouter is text-only"
metrics:
  duration: "4m 12s"
  completed_date: "2026-03-23"
  tasks_completed: 2
  files_changed: 4
---

# Phase 02 Plan 01: OpenRouter Text Adapter Summary

**One-liner:** OpenRouter HTTP adapter via `requests.post()` with model slash validation, prescriptive 401/402 errors, token cost reporting, and 8 passing pytest unit tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement _call_openrouter_text_mode and wire into dispatch | abe3330 | scripts/generate_pretty.py, requirements.txt |
| 2 | Create pytest unit tests for OpenRouter adapter | 81479ea | tests/__init__.py, tests/test_openrouter.py |

## What Was Built

### Task 1: OpenRouter Adapter Implementation

Added full OpenRouter text adapter to `scripts/generate_pretty.py`:

- `_REQUESTS_OK` conditional import guard for `requests` library (mirrors `_GENAI_OK` pattern)
- `_call_openrouter_text_mode(prompt, model, api_key)` function that calls `https://openrouter.ai/api/v1/chat/completions` via `requests.post()` with 120s timeout
- Status-first error handling: 401 and 402 have prescriptive messages before JSON parsing
- Model slash validation in dispatch branch fires before any API call
- Provider-aware cost report: OpenRouter prints `Input tokens: N / Output tokens: M`; Gemini continues using existing `print_cost_report()`
- `_GENAI_OK` check and `_build_genai_client()` call wrapped in non-openrouter branch so OpenRouter users don't need `google-genai` installed
- Image generation path gated to non-openrouter providers
- `NotImplementedError` stub removed entirely

### Task 2: Pytest Unit Tests

Created `tests/test_openrouter.py` with 8 tests across 4 test classes, all mocking `requests.post()`:

- `TestModelValidation`: subprocess tests that model-without-slash exits with "provider prefix" error; model-with-slash passes to key validation
- `TestOpenRouterHTTPErrors`: mocked 401, 402, 500 responses all call `sys.exit(1)`
- `TestOpenRouterSuccess`: mocked 200 response returns `(html_text, usage_dict)`; missing usage defaults to 0
- `TestTokenCostReport`: asserts `Input tokens:` and `Output tokens:` print statements exist in `generate_pretty` source

All 8 tests pass without a live API key.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — the OpenRouter adapter is fully wired. The `total_cost` field in the usage dict may be `None` (OpenRouter does not return `total_cost` in chat completions response per documented behavior); this is expected and the cost line is conditionally omitted.

## Self-Check: PASSED

- `scripts/generate_pretty.py` exists and contains `_call_openrouter_text_mode`: confirmed
- `tests/test_openrouter.py` exists with all 4 test classes: confirmed
- `requirements.txt` contains `requests>=2.28`: confirmed
- Commit abe3330 exists: confirmed
- Commit 81479ea exists: confirmed
- Module imports cleanly: confirmed
- All 8 pytest tests pass: confirmed
