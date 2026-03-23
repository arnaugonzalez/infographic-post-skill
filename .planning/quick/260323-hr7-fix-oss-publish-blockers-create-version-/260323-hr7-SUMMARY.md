---
phase: quick-260323-hr7
plan: "01"
subsystem: scripts
tags: [versioning, oss, license, cli]
dependency_graph:
  requires: []
  provides: [scripts/version_output.py, LICENSE]
  affects: [SKILL.md, README.md]
tech_stack:
  added: []
  patterns: [pathlib, argparse, Python 3.8+]
key_files:
  created:
    - scripts/version_output.py
    - LICENSE
  modified: []
decisions:
  - "Script creates root dir if missing (non-existing --root is valid for fresh projects)"
  - "MIT License year 2024 with generic copyright holder 'Infographic Skill Contributors'"
metrics:
  duration: "~2 minutes"
  completed: "2026-03-23"
  tasks_completed: 3
  tasks_total: 3
  files_created: 2
  files_modified: 0
---

# Phase quick-260323-hr7 Plan 01: Fix OSS Publish Blockers Summary

**One-liner:** Created versioned output directory manager (version_output.py) and MIT LICENSE file, resolving two open-source release blockers referenced in SKILL.md and README.md.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create scripts/version_output.py | e290e08 | scripts/version_output.py |
| 2 | Add MIT LICENSE file | 90c1149 | LICENSE |
| 3 | Release coherence verification | (no code changes) | — |

## What Was Built

### scripts/version_output.py

Full implementation of the versioning scheme from SKILL.md lines 531-605:

- **Default mode:** Creates `infographics/v1_last/` on first call; archives `v{N}_last -> v{N}` and creates `v{N+1}_last/` on subsequent calls. Prints only the absolute path to stdout — clean for shell pipeline use: `OUTPUT=$(python scripts/version_output.py --root .)`
- **`--list` mode:** Prints formatted version table with file counts, extensions, and `<- current` marker on the latest version
- **`--dir NAME`:** Overrides the output subdirectory name
- **Auto-detection:** Finds existing `infographics/`, `designs/`, `generated/`, or `output/` subdirectories under `--root`; defaults to `infographics/` if none exist
- **stderr/stdout separation:** Archive actions go to stderr; only the directory path goes to stdout

### LICENSE

Standard MIT License text (https://opensource.org/licenses/MIT), year 2024, copyright holder "Infographic Skill Contributors". Resolves the `[LICENSE](LICENSE)` reference in README.md line 163.

## Release Coherence Verification

All 6 scripts referenced in SKILL.md exist and are importable:
- scripts/generate.py
- scripts/generate_html.py
- scripts/generate_linkedin_arch.py
- scripts/generate_pretty.py
- scripts/parse_context.py
- scripts/version_output.py (newly created)

`python scripts/version_output.py --help` works. `python -c "import scripts.version_output"` succeeds. LICENSE file present.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Script accepts non-existing --root directory**
- **Found during:** Task 1 verification
- **Issue:** Plan's verify command passes a fresh temp directory that doesn't exist yet. Initial implementation rejected non-existing --root with an error. This is wrong for a fresh project where the user hasn't created the output dir yet.
- **Fix:** Changed `--root` validation to auto-create the directory (using `mkdir -p`) rather than failing with an error. This matches the "first call creates infographics/v1_last/" behavior described in SKILL.md.
- **Files modified:** scripts/version_output.py
- **Commit:** e290e08

## Self-Check: PASSED

- `scripts/version_output.py` exists and is importable
- `LICENSE` exists with MIT text and 2024 year
- Commits e290e08 and 90c1149 confirmed in git log
- All 6 SKILL.md script references resolve to existing files
