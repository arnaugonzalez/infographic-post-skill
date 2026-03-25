# Requirements: Infographic Skill

**Defined:** 2026-03-25
**Milestone:** v1.1 — Codebase Intelligence and Content Pipeline
**Core Value:** Turn any data or context into a publication-ready infographic with one command — no design tools required.

## v1.1 Requirements

### Codebase Reader (CODEBASE)

- [x] **CODEBASE-01**: User can run `read_codebase.py` on a directory and receive a filtered summary that skips build artifacts, dependencies, test files, config/dotfiles, and binary files
- [x] **CODEBASE-02**: User's codebase summary is automatically token-budget-capped before any LLM call; key files are prioritized if the total would exceed the budget
- [x] **CODEBASE-03**: File contents are redacted of secrets (API keys, tokens) before being sent to any external LLM API
- [x] **CODEBASE-04**: `read_codebase.py` emits a structured JSON `CodebaseReport` for downstream consumers (LinkedIn generator, infographic pipeline)

### LinkedIn Post Generator (POSTS)

- [ ] **POSTS-01**: User can generate two LinkedIn posts (technical angle for engineers + business angle for PMs/execs) from a codebase in one command
- [ ] **POSTS-02**: User is prompted to select the output language at runtime before posts are generated
- [ ] **POSTS-03**: Generated posts are formatted for LinkedIn (hook line, correct character length, ready-to-paste)
- [ ] **POSTS-04**: Output language is enforced in the system prompt (not just the user turn) to prevent English drift when code context is English

### Model-Aware Prompt Registry (PROMPTREG)

- [ ] **PROMPTREG-01**: A `_PROMPT_STRATEGIES` registry dict in `generate_pretty.py` maps model families (gemini, dalle, sd) to prompt strategy parameters, replacing inline `if/elif` model checks
- [ ] **PROMPTREG-02**: Registry entries store only structural constraints (context window, image dimensions, style vocabulary) — no quality heuristics that decay between model updates
- [ ] **PROMPTREG-03**: Each registry entry includes a `last_verified` date field to surface stale entries

### OSS Quality Audit (AUDIT)

- [ ] **AUDIT-01**: User can run `oss_audit.py` to get test coverage percentage per module via coverage.py
- [ ] **AUDIT-02**: Audit reports docstring coverage (via `ast.parse`) and presence of OSS baseline files (README, LICENSE, .env.example, CHANGELOG)
- [ ] **AUDIT-03**: Audit reports code quality issues via flake8 subprocess and complexity hotspots via ast branch counting
- [ ] **AUDIT-04**: Audit produces a structured `QUALITY_AUDIT.md` report file

## v2 Requirements

### Extended Codebase Intelligence

- **CODEBASE-EXT-01**: User can configure custom skip patterns beyond the default noise filter
- **CODEBASE-EXT-02**: Codebase reader supports incremental re-reads (only changed files since last run)

### Extended Content Pipeline

- **POSTS-EXT-01**: User can generate posts from arbitrary text/data input (not just codebase)
- **POSTS-EXT-02**: Post generator supports platforms beyond LinkedIn (Twitter/X thread, newsletter)

### Distribution

- **DIST-01**: Skill is packaged as a PyPI package (`pyproject.toml`, entry points, versioning) so users can `pip install infographic-skill` instead of cloning the repo
- **DIST-02**: CI workflow publishes to PyPI on tagged release

### Extended Provider Support

- **EXTPROV-01**: User can configure a custom image generation provider beyond Google (e.g. DALL-E via OpenAI, Stability AI)
- **EXTPROV-02**: User can configure an Anthropic Claude API key directly without going through OpenRouter
- **EXTPROV-03**: User can see cost estimates for OpenRouter runs with dollar amounts

## Out of Scope

| Feature | Reason |
|---------|--------|
| AST symbol graph / tree-sitter parsing | Over-engineered for a CLI skill; noise-filtered walker + LLM is sufficient |
| Vector embeddings / semantic search over codebase | Adds infrastructure complexity (vector DB); out of scope for v1.1 |
| Prompt management library (LangChain, PromptFlow) | Registry is data, not code; a dict suffices |
| radon / mccabe for complexity | Python 3.12 incompatible; use stdlib ast instead |
| Video/animation output | Static infographics only |
| Web UI or dashboard | CLI/skill interface is the contract |
| OpenRouter for image generation | Incompatible response format with Gemini inline_data |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CODEBASE-01 | Phase 4 | Planned |
| CODEBASE-02 | Phase 4 | Planned |
| CODEBASE-03 | Phase 4 | Planned |
| CODEBASE-04 | Phase 4 | Planned |
| PROMPTREG-01 | Phase 5 | Planned |
| PROMPTREG-02 | Phase 5 | Planned |
| PROMPTREG-03 | Phase 5 | Planned |
| POSTS-01 | Phase 6 | Planned |
| POSTS-02 | Phase 6 | Planned |
| POSTS-03 | Phase 6 | Planned |
| POSTS-04 | Phase 6 | Planned |
| AUDIT-01 | Phase 7 | Planned |
| AUDIT-02 | Phase 7 | Planned |
| AUDIT-03 | Phase 7 | Planned |
| AUDIT-04 | Phase 7 | Planned |

**Coverage:**
- v1.1 requirements: 15 total
- Mapped to phases: 15/15
- Unmapped: 0

---
*Requirements defined: 2026-03-25*
