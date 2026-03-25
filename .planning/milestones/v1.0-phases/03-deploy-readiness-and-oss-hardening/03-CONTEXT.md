# Phase 3: Deploy Readiness and OSS Hardening - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Harden the skill for public OSS publication: redact OpenRouter API keys in error output (matching existing Google key redaction), audit and document all env vars in `.env.example`, add OpenRouter setup section to SKILL.md and README.md, correct Python version requirement to 3.9+, and add a lazy import guard for the `openai` package so the matplotlib offline path works without it installed.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure/documentation phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing Google key redaction in `generate_pretty.py` — mirror this pattern for OpenRouter keys (`sk-or-v1-...` prefix)
- `.env.example` already has entries from Phase 1 — audit and extend
- SKILL.md and README.md exist in project root — add OpenRouter section

### Established Patterns
- Error messages: `print("❌  ..."); sys.exit(1)` for fatal errors
- Key redaction: existing pattern for `INFG_API_KEY` values — replicate for `INFG_OPENROUTER_API_KEY`
- Conditional imports: `try/except ImportError` with `_FLAG` pattern (used for `_GENAI_OK`, `_REQUESTS_OK`)

### Integration Points
- `generate_pretty.py` — add key redaction for sk-or-v1- prefixed keys
- `.env.example` — audit all `os.environ.get()` calls across all scripts
- `SKILL.md`, `README.md` — add OpenRouter setup section, fix Python version

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
