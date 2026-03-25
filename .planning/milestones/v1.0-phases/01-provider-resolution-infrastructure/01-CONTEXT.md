# Phase 1: Provider Resolution Infrastructure - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire env vars and CLI flags for LLM provider/model configuration, rename `_call_text_mode()` to `_call_gemini_text_mode()`, build a flat `if/elif` provider resolver, and update `.env.example` — all while keeping existing Gemini paths working identically for current users.

</domain>

<decisions>
## Implementation Decisions

### Image Model Override
- CLI `--model` flag takes precedence over `INFG_IMAGE_MODEL` env var (standard CLI > env > default)
- `INFG_IMAGE_MODEL` overrides only the hardcoded default (`gemini-3.1-flash-image-preview`); `_IMAGE_FALLBACK` stays as `gemini-2.5-flash-image` — it's a 404 safety net, not a user-configurable default
- `INFG_IMAGE_MODEL` is read silently (no diagnostic print — consistent with existing `_VERTEX_*` behavior)

### LLM Model Scope
- `INFG_LLM_MODEL` controls only the text/HTML generation path (LLM text generation)
- Image path remains controlled by `--model` flag and `INFG_IMAGE_MODEL` env var
- Separation prevents ambiguity: text models ≠ image models

### Provider Resolver Design
- Flat `if/elif` dispatch in `generate_pretty.py` — no ABC, no registry, no LiteLLM (per key decisions)
- Function: `_resolve_llm_provider(args)` → returns `(provider: str, model: str | None)` tuple
- Provider "gemini" is the default when `INFG_LLM_PROVIDER` is not set
- OpenRouter selected → raise `NotImplementedError("OpenRouter support coming in Phase 2")` with a clear print message

### CLI Flags
- `--llm-provider` and `--llm-model` added only to `generate_pretty.py` (only script with LLM text path)
- Precedence: CLI flags > env vars > defaults
- Existing `--model` flag remains as Gemini image model override — not deprecated

### Rename
- `_call_text_mode()` renamed to `_call_gemini_text_mode()` to disambiguate from future `_call_openrouter_text_mode()`

### .env.example
- Add entries for: `INFG_LLM_PROVIDER`, `INFG_LLM_MODEL`, `INFG_LLM_API_KEY`, `INFG_OPENROUTER_API_KEY`, `INFG_IMAGE_MODEL`
- All new vars are additive — existing users with only `INFG_API_KEY` / `INFG_VERTEX_PROJECT` see no behavior change

### Claude's Discretion
- Exact placement of env var reads (module-level, alongside existing `_VERTEX_*` vars)
- Error message wording for the OpenRouter NotImplementedError stub

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_load_dotenv()` — already parses `.env` into `os.environ`; all new env vars just use `os.environ.get()`
- `_build_genai_client(model_name)` — existing Gemini client builder; untouched in Phase 1
- `generate_pretty()` — main entry point; `model_name` parameter stays; provider routing wraps around it
- `argparse` already set up in the CLI section; adding `--llm-provider` / `--llm-model` is straightforward

### Established Patterns
- Env vars read at module level after `_load_dotenv()` (see `_VERTEX_PROJECT`, `_VERTEX_LOCATION`, `_USE_VERTEX`)
- Error messages: `print("❌  ...")` then `sys.exit(1)` for fatal errors
- Private helpers prefixed with `_`
- Type hints with Python 3.10+ `str | None` unions

### Integration Points
- `_call_text_mode()` → rename to `_call_gemini_text_mode()` (called at line ~855 in `generate_pretty()`)
- `generate_pretty()` function — provider resolver plugs in here to decide dispatch path
- `.env.example` — new section for LLM provider config
- CLI `__main__` block — where `--llm-provider` / `--llm-model` args are added

</code_context>

<specifics>
## Specific Ideas

- The resolver stub for OpenRouter should print a clear message before raising: `print("🔧  OpenRouter text adapter coming in Phase 2 — set INFG_LLM_PROVIDER=gemini for now")`
- No new module/file needed — everything stays in `generate_pretty.py`

</specifics>

<deferred>
## Deferred Ideas

- Diagnostic print when `INFG_IMAGE_MODEL` is set (deferred — silent config is consistent with existing behavior)
- Overriding `_IMAGE_FALLBACK` via env var (deferred to v2)
- OpenRouter HTTP adapter implementation (Phase 2)

</deferred>
