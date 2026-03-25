# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Multi-Provider Model Support

**Shipped:** 2026-03-25
**Phases:** 3 | **Plans:** 3 | **Tasks:** 7

### What Was Built

- Provider resolver with CLI > env var > gemini precedence — full backward compatibility
- OpenRouter HTTP adapter via `requests.post()` — no new required dependency
- API key redaction for both Google (`AIza...`) and OpenRouter (`sk-or-v1-...`) keys
- `openai` lazy import guard — matplotlib offline path survives without optional packages
- SKILL.md and README.md accuracy pass: Python 3.9+, optional deps correctly documented
- 17 pytest tests covering all deploy readiness and OpenRouter behaviors

### What Worked

- **Dependency ordering was clean**: Phase 1 (provider resolver stub) → Phase 2 (real adapter) → Phase 3 (hardening) had zero backtracking
- **TDD RED/GREEN for security tests**: Writing failing tests before implementation caught the `_redact_key` multi-pattern case cleanly
- **Flat `if/elif` dispatch**: Resisting the ABC/registry urge kept Phase 2 simple and readable
- **`_REQUESTS_OK` guard pattern**: Mirroring the existing `_GENAI_OK` convention made the new code blend naturally

### What Was Inefficient

- **ROADMAP.md Phase 3 status not updated**: The roadmap showed `0/1 plans executed` for Phase 3 even after completion — the milestone archive step caught this but it should be updated at execution time
- **One-liner extraction failure**: gsd-tools `summary-extract --fields one_liner` returned empty for Phase 3 SUMMARY.md — the Phase 3 summary lacked a top-level one-liner in the expected format

### Patterns Established

- `_XYZ_OK` conditional import guard pattern — use for every optional dependency
- Status-first error handling: check HTTP status code before parsing JSON in API adapters
- Model slash validation in the dispatch branch, before any API call — fires even without a key
- `from __future__ import annotations` as first statement for Python 3.9 PEP 604 union syntax

### Key Lessons

1. **Stub → replace is cleaner than build-in-place**: Phase 1 shipped a `NotImplementedError` stub for OpenRouter, letting Phase 2 focus entirely on the real implementation. This pattern worked well.
2. **Optional dependency guards at module level**: `_OPENAI_OK = False; try: import openai; _OPENAI_OK = True; except ImportError: pass` — consistent, zero-cost, readable.
3. **`except NotImplementedError: raise` guard matters**: Without explicit re-raise, a generic `except Exception` handler can swallow stub errors silently, causing downstream `UnboundLocalError`. Always guard.

### Cost Observations

- Model mix: sonnet (executor), opus (planner)
- Sessions: 3 (one per phase)
- Notable: Phase 1 completed in ~3 min, Phase 2 in ~4 min, Phase 3 in ~3 min — small, well-scoped plans executed fast

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 3 | 3 | First structured GSD milestone — established stub→replace pattern |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions |
|-----------|-------|-------------------|
| v1.0 | 17 | 0 (requests was already in requirements) |
