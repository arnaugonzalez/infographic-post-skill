# Phase 5: Prompt Registry and Codebase-to-Infographic - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `_PROMPT_STRATEGIES` registry dict to `generate_pretty.py` that replaces all inline model-version `if/elif` checks (e.g., `_supports_icons()`), and wire a `--codebase <dir>` flag that calls `read_codebase.py` and feeds the resulting `CodebaseReport` into the existing infographic generation pipeline.

New capabilities (new image providers, new output formats, CLI redesign) are out of scope.
</domain>

<decisions>
## Implementation Decisions

### Registry Shape (PROMPTREG-01, PROMPTREG-02, PROMPTREG-03)

- **D-01:** `_PROMPT_STRATEGIES` is a dict keyed by model family string. Each entry contains:
  - `supports_icons` (bool) — whether to inject the brand-icon guide into the prompt
  - `context_window` (int) — token context window for the model family
  - `style_vocabulary` (list of str) — e.g., `["glassmorphism", "gradient", "dark-background"]`
  - `prompt_fragments` (dict) — model-specific prompt text snippets (e.g., icon guide text, UPGRADE instructions). The registry is the **single source of truth** for all model-specific prompt content.
  - `last_verified` (str, ISO date) — when this entry was last verified against the live model

- **D-02:** Keys: `"gemini"` (full entry), `"dalle"` (empty/stub), `"sd"` (empty/stub). No per-version keys (e.g., not `"gemini-2.5"`). New Gemini variants are classified into the `"gemini"` family.

- **D-03:** The existing `_supports_icons()` function's logic moves into the registry lookup — it is no longer a separate version-check function. The registry lookup replaces the `major > 2 or (major == 2 and minor >= 5)` check.

- **D-04:** `last_verified` field is required in each entry. Staleness surfacing behavior is **Claude's Discretion** (not discussed — planner decides threshold and display).

### `--codebase` Flag (PROMPTREG-01, downstream of CODEBASE-04)

- **D-05:** `viz_type = "arch"` — codebase infographics always use the architecture diagram format.

- **D-06:** `CodebaseReport` → config mapping:
  - `report["layers"]` → `config["layers"]` (direct, arch.json-compatible — no transformation needed)
  - `report["summary"]` → `config["description"]`
  - `connections` from report → `config["connections"]` if present, otherwise empty list

- **D-07:** Title when `--title` is not specified: derive from the directory name, title-cased (e.g., `./infographic-skill` → `"Infographic Skill"`).

- **D-08:** Integration: `generate_pretty.py` imports `read_codebase` directly via `sys.path.insert(0, str(_SKILL_DIR / "scripts"))` — same pattern as the existing `generate_linkedin_arch` import (line ~245). No subprocess call.

### Unrecognized Model Fallback

- **D-09:** When the model family extracted from `--model` is not in `_PROMPT_STRATEGIES` (i.e., not `gemini`, `dalle`, or `sd`): print `⚠️  Unrecognized model family '{family}' — falling back to gemini strategy.` then proceed using the `gemini` entry. Never crash or exit.

### Claude's Discretion

- Staleness threshold for `last_verified` warnings — planner decides (e.g., 90 days, or only on unrecognized model)
- Exact logic for extracting model family from a full model string (e.g., `"gemini-3.1-flash-image-preview"` → `"gemini"`)
- Whether to expose `--codebase-budget` as a passthrough to `read_codebase`'s `INFG_CODEBASE_TOKEN_BUDGET` or leave it env-only

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Implementation
- `scripts/generate_pretty.py` — file being modified; contains `_supports_icons()`, `_build_image_prompt()`, `_build_html_prompt()`, `_IMAGE_ICON_GUIDE`, `_HTML_ICON_GUIDE`, CLI arg parsing
- `scripts/read_codebase.py` — Phase 4 output; `read_codebase(root_dir, budget)` returns `CodebaseReport` dict

### Requirements
- `.planning/REQUIREMENTS.md` §Model-Aware Prompt Registry (PROMPTREG-01, PROMPTREG-02, PROMPTREG-03) — acceptance criteria

### Phase 4 Artifacts
- `.planning/phases/04-codebase-reader-foundation/04-02-SUMMARY.md` — CodebaseReport schema details

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_supports_icons(model)` (line ~284): version-based icon mode check — logic moves into registry
- `_gemini_version(model)` (line ~275): version extractor — may still be needed for family detection
- `_IMAGE_ICON_GUIDE` / `_HTML_ICON_GUIDE` (lines ~290-388): large prompt fragments — move into registry's `prompt_fragments` dict
- `sys.path.insert(0, ...)` + import pattern (line ~243): established pattern for importing sibling scripts

### Established Patterns
- Flat `if/elif` for provider dispatch (gemini/openrouter) — registry doesn't change this, only the model-specific prompt content inside each path
- `_load_dotenv` + `os.environ.get` pattern for env var config — no change needed for `--codebase`
- `--config`, `--layers`, `--text` args all build a `config` dict → `generate_pretty(config, ...)` — `--codebase` follows the same pattern

### Integration Points
- `argparse` in `__main__` block (line ~1000+): add `--codebase` arg here alongside existing `--config`/`--layers`/`--text`
- `generate_pretty()` function: receives `config` dict — no signature change needed
- `_build_image_prompt()` / `_build_html_prompt()`: receive `use_icons` bool — replace with registry lookup result

</code_context>

<specifics>
## Specific Ideas

- The registry's `prompt_fragments` dict removes the need for `_IMAGE_ICON_GUIDE` and `_HTML_ICON_GUIDE` as module-level constants — they become values inside the gemini entry.
- `dalle` and `sd` stubs make the registry structure visible as an extension point even before those backends exist.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.
</deferred>

---

*Phase: 05-prompt-registry-and-codebase-to-infographic*
*Context gathered: 2026-03-25*
