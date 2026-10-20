"""Content structurer — LLM produces structured JSON for infographic templates.

Instead of asking the LLM to generate HTML (unreliable, model-dependent),
we ask it to return structured JSON with layer assignments and tech descriptions.
The template engine handles all visual design.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backends  # noqa: E402

_SKILL_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _SKILL_DIR / ".env"

# Layer color palette (assigned in order)
LAYER_PALETTE = [
    "#3B82F6", "#F59E0B", "#10B981", "#8B5CF6",
    "#06B6D4", "#EF4444", "#EC4899", "#F97316",
]

# The prompt template for structured JSON output
_STRUCTURER_PROMPT = """You are a senior software architect creating an architecture infographic.

Given the codebase analysis below, produce a JSON structure for an architecture diagram.

RULES:
- Group technologies into 4-6 logical layers (e.g., Frontend, Backend, Database, AI/ML, Auth, Infrastructure)
- Each layer has: "label" (uppercase short name), "items" array
- Each item has: "name" (exact technology name as commonly known), "description" (≤8 words, specific to this project)
- Add "connections" array showing data flow between layers
- Each connection has: "from_layer" (index), "to_layer" (index), "label" (short flow description)
- "title" should be derived from the project name, not generic
- "subtitle" is one short factual sentence specific to THIS project, or "" — never a generic
  phrase like "Technical Architecture Overview"
- "footer_summary" should be a one-line description of the project (≤80 chars)

IMPORTANT:
- Use REAL technology names that match common naming (e.g., "React Native" not "react-native", "PostgreSQL" not "postgres")
- Keep descriptions factual and specific to THIS project, not generic
- Maximum 5 items per layer
- Output ONLY valid JSON. No markdown fences, no explanation, no commentary.

CODEBASE ANALYSIS:
{codebase_report}

OUTPUT FORMAT (JSON only):
{{
  "title": "Project Name",
  "subtitle": "Technical Architecture Overview",
  "layers": [
    {{
      "label": "FRONTEND",
      "items": [
        {{"name": "React Native", "description": "Cross-platform mobile SDK"}},
        {{"name": "Expo", "description": "Build & deploy pipeline"}}
      ]
    }}
  ],
  "connections": [
    {{"from_layer": 0, "to_layer": 1, "label": "REST API"}},
    {{"from_layer": 1, "to_layer": 2, "label": "SQL queries"}}
  ],
  "footer_cta": "Follow for more software architecture content",
  "footer_summary": "One-line project description here"
}}"""


def _load_dotenv(path: Path) -> None:
    """Load .env file into os.environ (setdefault, no overwrite)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _strip_json_fences(raw: str) -> str:
    """Strip markdown code fences and any preamble before JSON."""
    raw = raw.strip()
    # Find the first { which starts the JSON
    idx = raw.find("{")
    if idx > 0:
        raw = raw[idx:]
    # Find the last } which ends the JSON
    ridx = raw.rfind("}")
    if ridx >= 0:
        raw = raw[:ridx + 1]
    return raw


def _call_openrouter(prompt: str, model: str, api_key: str) -> str:
    """Call OpenRouter API and return the response text."""
    import requests
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,  # Low temperature for structured output
        },
        timeout=120,
    )
    if resp.status_code != 200:
        print(f"❌ OpenRouter API error ({resp.status_code}): {resp.text[:200]}")
        sys.exit(1)
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_anthropic(prompt: str, model: str, api_key: str) -> str:
    """Call the Claude Messages API (low effort: extraction, not reasoning)."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=16000,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
    )
    if msg.stop_reason == "refusal":
        print(f"❌ {model} declined the request: {msg.stop_details}")
        sys.exit(1)
    return "".join(b.text for b in msg.content if b.type == "text")


def _call_gemini(prompt: str, model: str, api_key: str) -> str:
    """Call Gemini via AI Studio with JSON output mode."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return resp.text or ""


# Defaults chosen by the Oct 2026 benchmark (benchmark/RESULTS.md): on the project
# digest both extract every sub-project for ≤ $0.012 per call.
DEFAULT_MODELS = {"anthropic": "claude-haiku-5-5", "gemini": "gemini-3.8-flash"}

_CALLERS = {"openrouter": "_call_openrouter", "anthropic": "_call_anthropic", "gemini": "_call_gemini"}
_SLASH_PROVIDER = next(iter(_CALLERS))


def resolve_provider(model: str | None = None) -> tuple[str, str, str]:
    """Return (provider, model, api_key) from the model name and available keys.

    ``claude-*`` → Anthropic, ``gemini-*`` → Gemini (AI Studio), ``vendor/model`` →
    slash-prefixed provider (forbidden for ``gemini*``/``google/*``). With no model:
    ``INFG_LLM_MODEL``, else the first provider with a key (Anthropic, Gemini);
    raises ``SystemExit`` when neither is configured.
    """
    _load_dotenv(_ENV_PATH)
    keys = {
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        "gemini": os.environ.get("INFG_API_KEY", "").strip(),
        _SLASH_PROVIDER: (os.environ.get("INFG_OPENROUTER_API_KEY", "")
                          or os.environ.get("INFG_LLM_API_KEY", "")).strip(),
    }
    model = (model or os.environ.get("INFG_LLM_MODEL", "")).strip()
    if not model:
        for provider in ("anthropic", "gemini"):
            if keys[provider]:
                return provider, DEFAULT_MODELS[provider], keys[provider]
        raise SystemExit(backends.NO_BACKEND_MESSAGE)
    if "/" in model:
        if model.lower().startswith("google/") or "gemini" in model.lower():
            raise SystemExit("Gemini/Google models must use AI Studio (INFG_API_KEY) or a CLI backend.")
        provider = _SLASH_PROVIDER
    elif model.startswith("claude"):
        provider = "anthropic"
    else:
        provider = "gemini"
    return provider, model, keys[provider]


def _validate_and_default(data: dict) -> dict:
    if "layers" not in data or not isinstance(data["layers"], list):
        raise ValueError("Missing or invalid 'layers' key")
    if "title" not in data:
        raise ValueError("Missing 'title' key")
    data.setdefault("subtitle", "Technical Architecture Overview")
    data.setdefault("connections", [])
    data.setdefault("footer_cta", "Follow for more software architecture content")
    data.setdefault("footer_summary", "")
    return data


def _session_spec_from_report(codebase_report: dict) -> dict:
    """Build a structured spec locally for --backend session without paid API calls."""
    if "layers" in codebase_report and isinstance(codebase_report["layers"], list):
        spec = dict(codebase_report)
        spec.setdefault("title", codebase_report.get("title") or "System Architecture")
        return _validate_and_default(spec)
    langs = codebase_report.get("languages") or {}
    manifests = codebase_report.get("manifests") or []
    items = [{"name": str(k), "description": f"{v} source files"} for k, v in list(langs.items())[:5]]
    if not items and manifests:
        items = [{"name": Path(m).name, "description": m} for m in manifests[:5]]
    if not items:
        items = [{"name": "Application", "description": "Core project module"}]
    return _validate_and_default({
        "title": codebase_report.get("title") or "System Architecture",
        "subtitle": "Technical Architecture Overview",
        "layers": [{"label": "CORE", "items": items}],
        "connections": [],
        "summary_text": codebase_report.get("summary_text", ""),
    })


def structure_codebase(
    codebase_report: dict,
    model: str | None = None,
    api_key: str | None = None,
    max_retries: int = 2,
    backend: str | None = None,
    focus: str = "",
) -> dict:
    """Convert a codebase report (or project digest) into structured infographic data.

    Parameters
    ----------
    codebase_report : dict from project_digest.build_digest() or read_codebase()
    model : model identifier (default: resolved from backend or environment)
    api_key : key for direct API mode (default: from .env)
    max_retries : number of retries on JSON parse failure
    backend : ``auto|session|claude|agy|codex|copilot|opencode|api``
    focus : what the author wants the graphic to be about (``--learnings``); it outranks what the
        code alone suggests, e.g. when old code paths are still in the repository

    Returns a dict ready for template_renderer.render_infographic()
    """
    summary = codebase_report.get("summary_text", json.dumps(codebase_report, indent=2))
    if focus:
        summary = (f"AUTHOR'S FOCUS — describes the current version; when it conflicts with the code "
                   f"analysis below, follow the focus:\n{focus}\n\n{summary}")
    prompt = _STRUCTURER_PROMPT.format(codebase_report=summary)

    use_api_directly = (
        api_key is not None
        or backend == "api"
        or (backend is None and bool(model and "/" in model))
    )

    if not use_api_directly and backend is not None:
        resolved_backend, resolved_model = backends.resolve(backend, model)
        if resolved_backend == "session":
            return _session_spec_from_report(codebase_report)
        if resolved_backend != "api":
            for attempt in range(max_retries + 1):
                print(f"🤖 Structuring codebase data via {resolved_backend} ({resolved_model or 'default'})...")
                raw = backends.run(resolved_backend, resolved_model, prompt)
                cleaned = _strip_json_fences(raw)
                try:
                    data = _validate_and_default(json.loads(cleaned))
                    print(f"✅ Structured: {len(data['layers'])} layers, "
                          f"{sum(len(l.get('items', [])) for l in data['layers'])} items")
                    return data
                except (json.JSONDecodeError, ValueError) as e:
                    if attempt < max_retries:
                        print(f"⚠️ JSON parse failed (attempt {attempt+1}): {e} — retrying...")
                    else:
                        print(f"❌ Failed to parse LLM response after {max_retries+1} attempts: {e}")
                        sys.exit(1)
        model = resolved_model

    provider, model, env_key = resolve_provider(model)
    api_key = api_key or env_key
    if not api_key:
        env_name = {"anthropic": "ANTHROPIC_API_KEY", "gemini": "INFG_API_KEY",
                    _SLASH_PROVIDER: "INFG_OPENROUTER_API_KEY"}[provider]
        print(f"❌ Set {env_name} in .env (model {model!r} uses {provider})")
        sys.exit(1)
    call = globals()[_CALLERS[provider]]

    # Quality warning
    try:
        from model_quality import classify_model_quality, quality_warning
        tier = classify_model_quality(model)
        quality_warning(model, tier, context="infographic")
    except ImportError:
        pass

    # Call LLM with retry
    for attempt in range(max_retries + 1):
        print(f"🤖 Structuring codebase data via {model}...")
        raw = call(prompt, model, api_key)
        cleaned = _strip_json_fences(raw)
        try:
            data = _validate_and_default(json.loads(cleaned))
            print(f"✅ Structured: {len(data['layers'])} layers, {sum(len(l.get('items',[])) for l in data['layers'])} items")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries:
                print(f"⚠️ JSON parse failed (attempt {attempt+1}): {e} — retrying...")
            else:
                print(f"❌ Failed to parse LLM response after {max_retries+1} attempts: {e}")
                print(f"   Raw response: {raw[:300]}...")
                sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Structure a codebase digest into infographic JSON")
    ap.add_argument("codebase", nargs="?", default=".", help="Path to codebase directory")
    ap.add_argument("--backend", default=None, help="Backend: auto|session|claude|agy|codex|copilot|opencode|api")
    ap.add_argument("--model", default=None, help="Model override")
    ap.add_argument("--output", default="", help="Write JSON output to file instead of stdout")
    args = ap.parse_args()
    from project_digest import build_digest
    digest = build_digest(args.codebase)
    backend, model = backends.resolve(args.backend, args.model)
    data = structure_codebase(digest, model=model, backend=backend)
    out_text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out_text, encoding="utf-8")
    else:
        print(out_text)


if __name__ == "__main__":
    main()
