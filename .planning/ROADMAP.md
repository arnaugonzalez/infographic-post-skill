# Roadmap: Infographic Skill

## Milestones

- ✅ **v1.0 Multi-Provider Model Support** — Phases 1-3 (shipped 2026-03-25)
- [ ] **v1.1 Codebase Intelligence and Content Pipeline** — Phases 4-8

## Phases

<details>
<summary>✅ v1.0 Multi-Provider Model Support (Phases 1-3) — SHIPPED 2026-03-25</summary>

- [x] Phase 1: Provider Resolution Infrastructure (1/1 plans) — completed 2026-03-23
- [x] Phase 2: OpenRouter Text Adapter (1/1 plans) — completed 2026-03-23
- [x] Phase 3: Deploy Readiness and OSS Hardening (1/1 plans) — completed 2026-03-24

Archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### v1.1 Codebase Intelligence and Content Pipeline

- [ ] **Phase 4: Codebase Reader Foundation** - Noise-filtered directory reader with safety-first credential and token-budget guardrails
- [ ] **Phase 5: Prompt Registry and Codebase-to-Infographic** - Model-aware prompt strategy registry and `--codebase` flag on `generate_pretty.py`
- [ ] **Phase 6: LinkedIn Post Generator** - Two-angle post generator with runtime language selection and prompt-level angle differentiation (gap closure in progress)
- [ ] **Phase 7: OSS Quality Audit** - Standalone audit script producing structured `QUALITY_AUDIT.md` report
- [ ] **Phase 8: Integration and SKILL.md** - End-to-end smoke test and SKILL.md documentation updated to reflect all new capabilities

## Phase Details

### Phase 4: Codebase Reader Foundation
**Goal**: Users can feed any local repository into the skill safely — secrets stay local, token budgets are enforced, and a structured `CodebaseReport` is available for downstream consumers
**Depends on**: Nothing (first phase of v1.1; builds on existing codebase patterns from `parse_context.py`)
**Requirements**: CODEBASE-01, CODEBASE-02, CODEBASE-03, CODEBASE-04
**Success Criteria** (what must be TRUE):
  1. User can run `python read_codebase.py <dir>` and receive a filtered summary that omits build artifacts, dependencies, test files, config/dotfiles, and binary files
  2. User running on a directory with API keys in `.env` or `credentials.json` files does not see those values appear in the output — those files are unconditionally skipped
  3. User running on a large repo sees an explicit message listing which files were excluded to stay within the token budget, never silent truncation
  4. A downstream script can import `read_codebase` and receive a `CodebaseReport` dict with a `layers` key structurally compatible with the existing `arch.json` format
**Plans:** 1/2 plans executed
Plans:
- [x] 04-01-PLAN.md — TDD: noise filter, binary detection, credential safety (CODEBASE-01, CODEBASE-03)
- [ ] 04-02-PLAN.md — TDD: token budget, CodebaseReport schema, AST extraction, CLI (CODEBASE-02, CODEBASE-04)

### Phase 5: Prompt Registry and Codebase-to-Infographic
**Goal**: `generate_pretty.py` selects prompt strategy from a versioned registry keyed by model family, and can accept a codebase as infographic input via `--codebase`
**Depends on**: Phase 4 (`read_codebase.py` must exist before `--codebase` flag can call it)
**Requirements**: PROMPTREG-01, PROMPTREG-02, PROMPTREG-03
**Success Criteria** (what must be TRUE):
  1. User can see `_PROMPT_STRATEGIES` dict in `generate_pretty.py` with model-family keys replacing the prior inline `if/elif` model-string checks
  2. Each registry entry has a `last_verified` date field; running `generate_pretty.py` with an unrecognized model family prints a warning and falls back gracefully rather than crashing
  3. User can run `generate_pretty.py --codebase <dir>` and receive an infographic generated from the codebase summary without modifying any existing CLI arguments
**Plans:** 0/2 plans executed
Plans:
- [ ] 05-01-PLAN.md — TDD: prompt registry (_PROMPT_STRATEGIES, _model_family, _get_strategy) (PROMPTREG-01, PROMPTREG-02, PROMPTREG-03)
- [ ] 05-02-PLAN.md — TDD: --codebase flag wiring and CodebaseReport-to-config mapping (PROMPTREG-01)

### Phase 6: LinkedIn Post Generator
**Goal**: Users can generate two structurally distinct, ready-to-paste LinkedIn posts (technical and business angles) from a codebase in a single command, in their chosen language
**Depends on**: Phase 4 (`read_codebase.py`), Phase 5 (provider helpers from `generate_pretty.py`)
**Requirements**: POSTS-01, POSTS-02, POSTS-03, POSTS-04
**Success Criteria** (what must be TRUE):
  1. User can run `python generate_posts.py <dir>` and receive two clearly labeled posts (`--- TECHNICAL POST ---` / `--- BUSINESS POST ---`) in one command invocation
  2. User is prompted to select an output language at runtime; specifying `es` produces Spanish-language posts even when the codebase source code and comments are in English
  3. Generated posts are formatted for LinkedIn: hook line present, no unfilled template placeholders, within the 800-1,600 character target range
  4. The technical post includes a concrete implementation detail and the business post leads with an outcome — the two posts are structurally distinct, not paraphrases of each other
**Plans:** 1/3 plans complete (2 gap closure plans pending)
Plans:
- [x] 06-01-PLAN.md — TDD: generate_posts.py with dual-angle LLM calls, language enforcement, and character retry (POSTS-01, POSTS-02, POSTS-03, POSTS-04)
- [ ] 06-02-PLAN.md — Gap closure: minority language negative constraint (GAP-1) + retry robustness with strip (GAP-2) (POSTS-03, POSTS-04)
- [ ] 06-03-PLAN.md — Gap closure: redirect token budget warning to stderr (GAP-3) (POSTS-01, POSTS-02)

### Phase 7: OSS Quality Audit
**Goal**: Users can run a single command to get a structured, file-level audit report of their Python project's test coverage, docstring coverage, file presence, and code quality issues
**Depends on**: Nothing (fully standalone; no dependency on Phases 4-6)
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04
**Success Criteria** (what must be TRUE):
  1. User can run `python oss_audit.py` and receive a test coverage percentage per module, sourced from `coverage run -m pytest`
  2. The audit output names specific functions missing docstrings and lists which of README, LICENSE, .env.example, CHANGELOG are absent — not just aggregate scores
  3. The audit output includes flake8 logical error counts and flags specific functions with high branch complexity via stdlib `ast`
  4. Running `oss_audit.py` writes a `QUALITY_AUDIT.md` file to the project root that can be committed as a snapshot of project health
**Plans:** 2 plans
Plans:
- [ ] 07-01-PLAN.md — TDD: core audit functions — coverage, docstrings, OSS files, flake8, complexity (AUDIT-01, AUDIT-02, AUDIT-03)
- [ ] 07-02-PLAN.md — Report renderer, CLI wiring, integration tests, QUALITY_AUDIT.md generation (AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04)

### Phase 8: Integration and SKILL.md
**Goal**: All v1.1 capabilities are documented in SKILL.md with working invocation examples, and an end-to-end smoke test confirms the full codebase-to-infographic and codebase-to-posts pipelines run without errors on a real repository
**Depends on**: Phases 4, 5, 6, 7
**Requirements**: (no standalone requirements — validates all v1.1 requirements end-to-end)
**Success Criteria** (what must be TRUE):
  1. User can open SKILL.md and find copy-pasteable invocation examples for `read_codebase.py`, `generate_posts.py`, `oss_audit.py`, and the `generate_pretty.py --codebase` flag
  2. Every example command in SKILL.md runs without `unrecognized arguments` errors
  3. An end-to-end run of `generate_pretty.py --codebase <this repo>` and `generate_posts.py <this repo>` both complete successfully, confirming the full pipeline from codebase scan to output
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Provider Resolution Infrastructure | v1.0 | 1/1 | Complete | 2026-03-23 |
| 2. OpenRouter Text Adapter | v1.0 | 1/1 | Complete | 2026-03-23 |
| 3. Deploy Readiness and OSS Hardening | v1.0 | 1/1 | Complete | 2026-03-24 |
| 4. Codebase Reader Foundation | v1.1 | 1/2 | In Progress|  |
| 5. Prompt Registry and Codebase-to-Infographic | v1.1 | 0/2 | Planned    |  |
| 6. LinkedIn Post Generator | v1.1 | 1/3 | Gap Closure | - |
| 7. OSS Quality Audit | v1.1 | 0/2 | Planned | - |
| 8. Integration and SKILL.md | v1.1 | 0/? | Not started | - |
