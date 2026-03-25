# Phase 1: Provider Resolution Infrastructure - Research

**Researched:** 2026-03-23
**Domain:** Python argparse CLI flags, os.environ configuration, provider dispatch pattern
**Confidence:** HIGH

## Summary

Phase 1 is a pure code surgery task inside a single file (`scripts/generate_pretty.py`). All architectural decisions are already locked in CONTEXT.md. The work amounts to: adding five env var reads at module level, adding two argparse flags, renaming one function, inserting a `_resolve_llm_provider()` dispatcher that returns a `(provider, model)` tuple, wiring the HTML path to go through that dispatcher, and documenting five new env vars in `.env.example`.

No new dependencies are required. The project already has `argparse`, `os.environ`, and all requisite Python 3.10+ features in use. The provider resolver is a flat `if/elif` block — this is deliberately not an ABC or registry pattern (locked decision). The OpenRouter branch stubs to `NotImplementedError` with a print message; the Gemini branch calls the existing renamed `_call_gemini_text_mode()`.

**Primary recommendation:** Implement the five changes in dependency order — env var reads first, then argparse extension, then function rename, then resolver, then `.env.example` update — so each step is independently verifiable.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Image model override:** CLI `--model` flag takes precedence over `INFG_IMAGE_MODEL` env var (standard CLI > env > default). `INFG_IMAGE_MODEL` overrides only the hardcoded default (`gemini-3.1-flash-image-preview`); `_IMAGE_FALLBACK` stays as `gemini-2.5-flash-image` — it's a 404 safety net, not user-configurable.
- **`INFG_IMAGE_MODEL` is read silently** — no diagnostic print, consistent with existing `_VERTEX_*` behavior.
- **`INFG_LLM_MODEL` controls only the text/HTML generation path** — image path stays under `--model` flag and `INFG_IMAGE_MODEL`.
- **Provider resolver design:** Flat `if/elif` dispatch in `generate_pretty.py` — no ABC, no registry, no LiteLLM.
- **Resolver function signature:** `_resolve_llm_provider(args)` → returns `(provider: str, model: str | None)` tuple.
- **Provider "gemini" is the default** when `INFG_LLM_PROVIDER` is not set.
- **OpenRouter selected → `NotImplementedError("OpenRouter support coming in Phase 2")`** with a clear print message before raising.
- **`--llm-provider` and `--llm-model` flags added only to `generate_pretty.py`** (only script with LLM text path).
- **Precedence: CLI flags > env vars > defaults.**
- **Existing `--model` flag remains** as Gemini image model override — not deprecated.
- **`_call_text_mode()` renamed to `_call_gemini_text_mode()`** to disambiguate from future `_call_openrouter_text_mode()`.
- **`.env.example` entries for:** `INFG_LLM_PROVIDER`, `INFG_LLM_MODEL`, `INFG_LLM_API_KEY`, `INFG_OPENROUTER_API_KEY`, `INFG_IMAGE_MODEL`.
- **No new module/file** — everything stays in `generate_pretty.py`.

### Claude's Discretion

- Exact placement of env var reads (module level, alongside existing `_VERTEX_*` vars is the expected location).
- Error message wording for the OpenRouter `NotImplementedError` stub (the CONTEXT suggests: `print("🔧  OpenRouter text adapter coming in Phase 2 — set INFG_LLM_PROVIDER=gemini for now")`).

### Deferred Ideas (OUT OF SCOPE)

- Diagnostic print when `INFG_IMAGE_MODEL` is set.
- Overriding `_IMAGE_FALLBACK` via env var.
- OpenRouter HTTP adapter implementation (Phase 2).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROV-01 | User can set `INFG_LLM_PROVIDER=openrouter` in `.env` to route text generation through OpenRouter instead of Gemini | Resolver reads this var; OpenRouter branch stubs to NotImplementedError in Phase 1 — satisfies routing decision even without full implementation |
| PROV-02 | User can set `INFG_LLM_MODEL` to any model string to override default text model for HTML-output path | Resolver passes the value as the `model` component of the returned tuple; Gemini branch forwards it to `_call_gemini_text_mode()` |
| PROV-03 | User can set `INFG_LLM_API_KEY` as generic LLM provider API key | Read at module level alongside `_VERTEX_*` vars; stored as `_LLM_API_KEY`; not used in Phase 1 dispatch but must be present in env-read block |
| PROV-04 | User can set `INFG_OPENROUTER_API_KEY` as dedicated OpenRouter key | Read at module level; stored as `_OPENROUTER_API_KEY`; not used until Phase 2 but must be documented and read |
| PROV-05 | User can set `INFG_IMAGE_MODEL` to override default image model without touching code | Read at module level after `_load_dotenv()`; used to set the `model_name` default passed into `generate_pretty()` when `--model` is not explicitly provided |
| OROUTER-05 | User can override provider and model per-invocation via `--llm-provider` and `--llm-model` CLI flags | `argparse` already present; two new `add_argument()` calls with `default=None`; resolver reads `args.llm_provider` and `args.llm_model` |
</phase_requirements>

## Standard Stack

This phase introduces no new dependencies. Everything needed is already present.

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib | CLI flag parsing | Already used in `generate_pretty.py` — `ap.add_argument()` pattern is established |
| os.environ | stdlib | Env var reads | Already used for `INFG_API_KEY`, `INFG_VERTEX_PROJECT`, `INFG_VERTEX_LOCATION` |
| python-dotenv (custom) | n/a | `.env` parsing | `_load_dotenv()` already present — `os.environ.setdefault()` approach |

### Supporting
No new packages needed. `requests` is already in `requirements.txt` for Phase 2 but not used in Phase 1.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flat `if/elif` resolver | ABC / LiteLLM | Out of scope per locked decision — two providers do not justify abstraction |
| `os.environ.get()` at module level | Reading inside function | Module-level matches existing `_VERTEX_*` pattern and avoids repeated reads |

**Installation:** No new packages.

## Architecture Patterns

### File Layout (generate_pretty.py — section order)

The file already follows this structure; Phase 1 inserts into existing sections:

```
scripts/generate_pretty.py
├── [module docstring]
├── imports
├── _SKILL_DIR / _ENV_PATH
├── security helpers (_redact_key, _handle_credential_error)
├── _load_dotenv()
├── _load_dotenv(_ENV_PATH)          ← call site
├── [NEW] module-level env var reads for new provider vars  ← insert here
├── _VERTEX_* env reads              ← existing block to match
├── _AI_STUDIO_ONLY
├── google-genai conditional import
├── _build_genai_client()
├── [various helpers...]
├── _call_image_mode()
├── _call_text_mode()                ← RENAME to _call_gemini_text_mode()
├── HTML helpers
├── _IMAGE_FALLBACK constant
├── [NEW] _resolve_llm_provider()    ← insert before generate_pretty()
├── generate_pretty()                ← wire resolver into HTML path
└── __main__ / argparse              ← add --llm-provider, --llm-model
```

### Pattern 1: Module-Level Env Var Reads

**What:** Read env vars once at import time, store in private module-level constants.
**When to use:** All env var reads in `generate_pretty.py` — consistent with existing `_VERTEX_*` block.
**Example (existing pattern to match):**
```python
# Source: scripts/generate_pretty.py lines 115-117
_VERTEX_PROJECT  = os.environ.get("INFG_VERTEX_PROJECT",  "").strip()
_VERTEX_LOCATION = os.environ.get("INFG_VERTEX_LOCATION", "us-central1").strip()
_USE_VERTEX      = bool(_VERTEX_PROJECT)
```

New block to add immediately after this:
```python
# ── LLM provider configuration ────────────────────────────────────────────────
_LLM_PROVIDER     = os.environ.get("INFG_LLM_PROVIDER",      "").strip().lower()
_LLM_MODEL        = os.environ.get("INFG_LLM_MODEL",         "").strip()
_LLM_API_KEY      = os.environ.get("INFG_LLM_API_KEY",       "").strip()
_OPENROUTER_API_KEY = os.environ.get("INFG_OPENROUTER_API_KEY", "").strip()
_IMAGE_MODEL_ENV  = os.environ.get("INFG_IMAGE_MODEL",       "").strip()
```

### Pattern 2: Provider Resolver Function

**What:** Pure function — reads `args` (CLI flags), falls back to module-level env var constants, returns `(provider, model)` tuple.
**When to use:** Called once inside `generate_pretty()` before the HTML dispatch path.
**Example:**
```python
def _resolve_llm_provider(args) -> tuple[str, str | None]:
    """
    Resolve LLM provider and model from CLI flags and env vars.
    Precedence: CLI flag > env var > default ("gemini").
    Returns (provider, model_or_None).
    """
    provider = (getattr(args, "llm_provider", None) or _LLM_PROVIDER or "gemini").lower()
    model    = getattr(args, "llm_model", None) or _LLM_MODEL or None
    return provider, model
```

### Pattern 3: Flat if/elif Provider Dispatch

**What:** `if/elif` block inside the HTML path of `generate_pretty()` that dispatches to the correct adapter.
**When to use:** HTML generation path only (text models). Image path is unaffected.
**Example:**
```python
provider, llm_model = _resolve_llm_provider(args)

if provider == "gemini":
    effective_model = llm_model or model_name  # llm_model overrides image-path model_name for text
    raw_html, usage = _call_gemini_text_mode(prompt, client, effective_model)
elif provider == "openrouter":
    print("🔧  OpenRouter text adapter coming in Phase 2 — set INFG_LLM_PROVIDER=gemini for now")
    raise NotImplementedError("OpenRouter support coming in Phase 2")
else:
    print(f"❌  Unknown LLM provider: {provider!r}. Supported: gemini, openrouter")
    sys.exit(1)
```

### Pattern 4: argparse Extension

**What:** Add two optional flags to the existing `argparse` block. Both default to `None` so absence is detectable.
**When to use:** `__main__` block in `generate_pretty.py`.
**Example:**
```python
ap.add_argument("--llm-provider", default=None,
                help="LLM provider for text/HTML path: gemini (default) or openrouter")
ap.add_argument("--llm-model",    default=None,
                help="LLM model override for text/HTML path (e.g. gemini-2.5-pro)")
```

Note: argparse converts `--llm-provider` to `args.llm_provider` (hyphen → underscore) automatically.

### Pattern 5: INFG_IMAGE_MODEL Application

**What:** Apply the env var override to the `--model` default before `generate_pretty()` is called.
**When to use:** `__main__` block, after argparse but before `generate_pretty()` call.
**Example:**
```python
# Apply INFG_IMAGE_MODEL override if --model was not explicitly set
image_model = args.model
if _IMAGE_MODEL_ENV and args.model == "gemini-3.1-flash-image-preview":
    # Only override if user did not explicitly pass --model (still at default value)
    image_model = _IMAGE_MODEL_ENV

generate_pretty(config, args.output, args.type, image_model)
```

Alternative: pass `args` into `generate_pretty()` — but CONTEXT says resolver signature takes `args`, and `generate_pretty()` keeps `model_name: str` parameter. So apply the override in `__main__` before the call.

### Anti-Patterns to Avoid

- **Modifying `_build_genai_client()`:** The image path uses it; don't touch it in Phase 1. The resolver is only for the text/HTML path.
- **Passing `args` into `generate_pretty()`:** The function signature stays `generate_pretty(config, output, viz_type, model_name)`. The resolver takes `args` and is called in `__main__`, not inside `generate_pretty()`. However, `generate_pretty()` needs the resolved provider/model — see integration note below.
- **Overriding `_IMAGE_FALLBACK` via env var:** Explicitly deferred. Do not add this.
- **Printing when `INFG_IMAGE_MODEL` is set:** Explicitly deferred. Silent read only.
- **`os.environ.get()` inside a function body:** Don't read env vars inside `_resolve_llm_provider()` — read from the module-level constants already set.

### Integration Note: generate_pretty() Signature Change

The current signature is `generate_pretty(config, output, viz_type, model_name)`. For Phase 1 the HTML path needs to know the resolved provider and model. Two clean options:

**Option A (preferred per CONTEXT):** Resolve in `__main__` and pass `llm_provider` / `llm_model` as new optional kwargs:
```python
def generate_pretty(
    config: dict,
    output: str = "pretty_infographic.png",
    viz_type: str = "architecture",
    model_name: str = "gemini-3.1-flash-image-preview",
    llm_provider: str = "gemini",
    llm_model: str | None = None,
) -> Path:
```
`_resolve_llm_provider(args)` is called in `__main__` and the result is passed as kwargs. This keeps `generate_pretty()` testable without argparse.

**Option B:** Call `_resolve_llm_provider(args)` inside `generate_pretty()` by passing `args` as a parameter. This is more tightly coupled and harder to unit test.

**Recommendation:** Option A — matches the existing pattern where `model_name` is a plain string parameter, and makes the function signature self-documenting. The CONTEXT says resolver function takes `args`; that's fine for the `__main__` call site.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Env var precedence logic | Custom precedence machinery | `or` chaining: `args.llm_provider or _LLM_PROVIDER or "gemini"` — one line |
| Argument name normalization | Custom hyphen-to-underscore logic | argparse does this automatically for `--llm-provider` → `args.llm_provider` |
| Provider string normalization | Custom case logic | `.lower()` at read time on `_LLM_PROVIDER` and in resolver |

**Key insight:** The entire resolver can be implemented in ~10 lines. If it grows larger than 20 lines, the implementation has drifted from the locked `if/elif` design.

## Common Pitfalls

### Pitfall 1: Applying INFG_IMAGE_MODEL When --model Was Explicitly Set

**What goes wrong:** User passes `--model gemini-2.5-pro` and also has `INFG_IMAGE_MODEL=something` set — the env var wrongly overrides their explicit flag.
**Why it happens:** Naively applying `_IMAGE_MODEL_ENV` without checking whether `args.model` is at its default value.
**How to avoid:** Only apply `_IMAGE_MODEL_ENV` when `args.model == ap.get_default("model")` (the argparse default string `"gemini-3.1-flash-image-preview"`).
**Warning signs:** Tests with both `--model` and `INFG_IMAGE_MODEL` set produce unexpected model selection.

### Pitfall 2: _call_text_mode Rename Missing Call Site

**What goes wrong:** Function renamed to `_call_gemini_text_mode()` but the call at line ~855 inside `generate_pretty()` still says `_call_text_mode()` — `NameError` at runtime.
**Why it happens:** Rename applies only to the definition, not the call site.
**How to avoid:** Search for all occurrences of `_call_text_mode` before committing — there are two: the definition and the call site.
**Warning signs:** `NameError: name '_call_text_mode' is not defined` on first run.

### Pitfall 3: generate_pretty() Called Without args in Non-CLI Paths

**What goes wrong:** `generate_pretty()` is a public function — it can be imported and called without argparse. If `_resolve_llm_provider(args)` is called inside it and `args` is None, `getattr(None, ...)` raises `AttributeError`.
**Why it happens:** Assuming `args` is always a populated Namespace object.
**How to avoid:** Use Option A (pass resolved provider/model as plain string kwargs). `getattr(args, "llm_provider", None)` in the resolver also guards against this.
**Warning signs:** Import-based callers of `generate_pretty()` break.

### Pitfall 4: os.environ.setdefault vs os.environ.get Order

**What goes wrong:** `_load_dotenv()` uses `os.environ.setdefault()` — it does NOT overwrite existing env vars. If `INFG_LLM_PROVIDER` is already set in the shell environment before `_load_dotenv()` runs, the `.env` file value is ignored (correct behavior). If the module-level read happens before `_load_dotenv()` is called, the var won't be present yet.
**Why it happens:** Placing the new env var reads before `_load_dotenv(_ENV_PATH)` call.
**How to avoid:** New env var reads must be placed AFTER line 111 (`_load_dotenv(_ENV_PATH)`), matching the placement of `_VERTEX_PROJECT` reads at lines 115+.
**Warning signs:** `.env` values are silently ignored.

### Pitfall 5: LLM Model Ambiguity Between Text and Image Paths

**What goes wrong:** `INFG_LLM_MODEL` is applied to the image path as well, overriding the image model when an image model is in use.
**Why it happens:** Applying the resolved `llm_model` value unconditionally at the top of `generate_pretty()`.
**How to avoid:** The `llm_model` parameter only affects the HTML/text path. The `model_name` parameter continues to control the image path. In the dispatcher, use `llm_model or model_name` only inside the `if provider == "gemini":` branch of the HTML path.

## Code Examples

Verified patterns from existing source:

### Existing Env Var Read Pattern (lines 115-117)
```python
# Source: scripts/generate_pretty.py lines 115-117
_VERTEX_PROJECT  = os.environ.get("INFG_VERTEX_PROJECT",  "").strip()
_VERTEX_LOCATION = os.environ.get("INFG_VERTEX_LOCATION", "us-central1").strip()
_USE_VERTEX      = bool(_VERTEX_PROJECT)
```

### Existing argparse Pattern (lines 883-902)
```python
# Source: scripts/generate_pretty.py lines 883-902
ap = argparse.ArgumentParser(...)
ap.add_argument("--model", default="gemini-3.1-flash-image-preview",
                help="Gemini model (default: gemini-3.1-flash-image-preview)")
# new flags go here, matching this style:
ap.add_argument("--llm-provider", default=None,
                help="LLM provider for text/HTML path: gemini (default) or openrouter")
ap.add_argument("--llm-model",    default=None,
                help="LLM model override for text/HTML path")
```

### Existing Error Pattern (lines 168-182)
```python
# Source: scripts/generate_pretty.py lines 168-182
print(
    "❌  No credentials configured for pretty mode.\n"
    ...
)
sys.exit(1)
```

### _call_text_mode Current Definition (lines 715-734) — to be renamed
```python
# Source: scripts/generate_pretty.py lines 715-734
def _call_text_mode(
    prompt: str, client, model: str
) -> tuple[str, dict]:
    """Call Gemini for HTML text output. Returns (html_text, usage_dict)."""
    response = client.models.generate_content(...)
    ...
    return response.text, usage
```
Rename to `_call_gemini_text_mode()` — signature and body unchanged.

### generate_pretty() Call in __main__ (line 942)
```python
# Source: scripts/generate_pretty.py line 942
generate_pretty(config, args.output, args.type, args.model)
```
After Phase 1:
```python
llm_provider, llm_model = _resolve_llm_provider(args)
image_model = _IMAGE_MODEL_ENV if (_IMAGE_MODEL_ENV and args.model == "gemini-3.1-flash-image-preview") else args.model
generate_pretty(config, args.output, args.type, image_model,
                llm_provider=llm_provider, llm_model=llm_model)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded Gemini only | Flat if/elif provider dispatch | Phase 1 | OpenRouter can be wired in Phase 2 without touching the dispatch skeleton |
| `_call_text_mode()` | `_call_gemini_text_mode()` | Phase 1 | Name clearly scopes the function to Gemini; parallel `_call_openrouter_text_mode()` added in Phase 2 |
| Fixed image model | `INFG_IMAGE_MODEL` env var | Phase 1 | No code change needed to swap image models |

## Open Questions

1. **generate_pretty() signature — add kwargs or pass args object?**
   - What we know: CONTEXT says `_resolve_llm_provider(args)` is the resolver signature; `generate_pretty()` currently takes `model_name: str`
   - What's unclear: Whether to pass resolved values as new kwargs vs. restructure the call
   - Recommendation: Option A (new optional kwargs `llm_provider` and `llm_model`) — keeps the function callable without argparse and unit-testable

2. **`INFG_IMAGE_MODEL` override scope in __main__**
   - What we know: Only overrides when `--model` is at its default value (CLI > env)
   - What's unclear: Whether to detect "at default" via string comparison or via argparse `set_defaults` introspection
   - Recommendation: String comparison against `"gemini-3.1-flash-image-preview"` — simple, readable, matches the codebase's "no defensive null checks" philosophy

## Environment Availability

Step 2.6: SKIPPED (no external dependencies — phase is pure code/config edits to an existing Python file and `.env.example`; all required stdlib modules are already imported in the file).

## Validation Architecture

### Test Framework

No automated test framework exists in this project (confirmed by `.planning/codebase/TESTING.md`). The project's validation strategy is manual CLI testing and visual inspection.

| Property | Value |
|----------|-------|
| Framework | None — manual CLI validation |
| Config file | None |
| Quick run command | `python scripts/generate_pretty.py --help` (checks argparse wiring, no API call) |
| Full suite command | See manual acceptance tests below |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| PROV-01 | `INFG_LLM_PROVIDER=openrouter` routes to NotImplementedError stub | manual | `INFG_LLM_PROVIDER=openrouter python scripts/generate_pretty.py --text "test" --title "T"` | Should print stub message and exit non-zero |
| PROV-02 | `INFG_LLM_MODEL` overrides text model | manual | inspect resolver output in print statement or add temp debug print | No API call needed to verify resolver logic |
| PROV-03 | `INFG_LLM_API_KEY` is read into `_LLM_API_KEY` | manual | python -c import inspect of module-level constant | Phase 1 only reads; no dispatch use yet |
| PROV-04 | `INFG_OPENROUTER_API_KEY` is read into `_OPENROUTER_API_KEY` | manual | same as PROV-03 | Phase 1 only reads |
| PROV-05 | `INFG_IMAGE_MODEL` overrides default image model | manual | `INFG_IMAGE_MODEL=gemini-2.5-pro python scripts/generate_pretty.py --help` then trace model selection | Must not override explicit `--model` flag |
| OROUTER-05 | `--llm-provider` and `--llm-model` flags exist and take precedence | manual-automated | `python scripts/generate_pretty.py --help` verifies flags exist; `--llm-provider openrouter --text "x" --title "T"` triggers stub | Fully testable without credentials |

### Sampling Rate

- **Per change:** `python scripts/generate_pretty.py --help` (zero API calls, verifies parse-time correctness)
- **Phase gate:** All manual acceptance tests above pass before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] No test framework to install — manual validation only per project conventions
- [ ] No Wave 0 test file creation needed — project has no test infrastructure and TESTING.md documents this as intentional

## Sources

### Primary (HIGH confidence)
- Direct source read of `scripts/generate_pretty.py` (lines 1-943) — all pattern claims are derived from the actual file
- `.planning/codebase/CONVENTIONS.md` — naming, error handling, module organization patterns
- `.planning/codebase/TESTING.md` — confirmed absence of test framework
- `01-CONTEXT.md` — all locked decisions are verbatim from user discussion

### Secondary (MEDIUM confidence)
- Python stdlib `argparse` docs — hyphen-to-underscore conversion for `dest` is documented behavior (HIGH confidence from training data, verified by codebase usage pattern)
- `os.environ.setdefault()` ordering behavior — HIGH confidence stdlib behavior, confirmed by reading `_load_dotenv()` implementation

### Tertiary (LOW confidence)
- None — all claims verifiable from codebase source or stdlib docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all patterns from existing file
- Architecture: HIGH — all patterns directly observed in `generate_pretty.py`; locked decisions from CONTEXT.md
- Pitfalls: HIGH — derived from reading the actual code (rename call site, env var read ordering, INFG_IMAGE_MODEL override scope)
- Open questions: MEDIUM — architectural choice between two valid approaches; either works

**Research date:** 2026-03-23
**Valid until:** 2026-06-23 (stable — Python stdlib, no external packages, locked decisions)
