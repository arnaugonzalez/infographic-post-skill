---
phase: 03-deploy-readiness-and-oss-hardening
plan: "01"
subsystem: security-and-docs
tags:
  - key-redaction
  - security
  - oss-hardening
  - documentation
  - python-compatibility
dependency_graph:
  requires:
    - 02-01 (OpenRouter adapter — _call_openrouter_text_mode must exist)
  provides:
    - OpenRouter key redaction in all error output
    - openai import guard for offline safety
    - Python 3.9+ compatibility via future annotations
    - OpenRouter setup docs in SKILL.md and README.md
  affects:
    - scripts/generate_pretty.py (security, import guards)
    - SKILL.md (version claim, deps, OpenRouter docs)
    - README.md (version claim, OpenRouter docs)
    - tests/test_deploy.py (new test coverage)
tech_stack:
  added: []
  patterns:
    - TDD (RED/GREEN) for security and docs tests
    - Inline re.sub for multi-pattern key redaction
    - Import guard pattern (_OPENAI_OK mirroring _GENAI_OK and _REQUESTS_OK)
    - from __future__ import annotations for Python 3.9 PEP 604 union syntax
key_files:
  created:
    - tests/test_deploy.py
  modified:
    - scripts/generate_pretty.py
    - SKILL.md
    - README.md
decisions:
  - "Used inline re.sub() calls in _redact_key instead of module-level compiled pattern — simplifies multi-pattern extension"
  - "OpenRouter key redaction retains sk-or-v1- prefix so users can identify which key leaked"
  - "Removed google-genai and playwright from SKILL.md required pip deps — they are optional and caused unnecessary installs"
metrics:
  duration: "158s"
  completed_date: "2026-03-24"
  tasks_completed: 3
  files_modified: 4
---

# Phase 03 Plan 01: Deploy Readiness and OSS Hardening Summary

Extended API key redaction to cover OpenRouter keys, added openai import guard, fixed Python version claims to 3.9+, and documented OpenRouter setup in SKILL.md and README.md.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Create test scaffold | b96b808 | tests/test_deploy.py |
| 1 (GREEN) | Harden generate_pretty.py | df38cc1 | scripts/generate_pretty.py |
| 2 | Update SKILL.md and README.md | d891646 | SKILL.md, README.md |
| 3 | Full regression verification | (no commit — verify only) | — |

## What Was Built

### DEPLOY-01: OpenRouter Key Redaction

Extended `_redact_key()` to handle both Google AI Studio keys (`AIza...` → `[REDACTED]`) and OpenRouter keys (`sk-or-v1-xxx` → `sk-or-v1-[REDACTED]`). Removed the module-level `_KEY_PATTERN` compiled regex — replaced with two inline `re.sub()` calls. Also wrapped `resp.text[:200]` in `_redact_key()` on the generic OpenRouter error path (line 780).

### DEPLOY-02: Env Var Audit

Verified all 8 `os.environ.get()` calls in `generate_pretty.py` have matching entries in `.env.example`. No changes required — `.env.example` was already complete from Phase 02.

### DEPLOY-03: Docs Accuracy

- `SKILL.md`: `python: ">=3.8"` → `python: ">=3.9"`, removed `google-genai>=1.0` and `playwright` from required pip deps (they are optional), added "Optional setup: OpenRouter" section with `INFG_LLM_PROVIDER`, `INFG_LLM_MODEL`, `INFG_OPENROUTER_API_KEY` env var documentation.
- `README.md`: `Python 3.8+` → `Python 3.9+`, added "Optional setup: OpenRouter" section.

### DEPLOY-04: Offline Import Path

Added `_OPENAI_OK` import guard (try/except ImportError) mirroring existing `_GENAI_OK` and `_REQUESTS_OK` patterns. Module now loads cleanly when `openai` package is not installed.

### Python 3.9 Compatibility

Added `from __future__ import annotations` as the first statement after the module docstring. This makes `Path | None` and `str | None` union type annotations work on Python 3.9 (PEP 604 syntax is evaluated lazily with this import).

## Test Results

```
17 passed, 1 warning in 10.65s
```

- `tests/test_deploy.py` — 9 tests (TestKeyRedaction, TestEnvVarAudit, TestDocsAccuracy, TestOfflinePath) — all pass
- `tests/test_openrouter.py` — 8 tests (TestModelValidation, TestOpenRouterHTTPErrors, TestOpenRouterSuccess, TestTokenCostReport) — all pass
- Zero regressions from `generate_pretty.py` changes

## Deviations from Plan

None — plan executed exactly as written. The TDD RED/GREEN cycle was followed: tests created first (failing), then implementation made them pass.

## Known Stubs

None — all four DEPLOY requirements are fully implemented and verified.

## Self-Check: PASSED

- tests/test_deploy.py: FOUND
- scripts/generate_pretty.py modified: FOUND (df38cc1)
- SKILL.md modified: FOUND (d891646)
- README.md modified: FOUND (d891646)
- All success criteria verified via pytest
