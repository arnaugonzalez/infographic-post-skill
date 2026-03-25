# Phase 2: OpenRouter Text Adapter - Research

**Researched:** 2026-03-23
**Domain:** OpenRouter HTTP API, Python requests library, error handling patterns
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Dependency Management**
- Add `requests` to `requirements.txt` — it becomes a new hard runtime dependency for the OpenRouter path
- Import `requests` with `try/except ImportError` and a `_REQUESTS_OK = True/False` flag — matches the existing `_GENAI_OK` pattern in `generate_pretty.py`

**Error Message Design**
- 401 invalid key: `"❌  OpenRouter API key is invalid (401) — check INFG_OPENROUTER_API_KEY in your .env"` then `sys.exit(1)`
- 402 insufficient credits: `"❌  OpenRouter account has insufficient credits (402) — add credits at openrouter.ai/credits"` then `sys.exit(1)`
- Other non-200 status codes: show status code + first 200 chars of response body for debugging, then `sys.exit(1)`
- Model format validation (no slash): validate in resolver before any API call with example: `"❌  OpenRouter model must include provider prefix: 'openai/gpt-4o', got 'gpt-4o'"` then `sys.exit(1)`

**Token Cost Report Format**
- Placement: end of stdout after `✅ saved` — same position as Gemini cost output
- Format: indented multi-line matching existing cost report style:
  ```
    Input tokens:  N
    Output tokens: M
  ```
- Show cost if `usage.total_cost` is present in the OpenRouter response: `"  Cost:          $X.XXXXX"` — omit if not returned

**HTML Path Integration**
- Reuse `_gen_via_html_to_png()` directly — OpenRouter adapter replaces only the text-generation call; Playwright/HTML-to-PNG pipeline is shared
- Same system prompt as Gemini text mode — task is identical (generate infographic HTML), no model-specific tuning
- Playwright missing + OpenRouter provider → same existing Playwright check (provider-agnostic); no special error

### Claude's Discretion
- Exact placement of `_REQUESTS_OK` guard (where to print the "requests not installed" error — likely in the OpenRouter dispatch branch)
- Whether to print the OpenRouter model being used (like Gemini prints the backend label) — follow existing print patterns

### Deferred Ideas (OUT OF SCOPE)
- Streaming response support for large OpenRouter models — deferred, not in v1.0 success criteria
- Cost estimate via OpenRouter `/models` pricing endpoint — deferred to v2 (EXTPROV-03)
- `openai` Python SDK instead of raw `requests` — deferred to v1.x per Phase 1 key decision
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OROUTER-01 | User can generate infographics via the HTML-output path using any LLM available on OpenRouter when `INFG_LLM_PROVIDER=openrouter` | OpenRouter `/api/v1/chat/completions` is OpenAI-compatible; `requests.post()` with Bearer token is sufficient; `response["choices"][0]["message"]["content"]` yields HTML |
| OROUTER-02 | User sees a clear, actionable error message when OpenRouter API key is invalid (401) or account has insufficient credits (402) | Confirmed: OpenRouter uses HTTP 401 for bad keys and 402 for credit exhaustion; response body contains JSON `error.message`; `response.status_code` check before parsing content |
| OROUTER-03 | User sees a validation error with correct format example if model name is missing the required `provider/model` format before any API call is made | Pure Python string check: `"/" not in model` fires before `requests.post()`; no library needed |
| OROUTER-04 | User sees token usage counts (input/output tokens) after a successful OpenRouter run in the cost report section | `response["usage"]["prompt_tokens"]` and `response["usage"]["completion_tokens"]` always present on success; `total_cost` available only via separate `/api/v1/generation` endpoint, NOT in chat completions response body |
</phase_requirements>

---

## Summary

Phase 2 is a narrow, well-bounded implementation task. The existing `generate_pretty.py` already contains a `NotImplementedError` stub for OpenRouter at the correct dispatch point (line ~878). The work is to replace that stub with a working `_call_openrouter_text_mode()` function that calls `https://openrouter.ai/api/v1/chat/completions` using `requests.post()`, handles HTTP 401/402 errors with prescriptive messages, validates the `provider/model` format before any network call, and appends token counts to stdout after a successful run.

OpenRouter's chat completions endpoint is strictly OpenAI-compatible. The request requires an `Authorization: Bearer <key>` header and a JSON body with `model` and `messages`. The response includes `choices[0].message.content` for the HTML output and a `usage` object with `prompt_tokens` and `completion_tokens`. Note: `total_cost` is NOT present in the chat completions response; it is only available via the separate `/api/v1/generation` endpoint (identified by the response `id`). The CONTEXT.md decision to show cost "if `usage.total_cost` is present" must be interpreted as: show it only if the field unexpectedly appears — in practice it will be absent and the cost line will be omitted.

The `requests` library (version 2.31.0) is already installed in this environment, so the import guard is a safety pattern rather than a blocking concern. The `requirements.txt` change makes it a declared dependency so new installs always have it.

**Primary recommendation:** Implement `_call_openrouter_text_mode(prompt, model, api_key)` as a standalone function, add `_REQUESTS_OK` guard at module top, wire into the existing `elif llm_provider == "openrouter"` branch, and add model slash-validation at the entry of that branch.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.31.0 (installed) | HTTP POST to OpenRouter API | Explicitly chosen over `openai` SDK per Phase 1 key decision; zero new install overhead in this environment |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sys | stdlib | `sys.exit(1)` for fatal errors | Already established pattern in codebase |
| os | stdlib | `os.environ.get()` for API key | Already used for `_OPENROUTER_API_KEY` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests | openai SDK | Deferred to v1.x — adds dependency, overkill for one endpoint |
| requests | httpx | No advantage; not in requirements |

**Installation:**
```bash
# requests is already installed in this environment
# Add to requirements.txt (no comment — it is now a hard dependency):
pip install requests
```

**Version verification:** `requests` 2.31.0 is installed (verified via `pip3 show requests`).

---

## Architecture Patterns

### Recommended Project Structure

No new files or directories. All changes are within:

```
scripts/
└── generate_pretty.py     # Add _REQUESTS_OK guard + _call_openrouter_text_mode()
requirements.txt           # Add `requests>=2.28` as hard dependency
```

### Pattern 1: Conditional Import Guard (mirrors `_GENAI_OK`)

**What:** Import `requests` at module top inside `try/except ImportError`; set `_REQUESTS_OK` flag.
**When to use:** Any optional or new dependency that may not be installed.
**Example:**

```python
# Source: existing generate_pretty.py _GENAI_OK pattern (line ~136)
try:
    import requests       # pip install requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False
```

### Pattern 2: OpenRouter HTTP Call

**What:** Single `requests.post()` call to the OpenAI-compatible endpoint.
**When to use:** When `llm_provider == "openrouter"`.
**Example:**

```python
# Source: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    },
    timeout=120,
)
```

### Pattern 3: Status-First Error Handling

**What:** Check `resp.status_code` before attempting JSON parse; map known codes to specific messages.
**When to use:** After every `requests.post()` call to the OpenRouter API.
**Example:**

```python
if resp.status_code == 401:
    print("❌  OpenRouter API key is invalid (401) — check INFG_OPENROUTER_API_KEY in your .env")
    sys.exit(1)
if resp.status_code == 402:
    print("❌  OpenRouter account has insufficient credits (402) — add credits at openrouter.ai/credits")
    sys.exit(1)
if resp.status_code != 200:
    print(f"❌  OpenRouter API error ({resp.status_code}): {resp.text[:200]}")
    sys.exit(1)
```

### Pattern 4: Model Format Validation (no-slash check)

**What:** String guard before any API call.
**When to use:** At the entry of the OpenRouter dispatch branch (or in `_resolve_llm_provider`), before `_call_openrouter_text_mode()` is called.
**Example:**

```python
# Validate model format — OpenRouter requires "provider/model" format
if llm_model and "/" not in llm_model:
    print(
        f"❌  OpenRouter model must include provider prefix: "
        f"'openai/gpt-4o', got {llm_model!r}"
    )
    sys.exit(1)
```

### Pattern 5: Token Cost Report (OpenRouter variant)

**What:** Print input/output token counts after a successful run; match indentation of existing Gemini cost block.
**When to use:** After `_call_openrouter_text_mode()` succeeds, replacing or alongside existing `print_cost_report`.

```python
# After successful OpenRouter generation
print(f"  Input tokens:  {usage['prompt_tokens']}")
print(f"  Output tokens: {usage['completion_tokens']}")
if usage.get("total_cost") is not None:
    print(f"  Cost:          ${usage['total_cost']:.5f}")
```

### Anti-Patterns to Avoid

- **Parsing JSON before checking status_code:** `resp.json()` will raise on 401/402 HTML error pages — always check `resp.status_code` first.
- **Omitting timeout:** `requests.post()` without `timeout` can hang indefinitely; use `timeout=120`.
- **Using `resp.json()["usage"]["total_cost"]`:** `total_cost` is NOT in the chat completions response; it only comes from the `/api/v1/generation` endpoint polled after the fact. Guard with `.get()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP client | Custom socket code | `requests.post()` | Handles redirects, TLS, keep-alive, timeout |
| Model format regex | Complex validation | `"/" not in model` string check | The rule is simple: exactly one slash required |

**Key insight:** OpenRouter's API is intentionally OpenAI-compatible. No special client library is needed — a single `requests.post()` call is the canonical approach for Python scripts.

---

## Common Pitfalls

### Pitfall 1: `total_cost` Not in Chat Completions Response

**What goes wrong:** Code tries to read `resp.json()["usage"]["total_cost"]` and gets a `KeyError`.
**Why it happens:** OpenRouter's chat completions endpoint returns `prompt_tokens`, `completion_tokens`, and `total_tokens` in `usage`, but NOT `total_cost`. Cost data lives in the `/api/v1/generation` metadata endpoint (requires a second HTTP call with the response `id`).
**How to avoid:** Use `usage.get("total_cost")` and only print the cost line if the value is present. Per CONTEXT.md, cost display is conditional.
**Warning signs:** `KeyError: 'total_cost'` in test run.

### Pitfall 2: 401 Response Body Is Not JSON

**What goes wrong:** `resp.json()` raises `JSONDecodeError` when OpenRouter returns a plain-text or HTML 401 page.
**Why it happens:** Some error responses from the OpenRouter gateway are not JSON-encoded.
**How to avoid:** Always check `resp.status_code` before calling `resp.json()`. Use `resp.text[:200]` for the generic fallback message.
**Warning signs:** `JSONDecodeError` inside OpenRouter error handling.

### Pitfall 3: Missing `_REQUESTS_OK` Guard in Dispatch Branch

**What goes wrong:** User without `requests` installed sees an `ImportError` traceback instead of the friendly "not installed" message.
**Why it happens:** The guard is set at import time but never consulted before calling OpenRouter code.
**How to avoid:** In the `elif llm_provider == "openrouter"` branch, check `_REQUESTS_OK` first and print a helpful install message + `sys.exit(1)` if False.

### Pitfall 4: Model Validation Fires After API Call

**What goes wrong:** A bad model string like `"gpt-4o"` goes through to OpenRouter, which returns a non-obvious 400 error.
**Why it happens:** Validation placed after the `requests.post()` call or missing entirely.
**How to avoid:** Validate the slash-format before any I/O. Place the check at the entry of the `elif llm_provider == "openrouter"` block.

### Pitfall 5: API Key Precedence Not Respected

**What goes wrong:** `INFG_LLM_API_KEY` is used when `INFG_OPENROUTER_API_KEY` is set, or vice-versa.
**Why it happens:** Key resolution logic is wrong.
**How to avoid:** Resolve the API key as: `_OPENROUTER_API_KEY or _LLM_API_KEY`. If neither is set, print a missing-key error and `sys.exit(1)`.

---

## Code Examples

Verified patterns from official sources:

### OpenRouter Chat Completions Request (verified against official docs)

```python
# Source: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": model,   # must be "provider/model" format e.g. "openai/gpt-4o"
        "messages": [{"role": "user", "content": prompt}],
    },
    timeout=120,
)
```

### OpenRouter Response Parsing (verified field names)

```python
# Source: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
data = resp.json()
html_text  = data["choices"][0]["message"]["content"]
usage      = data.get("usage", {})
prompt_tok = usage.get("prompt_tokens", 0)
compl_tok  = usage.get("completion_tokens", 0)
# total_cost is NOT in this response — only in /api/v1/generation metadata endpoint
total_cost = usage.get("total_cost")   # will be None in practice
```

### Existing `_GENAI_OK` Pattern to Mirror (from generate_pretty.py lines ~136-141)

```python
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_OK = True
except ImportError:
    _GENAI_OK = False
```

### Existing Error/Exit Pattern (from generate_pretty.py)

```python
print("❌  Some message here")
sys.exit(1)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `_call_text_mode()` (generic) | `_call_gemini_text_mode()` (explicit) | Phase 1 | Disambiguates Gemini vs OpenRouter paths |
| `NotImplementedError` stub for OpenRouter | Working `_call_openrouter_text_mode()` | Phase 2 (this phase) | Enables OROUTER-01 through OROUTER-04 |

**Deprecated/outdated:**
- `NotImplementedError("OpenRouter support coming in Phase 2")` stub: must be replaced, not left in place.

---

## Open Questions

1. **Should the print for OpenRouter model mirror Gemini's backend label print?**
   - What we know: CONTEXT.md marks this as Claude's Discretion; Gemini prints `"🔑  Backend: AI Studio (API key)"` before generation.
   - What's unclear: Whether printing `"🤖  OpenRouter model: {model}"` adds useful signal or clutter.
   - Recommendation: Print the model name for observability — follow the existing `print(f"🤖  Calling {model_name} (HTML generation mode) …")` pattern already in the HTML path.

2. **Where exactly to place the `_REQUESTS_OK` guard check?**
   - What we know: CONTEXT.md marks this as Claude's Discretion; the natural placement is the `elif llm_provider == "openrouter"` branch entry.
   - Recommendation: Check `_REQUESTS_OK` as the first line in the `elif llm_provider == "openrouter"` block; print install hint and `sys.exit(1)` if False.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| requests | OpenRouter HTTP call | Yes | 2.31.0 | — |
| Python 3.9+ | f-strings, `str | None` types | Yes | 3.12.3 | — |
| Network (openrouter.ai) | OROUTER-01 live test | Assumed | — | Cannot test live without key |

**Missing dependencies with no fallback:** None — all code-level dependencies are present.

**Note on live testing:** A valid `INFG_OPENROUTER_API_KEY` is needed for integration testing. Unit tests can mock `requests.post()` responses without a real key.

---

## Validation Architecture

No test framework exists in this project (no `pytest.ini`, no `tests/` directory, no test files found). The project currently validates via manual CLI runs.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None (no test infrastructure detected) |
| Config file | None |
| Quick run command | `python scripts/generate_pretty.py --text "Test" --llm-provider openrouter --llm-model openai/gpt-4o --output /tmp/test_out.html` |
| Full suite command | Manual verification per success criteria |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OROUTER-01 | HTML generated via OpenRouter | manual / integration | Requires live key | No test infra |
| OROUTER-02 | Clear 401/402 error messages | manual | Run with bad key | No test infra |
| OROUTER-03 | Slash-format validation fires before API call | unit (mockable) | `python -c "import scripts..."` | No test infra |
| OROUTER-04 | Token counts in stdout after successful run | manual / integration | Requires live key | No test infra |

### Sampling Rate
- **Per task commit:** Manual smoke test of model validation (no key needed): `python scripts/generate_pretty.py --text "Test" --llm-provider openrouter --llm-model badmodelformat --output /tmp/t.html`
- **Per wave merge:** Full manual run with a valid OpenRouter key checking all 5 success criteria
- **Phase gate:** All 5 success criteria verified by human before `/gsd:verify-work`

### Wave 0 Gaps
- No test files — project has no test infrastructure. Validation is entirely via manual CLI runs.
- If unit tests were to be added: `tests/test_openrouter_adapter.py` covering OROUTER-03 (model validation, no key needed) and mock-based tests for OROUTER-02 (401/402 responses).

*(Existing test infrastructure: none found — manual verification is the established project pattern)*

---

## Sources

### Primary (HIGH confidence)
- https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request — request/response format, usage fields, status codes
- https://openrouter.ai/docs/api/api-reference/generations/get-generation — confirms `total_cost` lives in generation endpoint, not chat completions
- `scripts/generate_pretty.py` (project file) — existing `_GENAI_OK` pattern, `_call_gemini_text_mode()` signature, error/exit conventions, dispatch structure

### Secondary (MEDIUM confidence)
- https://openrouter.ai/docs/api/reference/overview — general API overview confirming OpenAI-compatible schema
- WebSearch results confirming `prompt_tokens`/`completion_tokens` field names in `usage` object

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `requests` is already installed; the API is OpenAI-compatible and well-documented
- Architecture: HIGH — insertion point (`elif llm_provider == "openrouter"`) is unambiguous in existing code
- Pitfalls: HIGH — `total_cost` absence verified against official docs; other pitfalls derived from the API contract
- Error codes: HIGH — 401/402 semantics confirmed via official OpenRouter docs

**Research date:** 2026-03-23
**Valid until:** 2026-09-23 (OpenRouter API is stable; `requests` API is stable)
