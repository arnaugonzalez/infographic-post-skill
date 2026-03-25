---
phase: 3
slug: deploy-readiness-and-oss-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none — existing infrastructure |
| **Quick run command** | `python3 -m pytest tests/test_deploy.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -x -q` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_deploy.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | — | setup | `python3 -m pytest tests/test_deploy.py --collect-only` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | DEPLOY-01 | unit | `python3 -m pytest tests/test_deploy.py::TestKeyRedaction -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | DEPLOY-02 | unit | `python3 -m pytest tests/test_deploy.py::TestEnvVarAudit -x` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | DEPLOY-03 | unit | `python3 -m pytest tests/test_deploy.py::TestDocsAccuracy -x` | ❌ W0 | ⬜ pending |
| 3-01-05 | 01 | 1 | DEPLOY-04 | unit | `python3 -m pytest tests/test_deploy.py::TestOfflinePath -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_deploy.py` — stubs for DEPLOY-01 through DEPLOY-04
- [ ] `tests/__init__.py` — already present from Phase 2

*Existing infrastructure covers the pytest runner — only the new test file is needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OpenRouter key redacted in real traceback | DEPLOY-01 | Requires live error path with real key value | Set `INFG_OPENROUTER_API_KEY=sk-or-v1-testkey123` and trigger a 401 error; confirm `sk-or-v1-[REDACTED]` appears in output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
