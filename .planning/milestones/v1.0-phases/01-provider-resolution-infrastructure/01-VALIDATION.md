---
phase: 1
slug: provider-resolution-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — manual CLI validation (project has no test infrastructure per TESTING.md) |
| **Config file** | none |
| **Quick run command** | `python scripts/generate_pretty.py --help` |
| **Full suite command** | See manual acceptance tests below |
| **Estimated runtime** | ~2 seconds (--help is instant, no API calls) |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/generate_pretty.py --help` (verifies parse-time correctness, zero API calls)
- **After every plan wave:** Run all manual acceptance tests below
- **Before `/gsd:verify-work`:** All manual acceptance tests must pass
- **Max feedback latency:** 5 seconds (--help) / manual for full suite

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Notes |
|---------|------|------|-------------|-----------|-------------------|-------|
| env-vars | 01 | 1 | PROV-01..05 | manual | `python -c "import scripts.generate_pretty as m; print(m._LLM_PROVIDER)"` | Verifies env var block reads |
| rename | 01 | 1 | — | automated | `python scripts/generate_pretty.py --help` | NameError if call site not renamed |
| resolver | 01 | 1 | PROV-01,02 | manual | `INFG_LLM_PROVIDER=openrouter python scripts/generate_pretty.py --text "test" --type dashboard --title "T" 2>&1` | Should print stub msg and exit non-zero |
| cli-flags | 01 | 1 | OROUTER-05 | automated | `python scripts/generate_pretty.py --help \| grep -E "llm-provider\|llm-model"` | Flags must appear in help |
| image-model | 01 | 1 | PROV-05 | automated | `INFG_IMAGE_MODEL=gemini-2.5-pro python scripts/generate_pretty.py --help` | No crash; model override wired |
| env-example | 01 | 1 | PROV-01..05 | automated | `grep -c "INFG_LLM_PROVIDER\|INFG_LLM_MODEL\|INFG_LLM_API_KEY\|INFG_OPENROUTER_API_KEY\|INFG_IMAGE_MODEL" .env.example` | Must output 5 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

No test framework setup needed — project intentionally has no automated test infrastructure. Manual CLI validation is the project's documented approach.

*Existing infrastructure covers all phase requirements via manual CLI tests.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `INFG_LLM_PROVIDER=openrouter` routes to NotImplementedError stub | PROV-01 | Requires env var set and script execution | Run: `INFG_LLM_PROVIDER=openrouter python scripts/generate_pretty.py --text "test" --type dashboard --title "T"` — expect stub print + non-zero exit |
| `INFG_LLM_MODEL` overrides text path model | PROV-02 | No test harness; traced via resolver output | Run: `INFG_LLM_MODEL=gemini-2.5-pro python scripts/generate_pretty.py --help` then inspect resolver behavior |
| `INFG_LLM_API_KEY` read into `_LLM_API_KEY` | PROV-03 | Module-level constant inspection | Run: `python -c "import sys; sys.path.insert(0,'scripts'); import generate_pretty as m; print(m._LLM_API_KEY)"` |
| `INFG_OPENROUTER_API_KEY` read into `_OPENROUTER_API_KEY` | PROV-04 | Same as PROV-03 | Same approach |
| `INFG_IMAGE_MODEL` overrides default but not explicit `--model` flag | PROV-05 | Requires verifying two branches | (a) `INFG_IMAGE_MODEL=gemini-2.5-pro python scripts/generate_pretty.py --text "x" --title "T"` → model should be gemini-2.5-pro; (b) same + `--model gemini-2.0-flash` → model should stay gemini-2.0-flash |
| `--llm-provider openrouter` triggers stub (CLI flag takes precedence over absent env var) | OROUTER-05 | Requires execution | `python scripts/generate_pretty.py --llm-provider openrouter --text "x" --title "T"` → same stub as PROV-01 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or manual test instructions
- [ ] `python scripts/generate_pretty.py --help` passes after every task
- [ ] All 6 manual acceptance tests pass before verify-work
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s (--help instant)
- [ ] `nyquist_compliant: true` set in frontmatter when all above checked

**Approval:** pending
