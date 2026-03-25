---
phase: 04-codebase-reader-foundation
plan: "02"
subsystem: codebase-reader
tags: [tdd, python, token-budget, ast-extraction, cli, layers]
dependency_graph:
  requires: ["04-01"]
  provides: ["complete-read_codebase-api", "codebase-cli", "token-budget-enforcement"]
  affects: ["phase-05-codebase-flag", "phase-06-linkedin-posts"]
tech_stack:
  added: []
  patterns:
    - "Token budget enforcement with explicit exclusion messages (never silent truncation)"
    - "AST-based Python signal extraction (class names, public function signatures)"
    - "File prioritization: entry points first, then .py by size, then others"
    - "arch.json-compatible layer categorization via path pattern matching"
    - "INFG_CODEBASE_TOKEN_BUDGET env var override for token budget"
    - "Positional directory CLI arg + legacy --root backward compat"
key_files:
  created: []
  modified:
    - scripts/read_codebase.py
    - tests/test_read_codebase.py
key_decisions:
  - "Exclusion messages printed to stdout (not stderr) so capsys in tests can capture them; CLI test uses small file that never triggers budget message, keeping JSON output clean"
  - "File prioritization sorts main.py/app.py/__init__.py first, then .py files by size ascending — smallest first maximizes number of files included under budget"
  - "_infer_layers only adds non-empty categories to the layers list, keeping output compact"
  - "Kept --root legacy flag for backward compat while adding positional directory arg"
metrics:
  duration_seconds: 274
  completed_date: "2026-03-25"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
  tests_added: 16
  tests_total: 51
---

# Phase 04 Plan 02: Token Budget, AST Extraction, CodebaseReport, CLI Summary

**One-liner:** Token budget enforcement with env var override, AST signal extraction for Python files, arch.json-compatible layer inference, and positional-arg CLI completing the full CodebaseReport contract.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED — Failing tests for token budget, schema, AST, CLI | f331b98 | tests/test_read_codebase.py (+189 lines) |
| 2 | GREEN — Implement token budget, AST extraction, CodebaseReport, CLI | bff04a1 | scripts/read_codebase.py (+215/-31 lines) |

## What Was Built

### Token Budget Enforcement (CODEBASE-02)

`read_codebase()` now enforces a token budget (default 40,000 tokens, ~160KB text). When the budget is exceeded:
- Files are sorted by priority before processing (entry points first, then smallest .py files, then others)
- Files that would exceed the budget are moved to `files_excluded`
- An explicit message is printed: `"Token budget (N tokens) reached. Excluded X files: ..."`

The budget is configurable via `INFG_CODEBASE_TOKEN_BUDGET` env var, which takes precedence over the `token_budget` argument.

### AST Signal Extraction (CODEBASE-01/04)

Python files get a `## Signals` preamble block in `summary_text` containing:
- Module docstring (first 200 chars)
- All class names (`class Foo:`)
- All public function names (`def bar(...):` — private `_` functions excluded)

Non-Python files get raw content only.

### CodebaseReport Schema (CODEBASE-04)

`read_codebase()` returns all 9 required keys:
- `root` — absolute path string
- `title` — directory basename
- `summary_text` — file blocks with AST signals for .py files
- `layers` — arch.json-compatible list of layer dicts
- `connections` — [] (populated by downstream consumers)
- `files_included` — list of relative paths actually read
- `files_excluded` — noise-filtered + budget-excluded paths
- `token_estimate` — tokens used (chars of included content // 4)
- `format` — "codebase"

### Layer Inference (CODEBASE-04)

`_infer_layers()` categorizes files into arch.json-compatible dicts with keys `label, category, items, bg, border, label_color`. Five categories:
- `testing` — files in `tests/` or with `test_` in name
- `backend` — files in `scripts/`, `src/`, `app/`
- `docs` — `.md`, `.txt`, `.rst` files
- `config` — `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini` files
- `other` — everything else

Empty categories are omitted from the layers list.

### CLI (CODEBASE-04)

`python scripts/read_codebase.py <directory>` — positional directory arg, prints JSON to stdout.
`python scripts/read_codebase.py <directory> --output report.json` — writes to file.
`--root` flag retained for backward compatibility.

## Tests

**16 new tests added** (total: 51 passing):

| Class | Count | Tests |
|-------|-------|-------|
| TestTokenBudget | 4 | budget_excludes_large_files, exclusion_message_printed, all_files_within_budget, token_estimate_in_report |
| TestTokenBudgetEnvVar | 2 | env_var_overrides_default, env_var_not_set_uses_default |
| TestCodebaseReportSchema | 4 | required_keys, format_is_codebase, root_is_absolute_path, title_is_dirname |
| TestLayersFormat | 2 | layers_is_list, layer_has_required_keys |
| TestASTExtraction | 2 | python_file_signals_extracted, non_python_file_raw_content |
| TestCLI | 2 | cli_json_output, cli_output_flag |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All features are fully implemented:
- Token budget: wired and tested
- AST extraction: wired for all .py files
- `_infer_layers`: wired to real files_included list
- CLI: fully functional with both positional and --output args

## Self-Check

- `scripts/read_codebase.py` exists: FOUND
- `tests/test_read_codebase.py` exists: FOUND
- Commit f331b98 (RED): FOUND
- Commit bff04a1 (GREEN): FOUND
- `python3 -m pytest tests/test_read_codebase.py -x -q` → 34 passed
- `python3 -m pytest tests/ -q` → 51 passed
- `python3 scripts/read_codebase.py . --output /tmp/test_report.json` → valid JSON with 9 keys, 5 layers

## Self-Check: PASSED
