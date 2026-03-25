# Phase 3: Deploy Readiness and OSS Hardening - Research

**Researched:** 2026-03-23
**Domain:** Python OSS hardening — API key redaction, env var documentation, docs accuracy, optional-dep isolation
**Confidence:** HIGH

## Summary

Phase 3 is a pure hardening phase with four well-scoped tasks. No new external libraries are needed. Every task has an existing pattern in the codebase to mirror. The work splits cleanly into: security (DEPLOY-01 key redaction), documentation audit (DEPLOY-02 env var coverage, DEPLOY-03 docs accuracy), and isolation (DEPLOY-04 lazy import guard).

The existing `_KEY_PATTERN`/`_redact_key()` infrastructure in `generate_pretty.py` already handles Google AI Studio keys (`AIza...` prefix). DEPLOY-01 is a pure extension: add a second regex pattern for the `sk-or-v1-` prefix and update the single `_redact_key()` function. No structural change needed.

DEPLOY-02 is complete as-is: all `os.environ.get()` calls are in `generate_pretty.py` only, and all eight variables (`INFG_VERTEX_PROJECT`, `INFG_VERTEX_LOCATION`, `INFG_LLM_PROVIDER`, `INFG_LLM_MODEL`, `INFG_LLM_API_KEY`, `INFG_OPENROUTER_API_KEY`, `INFG_IMAGE_MODEL`, `INFG_API_KEY`) already have entries in `.env.example`. Audit confirms no gaps.

DEPLOY-03 requires: (1) Python version bump from 3.8 to 3.9+ in README.md and SKILL.md frontmatter, (2) add an OpenRouter setup section to both docs. The `str | None` union type hint syntax in `generate_pretty.py` (lines 806, 834, 851) requires Python 3.10+ at runtime, but the hard minimum for `dict[str, ...]` built-in generics used at line 248 is Python 3.9+. The stated target is 3.9+ per success criteria.

DEPLOY-04 requires adding a `try/except ImportError` guard for the `openai` SDK package in `generate_pretty.py` — modeled after the existing `_GENAI_OK` and `_REQUESTS_OK` patterns. Currently `generate_pretty.py` has no openai import at all; the guard is a defensive measure to ensure the module can still load (and `generate.py` can still run) if openai is ever added as an optional import in a future PR. The task also requires a verification test.

**Primary recommendation:** Mirror existing patterns exactly — extend `_KEY_PATTERN` for DEPLOY-01, add `_OPENAI_OK` guard for DEPLOY-04, fix two doc files for DEPLOY-03, confirm env var audit is clean for DEPLOY-02.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — all implementation choices are at Claude's discretion.

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure/documentation phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

### Deferred Ideas (OUT OF SCOPE)
None — discuss phase skipped.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPLOY-01 | OpenRouter API keys (`sk-or-v1-...` format) are redacted in all error output, log messages, and tracebacks — matching existing Google key redaction behavior | Extend `_KEY_PATTERN` regex in `generate_pretty.py` line 58; update `_redact_key()` to cover both patterns; apply to OpenRouter error paths at lines 774, 780 |
| DEPLOY-02 | Every env var consumed by `os.environ.get()` in all scripts is documented in `.env.example` with description and example value | Audit confirmed: only `generate_pretty.py` uses `os.environ.get()`; all 8 vars already in `.env.example`; verify `INFG_API_KEY` has inline description matching the others |
| DEPLOY-03 | SKILL.md and README.md document the OpenRouter setup path and correct Python version from 3.8 to 3.9+ | Two files to update: SKILL.md frontmatter `python: ">=3.8"` → `">=3.9"` and `dependencies.pip` section; README.md `Python 3.8+` → `Python 3.9+`; add OpenRouter setup subsection in both |
| DEPLOY-04 | Infographic generation via matplotlib offline path works correctly when `openai` package is not installed (lazy import guard) | Add `try: import openai as _openai_lib; _OPENAI_OK = True except ImportError: _openai_lib = None; _OPENAI_OK = False` block to `generate_pretty.py` modeled after `_GENAI_OK` pattern; add test verifying offline path survives without openai |
</phase_requirements>

---

## Standard Stack

### Core (no new packages needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `re` | stdlib | Regex for key redaction | Already used for `_KEY_PATTERN` |
| Python `os` | stdlib | Env var reads | Already used throughout |
| pytest | 9.0.2 | Test framework | Already used in `tests/test_openrouter.py` |

### No new dependencies required

All four requirements are satisfied through code edits, documentation edits, and tests. No `pip install` needed.

## Architecture Patterns

### Pattern 1: Key Redaction (for DEPLOY-01)

**What:** A module-level compiled regex + single function that scrubs keys before any print/output.

**Existing implementation (lines 58-63 of generate_pretty.py):**
```python
# Source: scripts/generate_pretty.py lines 58-63
_KEY_PATTERN = re.compile(r"AIza[a-zA-Z0-9_-]{30,}")

def _redact_key(text: str) -> str:
    """Replace any embedded API key values with [REDACTED] before printing."""
    return _KEY_PATTERN.sub("[REDACTED]", text)
```

**Extension for DEPLOY-01:** Update `_KEY_PATTERN` to a combined pattern covering both Google (`AIza...`) and OpenRouter (`sk-or-v1-...`) keys. The OpenRouter key format is `sk-or-v1-` followed by hex characters (typically 64 hex chars, but treat as `[a-zA-Z0-9_-]{30,}` for safety margin).

**Pattern to add:**
```python
# Source: Pattern derived from OpenRouter key format sk-or-v1-<hex64>
_KEY_PATTERN = re.compile(
    r"AIza[a-zA-Z0-9_-]{30,}"         # Google AI Studio keys
    r"|sk-or-v1-[a-zA-Z0-9_-]{30,}"   # OpenRouter keys
)
```

The success criteria specifies redaction to `sk-or-v1-[REDACTED]` — not `[REDACTED]`. This means a two-pattern approach with different substitutions, OR a single sub that retains the prefix. Use a `re.sub` with a lambda or two separate patterns:

```python
def _redact_key(text: str) -> str:
    """Replace embedded API key values with [REDACTED] before printing."""
    text = re.sub(r"AIza[a-zA-Z0-9_-]{30,}", "[REDACTED]", text)
    text = re.sub(r"sk-or-v1-[a-zA-Z0-9_-]{30,}", "sk-or-v1-[REDACTED]", text)
    return text
```

**CRITICAL NOTE:** The success criteria says redacted form is `sk-or-v1-[REDACTED]` (prefix retained), while the Google key becomes `[REDACTED]` (no prefix). The implementation must match this asymmetry. The current module-level `_KEY_PATTERN` uses `.sub("[REDACTED]", text)` as a single replacement — split into two separate `re.sub` calls to handle different output formats.

### Pattern 2: Optional Import Guard (for DEPLOY-04)

**What:** Module-level `try/except ImportError` sets a `_FLAG` boolean; all code paths that need the optional package check the flag first.

**Existing implementations to mirror:**

```python
# Source: scripts/generate_pretty.py lines 136-141 (_GENAI_OK pattern)
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_OK = True
except ImportError:
    _GENAI_OK = False

# Source: scripts/generate_pretty.py lines 144-149 (_REQUESTS_OK pattern)
try:
    import requests as _requests_lib
    _REQUESTS_OK = True
except ImportError:
    _requests_lib = None
    _REQUESTS_OK = False
```

**Pattern for DEPLOY-04:**
```python
# openai SDK — optional, deferred to v1.x; guard prevents ImportError on offline path
try:
    import openai as _openai_lib   # pip install openai
    _OPENAI_OK = True
except ImportError:
    _openai_lib = None
    _OPENAI_OK = False
```

Place this block immediately after the `_REQUESTS_OK` block (lines 144-149) to maintain the grouping of optional-dependency guards.

### Pattern 3: Env Var Documentation (for DEPLOY-02)

**Current .env.example status — AUDIT RESULT:**

All eight `os.environ.get()` calls in `generate_pretty.py` already have documented entries in `.env.example`:

| Variable | Line in generate_pretty.py | In .env.example |
|----------|---------------------------|-----------------|
| `INFG_VERTEX_PROJECT` | 115 | Yes (line 16) |
| `INFG_VERTEX_LOCATION` | 116 | Yes (line 17) |
| `INFG_LLM_PROVIDER` | 120 | Yes (line 22) |
| `INFG_LLM_MODEL` | 121 | Yes (line 26) |
| `INFG_LLM_API_KEY` | 122 | Yes (line 29) |
| `INFG_OPENROUTER_API_KEY` | 123 | Yes (line 32-33) |
| `INFG_IMAGE_MODEL` | 124 | Yes (line 37) |
| `INFG_API_KEY` | 165 | Yes (line 11) |

**DEPLOY-02 verdict:** `.env.example` is already complete. The only potential task is adding a `MPLBACKEND` entry for CI/headless environments (currently in a comment on line 41-42 but not as an uncommented entry). This is not required by DEPLOY-02 success criteria but is good practice for OSS users.

### Pattern 4: Documentation Update (for DEPLOY-03)

**Locations to update:**

1. **SKILL.md frontmatter** (line 15): `python: ">=3.8"` → `python: ">=3.9"`
2. **SKILL.md pip deps** (lines 16-21): Remove `google-genai` and `playwright` from required deps (they are optional); or add them as optional with comment. The offline path requires only `matplotlib>=3.7`, `Pillow>=10.0`, `numpy>=1.24`, `requests>=2.28`.
3. **README.md prerequisites** (line 15): `Python 3.8+` → `Python 3.9+`
4. **Both files**: Add OpenRouter setup section under the existing "Pretty mode" section.

**OpenRouter section content (to add to both docs):**

```markdown
### Optional setup: OpenRouter

Use OpenRouter to route text generation through any model (Claude, GPT-4o, Llama, etc.).

1. Get an API key at https://openrouter.ai/keys
2. Set in `.env`:

```text
INFG_LLM_PROVIDER=openrouter
INFG_LLM_MODEL=anthropic/claude-opus-4
INFG_OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

3. Run:

```bash
python3 scripts/generate_pretty.py \
  --text "Your data here" \
  --output pretty.html
```

Note: OpenRouter only supports the HTML-output path. Image generation always uses Gemini.
```

**Python version rationale (for commit message / PR description):**

`generate_pretty.py` uses `dict[str, tuple[...]]` as a runtime annotation (line 248) which requires Python 3.9+ (PEP 585). It also uses `X | Y` union syntax (lines 701, 806, 834, 851) which requires Python 3.10+. The stated OSS minimum is 3.9+ per ROADMAP success criteria. The `str | None` annotations would fail on Python 3.9 at runtime in some contexts — but since these are function signatures used only within the module (not exported as an API), and the codebase uses Python 3.12 in development, targeting 3.9+ is the stated minimum. Flag this asymmetry in docs with a note if needed, but do not change it — the ROADMAP specifies 3.9+.

### Anti-Patterns to Avoid

- **Two separate redact functions:** Keep a single `_redact_key()` function. Do not add `_redact_openrouter_key()` separately — that creates drift risk.
- **Replacing module-level _KEY_PATTERN entirely:** The existing pattern variable can be removed or kept; if kept, it must match both Google and OpenRouter patterns. Cleaner to use two inline `re.sub` calls inside `_redact_key()`.
- **Hard-coding redacted suffix in multiple places:** The `sk-or-v1-[REDACTED]` format should only appear inside `_redact_key()`, not scattered across error message strings.
- **Requiring DEPLOY-04 to add openai as a real dependency:** The guard is purely defensive/preventive. Do not add `openai` to `requirements.txt` or `SKILL.md` pip deps.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Key redaction | Custom string scanner | `re.sub()` with anchored prefix patterns | Regex handles all string contexts including tracebacks |
| Multiple optional dep guards | Custom import machinery | `try/except ImportError` + `_FLAG` boolean | Already established pattern in codebase; zero overhead |
| Env var documentation | Auto-generation script | Manual audit + hand-written .env.example | Only 8 vars, all already documented |
| Python version detection | Runtime check | Docs-only fix | Users select interpreter; no runtime enforcement needed |

## Common Pitfalls

### Pitfall 1: Redaction Pattern Too Narrow
**What goes wrong:** OpenRouter key regex matches only known key lengths (e.g., exactly 64 chars) — future key format changes or test keys with different lengths bypass redaction.
**Why it happens:** Treating "typical" key length as "guaranteed" key length.
**How to avoid:** Use `{30,}` (at least 30 chars) rather than exact count. The current Google pattern uses `{30,}` — match this convention for OpenRouter.
**Warning signs:** Test fails when using a short synthetic key like `sk-or-v1-testkey123456789012345`.

### Pitfall 2: Redaction Applied to `or_api_key` Variable But Not Error Bodies
**What goes wrong:** Error messages at lines 774-781 print `resp.text[:200]` which could contain the API key if the server echoes it back in a 4xx error.
**Why it happens:** `resp.text` is unfiltered server response text.
**How to avoid:** Wrap `resp.text[:200]` in `_redact_key()` in the generic error path at line 780.
**Warning signs:** A mock that returns `resp.text = "key=sk-or-v1-abc..."` leaks in test output.

### Pitfall 3: SKILL.md Dependencies Section Confusion
**What goes wrong:** SKILL.md YAML frontmatter `dependencies.pip` is consumed by Claude Code's skill installation. Listing `google-genai` as required causes Claude to try to install it for every skill use, even offline-only operations.
**Why it happens:** Original authorship listed all known deps without distinguishing optional.
**How to avoid:** Remove `google-genai` and `playwright` from required pip list; document them as optional in the markdown body (already done).
**Warning signs:** Claude Code install instructions prompt for `google-genai` on machines that only want offline mode.

### Pitfall 4: `str | None` Syntax Breaking Python 3.9
**What goes wrong:** `generate_pretty.py` uses `Path | None` in function signatures (lines 806, 834, 851). On Python 3.9, `X | Y` union syntax in annotations raises `TypeError` at function definition time (not import time, but at function call time if annotations are evaluated).
**Why it happens:** `X | Y` for types is Python 3.10+ (PEP 604). Python 3.9 only added `dict[...]` and `list[...]` (PEP 585).
**How to avoid:** Either add `from __future__ import annotations` at the top of `generate_pretty.py` (makes all annotations strings, deferred evaluation — works on Python 3.9), or change `Path | None` to `Optional[Path]` from `typing`. Since ROADMAP says 3.9+, adding `from __future__ import annotations` is the minimal fix.
**Warning signs:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` on Python 3.9.

**Decision for plan:** The ROADMAP specifies 3.9+. Add `from __future__ import annotations` if fixing the Python version claim — this is a single-line fix that makes the codebase actually compatible with 3.9+. If 3.10+ is the real minimum, the docs should say 3.10+. The planner should add `from __future__ import annotations` to `generate_pretty.py` as part of DEPLOY-03 to make the 3.9+ claim accurate.

### Pitfall 5: DEPLOY-04 Test Not Actually Blocking openai
**What goes wrong:** Test uses `unittest.mock.patch` to hide openai but the module was already loaded and cached — `_OPENAI_OK` is already `True` from the previous import.
**Why it happens:** Python module caching means the `try/except` block only runs once per process.
**How to avoid:** Use `subprocess.run` for the DEPLOY-04 test (same pattern as `TestModelValidation` in `tests/test_openrouter.py`), or use `importlib.reload()` after manipulating `sys.modules`.
**Warning signs:** Test passes even when the guard isn't present.

## Code Examples

### Example 1: Extended _redact_key() with asymmetric output

```python
# Source: Pattern derived from existing _redact_key() + OpenRouter key format
def _redact_key(text: str) -> str:
    """Replace embedded API key values with [REDACTED] before printing."""
    # Google AI Studio keys (AIza prefix)
    text = re.sub(r"AIza[a-zA-Z0-9_-]{30,}", "[REDACTED]", text)
    # OpenRouter keys (retain prefix so users know which key type was redacted)
    text = re.sub(r"sk-or-v1-[a-zA-Z0-9_-]{30,}", "sk-or-v1-[REDACTED]", text)
    return text
```

### Example 2: OpenAI SDK lazy import guard

```python
# Source: Modeled after _GENAI_OK and _REQUESTS_OK patterns in generate_pretty.py
# openai SDK — optional, deferred to v1.x; guard prevents ImportError on offline path
try:
    import openai as _openai_lib   # pip install openai
    _OPENAI_OK = True
except ImportError:
    _openai_lib = None
    _OPENAI_OK = False
```

### Example 3: Test for DEPLOY-01 key redaction

```python
# Source: Modeled after test_openrouter.py patterns
from scripts.generate_pretty import _redact_key

def test_openrouter_key_redacted():
    text = "Error: sk-or-v1-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
    result = _redact_key(text)
    assert "sk-or-v1-[REDACTED]" in result
    assert "sk-or-v1-abc123" not in result

def test_google_key_still_redacted():
    text = "key=AIzaSyD_example_key_1234567890abcdefghij"
    result = _redact_key(text)
    assert "[REDACTED]" in result
    assert "AIzaSyD_example_key" not in result
```

### Example 4: Test for DEPLOY-04 (subprocess pattern)

```python
# Source: Modeled after TestModelValidation subprocess pattern in test_openrouter.py
import subprocess, sys

def test_offline_path_works_without_openai():
    """DEPLOY-04: generate.py runs without openai installed."""
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.modules['openai'] = None; "
         "import importlib.util; "
         "spec = importlib.util.spec_from_file_location('generate', 'scripts/generate.py'); "
         "mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)"],
        capture_output=True, text=True, timeout=15,
        cwd="/path/to/infographic-skill"
    )
    assert result.returncode == 0
    assert "ImportError" not in result.stderr
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single regex pattern `_KEY_PATTERN` | Two-call `re.sub` in `_redact_key()` | This phase | Handles asymmetric redaction output formats |
| Python 3.8+ claim | Python 3.9+ claim (with `from __future__ import annotations`) | This phase | Accurate min version; `dict[...]` generics work |
| No OpenRouter docs | OpenRouter setup section in SKILL.md + README.md | This phase | OSS users can discover and configure OpenRouter path |

## Open Questions

1. **`str | None` union syntax: 3.9+ vs 3.10+ minimum**
   - What we know: `generate_pretty.py` uses `X | Y` union annotation syntax at function signatures (lines 701, 806, 834, 851); this syntax requires Python 3.10+ to work without `from __future__ import annotations`
   - What's unclear: Whether the ROADMAP's "3.9+" is intentional or a typo for "3.10+"
   - Recommendation: Add `from __future__ import annotations` to `generate_pretty.py` to make 3.9+ claim accurate. This is a one-line fix with zero behavioral impact (deferred annotation evaluation). Do NOT change the stated minimum to 3.10+ — the ROADMAP is authoritative.

2. **MPLBACKEND in .env.example**
   - What we know: `.env.example` has `MPLBACKEND=Agg` as a comment (line 41-42) but not as an active entry
   - What's unclear: Whether DEPLOY-02 requires it to be an uncommented entry
   - Recommendation: The success criteria says "every env var consumed by `os.environ.get()`" — `MPLBACKEND` is consumed by matplotlib internally, not by a project `os.environ.get()` call. It does not need an entry per DEPLOY-02's strict definition. Leave as comment.

## Environment Availability

Step 2.6: Audited — no external dependencies beyond current Python environment.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All scripts | Yes | 3.12.3 | — |
| pytest | Test execution | Yes | 9.0.2 | — |
| matplotlib | generate.py offline path test | Yes | 3.10.8 | — |
| openai package | DEPLOY-04 simulation | Yes (2.24.0) | 2.24.0 | Block via sys.modules in subprocess |

**No missing dependencies.** The openai package is currently installed (2.24.0) — the DEPLOY-04 test should use subprocess with `sys.modules['openai'] = None` simulation rather than actually uninstalling openai.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none (no pytest.ini/pyproject.toml) |
| Quick run command | `python3 -m pytest tests/ -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-01 | OpenRouter key `sk-or-v1-xxx` is redacted to `sk-or-v1-[REDACTED]` in `_redact_key()` | unit | `python3 -m pytest tests/test_deploy.py::TestKeyRedaction -x` | No — Wave 0 |
| DEPLOY-01 | Google key (`AIza...`) still redacted after _redact_key() update | unit | `python3 -m pytest tests/test_deploy.py::TestKeyRedaction::test_google_key_still_redacted -x` | No — Wave 0 |
| DEPLOY-02 | All os.environ.get() vars have .env.example entries | smoke/audit | `python3 -m pytest tests/test_deploy.py::TestEnvVarAudit -x` | No — Wave 0 |
| DEPLOY-03 | SKILL.md python version is >= 3.9 | smoke | `python3 -m pytest tests/test_deploy.py::TestDocsAccuracy -x` | No — Wave 0 |
| DEPLOY-03 | README.md mentions Python 3.9+ | smoke | `python3 -m pytest tests/test_deploy.py::TestDocsAccuracy::test_readme_python_version -x` | No — Wave 0 |
| DEPLOY-03 | SKILL.md has OpenRouter section | smoke | `python3 -m pytest tests/test_deploy.py::TestDocsAccuracy::test_skill_openrouter_section -x` | No — Wave 0 |
| DEPLOY-03 | README.md has OpenRouter section | smoke | `python3 -m pytest tests/test_deploy.py::TestDocsAccuracy::test_readme_openrouter_section -x` | No — Wave 0 |
| DEPLOY-04 | generate.py loads cleanly when openai blocked | unit | `python3 -m pytest tests/test_deploy.py::TestOfflinePath -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/ -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_deploy.py` — covers DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04
- [ ] No `conftest.py` needed — existing test structure uses no fixtures

## Sources

### Primary (HIGH confidence)

- Direct code audit — `scripts/generate_pretty.py` (lines 58-63, 115-165, 136-149, 701-851)
- Direct code audit — `scripts/generate.py` (imports section, lines 13-22)
- Direct file audit — `.env.example` (all 8 env vars verified present)
- Direct file audit — `SKILL.md` (frontmatter python version, dependencies)
- Direct file audit — `README.md` (Prerequisites section, Pretty mode section)
- `tests/test_openrouter.py` — existing test patterns (subprocess, mock.patch)

### Secondary (MEDIUM confidence)

- Python 3.9 PEP 585 (`dict[str, ...]` built-in generics): https://peps.python.org/pep-0585/
- Python 3.10 PEP 604 (`X | Y` union syntax): https://peps.python.org/pep-0604/
- `from __future__ import annotations` PEP 563: https://peps.python.org/pep-0563/

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new dependencies; all patterns confirmed in codebase
- Architecture: HIGH — all four tasks have direct analogues in existing code
- Pitfalls: HIGH — `str | None` syntax issue verified by PEP dates; redaction format verified from success criteria
- Validation: HIGH — existing test infrastructure confirmed; pytest 9.0.2 present

**Research date:** 2026-03-23
**Valid until:** 2026-06-23 (stable domain — Python stdlib patterns, no fast-moving dependencies)
