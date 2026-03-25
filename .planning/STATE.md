---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Codebase Intelligence and Content Pipeline
status: Ready to plan
last_updated: "2026-03-25T13:06:33.612Z"
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 4
  completed_plans: 4
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-25)

**Core value:** Turn any data or context into a publication-ready infographic with one command.
**Current focus:** Phase 05 — prompt-registry-and-codebase-to-infographic

## Current Position

Phase: 6
Plan: Not started

## Performance Metrics

| Metric | v1.0 | v1.1 Target |
|--------|------|-------------|
| Phases | 3 | 5 |
| Requirements | 11 (all mapped) | 15 (all mapped) |
| Tests passing | 17 | 17+ (extend) |
| Phase 04-codebase-reader-foundation P01 | 3 | 2 tasks | 3 files |
| Phase 04 P02 | 274 | 2 tasks | 2 files |
| Phase 05-prompt-registry-and-codebase-to-infographic P01 | 12 | 2 tasks | 2 files |
| Phase 05-prompt-registry-and-codebase-to-infographic P02 | 4 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Full decisions log in PROJECT.md Key Decisions table.

Key v1.1 decisions pre-loaded from research:

- `pathspec>=0.12.1` is the only new `requirements.txt` addition; audit-only deps go in `requirements-audit.txt`
- Codebase reader must redact secrets at read time (not just in error handlers as in v1.0); credential files unconditionally skipped
- Token budget default: 40,000 tokens; configurable via `INFG_CODEBASE_TOKEN_BUDGET`; explicit exclusion message on truncation, never silent
- LinkedIn posts use two separate LLM calls with structurally distinct templates to prevent angle collapse
- Language instruction placed in system prompt with closing-line repetition; validated against explicit enum
- OSS audit uses `coverage run -m pytest` (not `pytest --cov`) with `.coveragerc source = ["scripts"]`
- `flake8 --select=F` via subprocess; `ast` branch-node counter for complexity (replaces stale `radon`/`mccabe`)
- Phase 8 (SKILL.md) always last — documents working reality, not intent
- [Phase 04-codebase-reader-foundation]: Use 'gitignore' pattern type (not deprecated 'gitwildmatch') for pathspec.PathSpec.from_lines
- [Phase 04-codebase-reader-foundation]: Credential files unconditionally skipped (not just redacted) — safety-first approach for read_codebase
- [Phase 04-codebase-reader-foundation]: _SECRET_PATTERNS defined independently in read_codebase.py — avoids coupling to generate_pretty.py
- [Phase 04]: Exclusion messages printed to stdout so capsys can capture in tests; CLI test uses small file avoiding message contamination of JSON output
- [Phase 04]: File prioritization: entry points first, then .py by size ascending to maximize file count within token budget
- [Phase 05-prompt-registry-and-codebase-to-infographic]: Registry keyed by family string (gemini/dalle/sd), not per-version — new variants classify into existing families without code changes
- [Phase 05-prompt-registry-and-codebase-to-infographic]: Staleness threshold set at 90 days for _warn_if_stale(); _gemini_version() retained for icon-mode print message; only _supports_icons() removed
- [Phase 05-prompt-registry-and-codebase-to-infographic]: D-05: viz_type always 'arch' for codebase infographics via _config_from_codebase_report returning (config, 'arch') tuple
- [Phase 05-prompt-registry-and-codebase-to-infographic]: D-06: report['summary_text'] maps to config['description'] (not report['summary'])
- [Phase 05-prompt-registry-and-codebase-to-infographic]: D-08: read_codebase imported lazily inside elif branch via existing sys.path pattern

### Pending Todos

- Plan Phase 4: Codebase Reader Foundation

### Blockers/Concerns

None.
