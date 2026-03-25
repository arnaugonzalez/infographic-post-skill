# Phase 2: OpenRouter Text Adapter - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement `_call_openrouter_text_mode()` in `generate_pretty.py` — a flat `requests.post()` adapter that routes the HTML-output text path through any OpenRouter LLM. Includes model format validation before the API call, specific 401/402 error messages with action hints, and token cost reporting appended to the existing cost report section. The Playwright HTML-to-PNG pipeline is reused unchanged.

</domain>

<decisions>
## Implementation Decisions

### Dependency Management
- Add `requests` to `requirements.txt` — it becomes a new hard runtime dependency for the OpenRouter path
- Import `requests` with `try/except ImportError` and a `_REQUESTS_OK = True/False` flag — matches the existing `_GENAI_OK` pattern in `generate_pretty.py`

### Error Message Design
- 401 invalid key: `"❌  OpenRouter API key is invalid (401) — check INFG_OPENROUTER_API_KEY in your .env"` then `sys.exit(1)`
- 402 insufficient credits: `"❌  OpenRouter account has insufficient credits (402) — add credits at openrouter.ai/credits"` then `sys.exit(1)`
- Other non-200 status codes: show status code + first 200 chars of response body for debugging, then `sys.exit(1)`
- Model format validation (no slash): validate in resolver before any API call with example: `"❌  OpenRouter model must include provider prefix: 'openai/gpt-4o', got 'gpt-4o'"` then `sys.exit(1)`

### Token Cost Report Format
- Placement: end of stdout after `✅ saved` — same position as Gemini cost output
- Format: indented multi-line matching existing cost report style:
  ```
    Input tokens:  N
    Output tokens: M
  ```
- Show cost if `usage.total_cost` is present in the OpenRouter response: `"  Cost:          $X.XXXXX"` — omit if not returned

### HTML Path Integration
- Reuse `_gen_via_html_to_png()` directly — OpenRouter adapter replaces only the text-generation call; Playwright/HTML-to-PNG pipeline is shared
- Same system prompt as Gemini text mode — task is identical (generate infographic HTML), no model-specific tuning
- Playwright missing + OpenRouter provider → same existing Playwright check (provider-agnostic); no special error

### Claude's Discretion
- Exact placement of `_REQUESTS_OK` guard (where to print the "requests not installed" error — likely in the OpenRouter dispatch branch)
- Whether to print the OpenRouter model being used (like Gemini prints the backend label) — follow existing print patterns

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_call_gemini_text_mode()` — sibling function; `_call_openrouter_text_mode()` follows same signature pattern
- `_gen_via_html_to_png()` — Playwright HTML-to-PNG pipeline; reused unchanged for OpenRouter path
- `_resolve_llm_provider(args)` → `(provider, model)` tuple — already wired; Phase 2 removes the `NotImplementedError` stub
- `_load_dotenv()` — loads `INFG_OPENROUTER_API_KEY` / `INFG_LLM_API_KEY` already
- Existing cost report print section after generation — token counts appended here
- `print("❌  ..."); sys.exit(1)` — established fatal error pattern

### Established Patterns
- Conditional import with `_GENAI_OK` flag (see top of `generate_pretty.py`) — mirror for `_REQUESTS_OK`
- `_build_genai_client()` returns `(client, backend_label)` — `_call_openrouter_text_mode()` returns the HTML string
- Error messages use `"❌  "` prefix (two spaces after emoji) and `sys.exit(1)`
- Cost report: indented lines with consistent column alignment

### Integration Points
- `_resolve_llm_provider(args)` dispatch — remove `NotImplementedError` stub, route to `_call_openrouter_text_mode()`
- `generate_pretty()` main function — provider dispatch already structured from Phase 1
- `requirements.txt` — add `requests`
- `.env.example` already has `INFG_OPENROUTER_API_KEY` entry from Phase 1

</code_context>

<specifics>
## Specific Ideas

- Model validation (no-slash check) should fire in `_resolve_llm_provider()` or at the OpenRouter dispatch entry, before `requests.post()` is called
- The `_call_openrouter_text_mode()` function sends to `https://openrouter.ai/api/v1/chat/completions` (OpenAI-compatible endpoint)
- OpenRouter response format: `response_json["choices"][0]["message"]["content"]` for the HTML string; `response_json["usage"]` for token counts

</specifics>

<deferred>
## Deferred Ideas

- Streaming response support for large OpenRouter models — deferred, not in v1.0 success criteria
- Cost estimate via OpenRouter `/models` pricing endpoint — deferred to v2 (EXTPROV-03)
- `openai` Python SDK instead of raw `requests` — deferred to v1.x per Phase 1 key decision

</deferred>
