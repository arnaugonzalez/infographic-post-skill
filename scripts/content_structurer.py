"""Content structurer — LLM produces structured JSON for infographic templates.

Instead of asking the LLM to generate HTML (unreliable, model-dependent),
we ask it to return structured JSON with layer assignments and tech descriptions.
The template engine handles all visual design.
"""
from __future__ import annotations

import json
import re
import sys
import os
from pathlib import Path

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
- "subtitle" should be "Technical Architecture Overview" or similar
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


def structure_codebase(
    codebase_report: dict,
    model: str | None = None,
    api_key: str | None = None,
    max_retries: int = 2,
) -> dict:
    """Convert a codebase report into structured infographic data.
    
    Parameters
    ----------
    codebase_report : dict from read_codebase()
    model : OpenRouter model identifier (default: from INFG_LLM_MODEL env)
    api_key : OpenRouter API key (default: from INFG_OPENROUTER_API_KEY env)
    max_retries : number of retries on JSON parse failure
    
    Returns a dict ready for template_renderer.render_infographic()
    """
    _load_dotenv(_ENV_PATH)
    
    if not model:
        model = os.environ.get("INFG_LLM_MODEL", "google/gemini-2.0-flash-001").strip()
    if not api_key:
        api_key = os.environ.get("INFG_OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("❌ Set INFG_OPENROUTER_API_KEY in .env or pass api_key parameter")
        sys.exit(1)
    
    # Quality warning
    try:
        from model_quality import classify_model_quality, quality_warning
        tier = classify_model_quality(model)
        quality_warning(model, tier, context="infographic")
    except ImportError:
        pass
    
    # Build prompt
    summary = codebase_report.get("summary_text", json.dumps(codebase_report, indent=2))
    prompt = _STRUCTURER_PROMPT.format(codebase_report=summary)
    
    # Call LLM with retry
    for attempt in range(max_retries + 1):
        print(f"🤖 Structuring codebase data via {model}...")
        raw = _call_openrouter(prompt, model, api_key)
        cleaned = _strip_json_fences(raw)
        try:
            data = json.loads(cleaned)
            # Validate required keys
            if "layers" not in data or not isinstance(data["layers"], list):
                raise ValueError("Missing or invalid 'layers' key")
            if "title" not in data:
                raise ValueError("Missing 'title' key")
            # Set defaults
            data.setdefault("subtitle", "Technical Architecture Overview")
            data.setdefault("connections", [])
            data.setdefault("footer_cta", "Follow for more software architecture content")
            data.setdefault("footer_summary", "")
            print(f"✅ Structured: {len(data['layers'])} layers, {sum(len(l.get('items',[])) for l in data['layers'])} items")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries:
                print(f"⚠️ JSON parse failed (attempt {attempt+1}): {e} — retrying...")
            else:
                print(f"❌ Failed to parse LLM response after {max_retries+1} attempts: {e}")
                print(f"   Raw response: {raw[:300]}...")
                sys.exit(1)
