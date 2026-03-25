# Phase 6: LinkedIn Post Generator - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `scripts/generate_posts.py` — a new script that accepts a codebase directory, reads it via `read_codebase.py`, generates two structurally distinct LinkedIn posts (technical angle for engineers + business angle for PMs/execs) using OpenRouter, and writes the result to `linkedin_posts.md` in the current working directory.

New capabilities (multi-platform output, post scheduling, interactive editing, vector embeddings) are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Language Selection (POSTS-02)

- **D-01:** Language is specified via `--language` CLI flag (e.g., `python generate_posts.py ./myrepo --language es`). No interactive prompt.
- **D-02:** Language is validated against a fixed enum: `['en', 'es', 'fr', 'de', 'pt', 'it']`. Unknown values produce a clear error message and exit before making any LLM calls.
- **D-03:** Language instruction is placed in the system prompt (not just the user turn) to prevent English drift when code context is English. Planner decides the exact system-prompt wording (closing-line repetition pattern from STATE.md decisions is the validated approach).

### Post Output (POSTS-01, POSTS-03)

- **D-04:** Output is written to `linkedin_posts.md` in the current working directory. Both posts are in a single file. Posts are also printed to stdout with `--- TECHNICAL POST ---` / `--- BUSINESS POST ---` separators.
- **D-05:** File format is `.md` — preserves emoji and markdown structure for LinkedIn copy-paste. File is overwritten on each run (no appending).
- **D-06:** After saving, print the file path: `✓  Saved to linkedin_posts.md`

### Post Structure (POSTS-04)

- **D-07:** Prompt-guided, not fill-in-the-blank templates. Each system prompt specifies structural requirements:
  - **Technical post** must open with a concrete implementation detail (specific tech, approach, or constraint solved).
  - **Business post** must lead with an outcome or result (what changed for the user/team/product).
  - Both posts must include a hook line (first line that stops the scroll), no unfilled template placeholders, and a closing call-to-action.
- **D-08:** Two separate LLM calls — one per post — using structurally distinct system prompts. The prompts share the same codebase summary context but have no other structural overlap.
- **D-09:** Character length target: 800–1,600 characters per post. If a post comes back outside this range after the first call, make **one retry** with an explicit length-correction instruction in the follow-up prompt ("Your previous response was {N} characters. Rewrite it to be between 800 and 1,600 characters, keeping the structure and language."). Accept the result of the retry regardless of length.

### LLM Configuration

- **D-10:** Reuse `INFG_OPENROUTER_API_KEY` and `INFG_LLM_MODEL` — same env vars as `generate_pretty.py`. No new vars. No `.env.example` additions needed.
- **D-11:** Use the same `_load_dotenv()` / `requests.post()` pattern from `generate_pretty.py`. No openai SDK dependency.

### Claude's Discretion

- Exact system prompt wording (beyond the structural anchors in D-07)
- Whether to extract a `--model` CLI override flag (or env-only via `INFG_LLM_MODEL`)
- Default language when `--language` flag is omitted (suggest `en`)
- Stdout character count note per post (e.g., `(1,243 chars)` after each separator)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Scripts (patterns to follow)
- `scripts/generate_pretty.py` — OpenRouter call pattern (`_call_openrouter_text_mode`, `_load_dotenv`, env var reading, argparse setup, `.env` loading)
- `scripts/read_codebase.py` — `read_codebase(root_dir, budget)` returns `CodebaseReport` dict; `CodebaseReport` keys: `summary_text`, `layers`, `connections`, `file_count`, `token_count`

### Requirements
- `.planning/REQUIREMENTS.md` §LinkedIn Post Generator (POSTS-01, POSTS-02, POSTS-03, POSTS-04) — acceptance criteria
- `.planning/ROADMAP.md` §Phase 6 — success criteria (4 items) and goal statement

### Prior Phase Decisions
- `.planning/STATE.md` §Accumulated Context/Decisions — pre-validated decisions: two separate LLM calls, language in system prompt, `requests.post()` for OpenRouter

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_load_dotenv()` (generate_pretty.py ~line 100): loads `.env` file — copy or import this pattern
- `_call_openrouter_text_mode(prompt, system_prompt, model, api_key)` (generate_pretty.py ~line 829): full OpenRouter call with error handling for 401/402/other — replicate this pattern directly
- `read_codebase(root_dir, budget)` (read_codebase.py): returns `CodebaseReport`; `summary_text` field is the primary input to both post prompts

### Established Patterns
- `sys.path.insert(0, str(_SKILL_DIR / "scripts"))` then `from read_codebase import read_codebase` — established pattern for cross-script imports
- `INFG_OPENROUTER_API_KEY` and `INFG_LLM_MODEL` env vars already documented in `.env.example`
- argparse with `--` prefixed long flags, no short flags for new scripts (follow phase 04/05 pattern)

### Integration Points
- `generate_posts.py` is a standalone script — no changes needed to existing scripts
- `read_codebase.py` is called as an import (not subprocess), same as Phase 5 pattern

</code_context>

<specifics>
## Specific Ideas

- Posts written to `linkedin_posts.md` should render cleanly when opened in a markdown viewer — emojis and line breaks preserved for direct copy-paste to LinkedIn.
- The `--- TECHNICAL POST ---` / `--- BUSINESS POST ---` separators match the success criteria wording in ROADMAP.md exactly.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-linkedin-post-generator*
*Context gathered: 2026-03-25*
