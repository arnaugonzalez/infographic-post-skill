---
phase: 2
slug: openrouter-text-adapter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/test_openrouter.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_openrouter.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | — | setup | `python -m pytest tests/test_openrouter.py --collect-only` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | OROUTER-01 | unit | `python -m pytest tests/test_openrouter.py::test_call_openrouter_text_mode_success -x` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | OROUTER-02 | unit | `python -m pytest tests/test_openrouter.py::test_openrouter_401_error -x` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | OROUTER-02 | unit | `python -m pytest tests/test_openrouter.py::test_openrouter_402_error -x` | ❌ W0 | ⬜ pending |
| 2-01-05 | 01 | 1 | OROUTER-03 | unit | `python -m pytest tests/test_openrouter.py::test_openrouter_model_validation_no_slash -x` | ❌ W0 | ⬜ pending |
| 2-01-06 | 01 | 1 | OROUTER-04 | unit | `python -m pytest tests/test_openrouter.py::test_openrouter_token_counts -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_openrouter.py` — stubs for OROUTER-01 through OROUTER-04
- [ ] `tests/__init__.py` — package marker if not present
- [ ] `pytest` — install if not present (`pip install pytest`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full infographic generated via OpenRouter with valid key | OROUTER-01 | Requires live API key and credits | Set `INFG_LLM_PROVIDER=openrouter INFG_OPENROUTER_API_KEY=sk-or-v1-...` and run `python scripts/generate_pretty.py --text "Test data" --output test.png`; verify PNG exists and is non-zero |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
