#!/usr/bin/env python3
"""
Infographic Skill — Gemini "Pretty" Mode Generator

Uses Google Gemini (google-genai SDK) to produce visually stunning
LinkedIn-ready infographics.

Default model: gemini-3.1-flash-image-preview
  → For *-image models: generates a PNG directly via IMAGE modality
  → For text models:    generates self-contained HTML → PNG via Playwright
  → Always prints a cost breakdown after every generation.

Backend routing (automatic):
  • AI-Studio-only models (e.g. gemini-3.1-flash-image-preview) → AI Studio (INFG_API_KEY)
  • Stable models (e.g. gemini-2.5-flash-image, gemini-2.5-pro)  → Vertex AI (INFG_VERTEX_PROJECT)
  • If only one backend is configured, all models route there.

Usage:
    # From a pre-built arch.json:
    python scripts/generate_pretty.py --config arch.json --output pretty.png

    # Quick inline architecture:
    python scripts/generate_pretty.py \\
        --layers "Frontend:React,Next.js|Backend:FastAPI,Celery|Database:PostgreSQL,Redis" \\
        --title "My SaaS Architecture" --author "Your Name" --output pretty.png

    # Dashboard / KPI infographic:
    python scripts/generate_pretty.py \\
        --text "Revenue $2.4M (+18%), NPS 72, Churn 2.1%, New customers 340" \\
        --type dashboard --title "Q3 Performance" --output pretty.png

    # Use a different model:
    python scripts/generate_pretty.py --config arch.json --model gemini-2.5-pro --output pretty.html

Available models (Feb 2026):
    gemini-3.1-flash-image-preview ← default  (AI Studio, native PNG)
    gemini-2.5-flash-image                     (Vertex AI, native PNG, stable fallback)
    gemini-2.5-pro                             (Vertex AI, HTML output, best quality)
    gemini-2.0-flash                           (Vertex AI, HTML output, fast/cheap)
    gemini-2.0-flash-lite                      (Vertex AI, HTML output, cheapest)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# ── Locate skill root & load .env ────────────────────────────────────────────

_SKILL_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH  = _SKILL_DIR / ".env"

# ── Security helper ───────────────────────────────────────────────────────────


def _redact_key(text: str) -> str:
    """Replace embedded API key values with [REDACTED] before printing."""
    # Google AI Studio keys (AIza prefix) — full redaction
    text = re.sub(r"AIza[a-zA-Z0-9_-]{30,}", "[REDACTED]", text)
    # OpenRouter keys (sk-or-v1- prefix) — retain prefix so users know which key leaked
    text = re.sub(r"sk-or-v1-[a-zA-Z0-9_-]{30,}", "sk-or-v1-[REDACTED]", text)
    return text


def _handle_credential_error(exc: Exception) -> None:
    """
    If `exc` is an auth/credential error, print a user-friendly message and exit.
    Non-auth errors are ignored so the caller can re-raise them normally.
    """
    exc_type = type(exc).__name__
    exc_module = type(exc).__module__ or ""
    credential_signals = (
        "DefaultCredentialsError",
        "PermissionDenied",
        "Unauthenticated",
        "UNAUTHENTICATED",
    )
    is_auth_error = (
        any(sig in exc_type for sig in credential_signals)
        or any(sig in str(exc) for sig in ("UNAUTHENTICATED", "credentials", "Permission denied"))
        or "google.auth" in exc_module
    )
    if is_auth_error:
        safe_msg = _redact_key(str(exc))
        print(
            f"❌  Credentials error: {safe_msg}\n"
            "\n"
            "   To fix:\n"
            "     Run: cp .env.example .env  then add your API key or project ID\n"
            "     Docs: see README.md for full setup instructions\n"
            "\n"
            "   Option A — AI Studio key:   set INFG_API_KEY in .env\n"
            "   Option B — Vertex AI:       set INFG_VERTEX_PROJECT and run\n"
            "                               gcloud auth application-default login"
        )
        sys.exit(1)


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv(_ENV_PATH)

# ── Backend detection ────────────────────────────────────────────────────────

_VERTEX_PROJECT  = os.environ.get("INFG_VERTEX_PROJECT",  "").strip()
_VERTEX_LOCATION = os.environ.get("INFG_VERTEX_LOCATION", "us-central1").strip()
_USE_VERTEX      = bool(_VERTEX_PROJECT)

# -- LLM provider configuration -----------------------------------------------
_LLM_PROVIDER       = os.environ.get("INFG_LLM_PROVIDER",      "").strip().lower()
_LLM_MODEL          = os.environ.get("INFG_LLM_MODEL",         "").strip()
_LLM_API_KEY        = os.environ.get("INFG_LLM_API_KEY",       "").strip()
_OPENROUTER_API_KEY = os.environ.get("INFG_OPENROUTER_API_KEY", "").strip()
_IMAGE_MODEL_ENV    = os.environ.get("INFG_IMAGE_MODEL",       "").strip()

# Models only available on AI Studio (404 on Vertex AI as of Feb 2026).
# These are automatically routed to AI Studio when INFG_API_KEY is set.
_AI_STUDIO_ONLY = frozenset({
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview",
})

# ── Gemini SDK ────────────────────────────────────────────────────────────────

try:
    from google import genai                      # pip install google-genai
    from google.genai import types as genai_types
    _GENAI_OK = True
except ImportError:
    _GENAI_OK = False

# ── HTTP client for OpenRouter ────────────────────────────────────────────────
try:
    import requests as _requests_lib   # pip install requests
    _REQUESTS_OK = True
except ImportError:
    _requests_lib = None
    _REQUESTS_OK = False

# ── openai SDK — optional, deferred to v1.x ────────────────────────────────
try:
    import openai as _openai_lib   # pip install openai
    _OPENAI_OK = True
except ImportError:
    _openai_lib = None
    _OPENAI_OK = False

# ── Vertex AI helpers ─────────────────────────────────────────────────────────


def _build_genai_client(model_name: str = "") -> tuple:
    """
    Build a google-genai Client and return (client, backend_label).

    Routing logic — cheapest available option:
      1. AI-Studio-only models (in _AI_STUDIO_ONLY) → AI Studio  (INFG_API_KEY)
      2. All other models                            → Vertex AI  (INFG_VERTEX_PROJECT + ADC)
      3. Last resort fallback                        → AI Studio  (INFG_API_KEY)

    If neither backend is configured the process exits with a helpful message.
    """
    api_key = os.environ.get("INFG_API_KEY", "").strip()

    # Route AI-Studio-only models to AI Studio when a key is available
    if model_name in _AI_STUDIO_ONLY and api_key:
        return genai.Client(api_key=api_key), "aistudio"

    # Prefer Vertex AI for stable models (uses ADC — no key file required)
    if _USE_VERTEX:
        return genai.Client(
            vertexai=True,
            project=_VERTEX_PROJECT,
            location=_VERTEX_LOCATION,
        ), "vertex"

    # Fallback: AI Studio with API key
    if api_key:
        return genai.Client(api_key=api_key), "aistudio"

    print(
        "❌  No credentials configured for pretty mode.\n"
        "\n"
        "   Recommended path — Google AI Studio for the default max-quality image model:\n"
        "     1. Get an API key at: https://aistudio.google.com/apikey\n"
        "     2. cp .env.example .env\n"
        "     3. Set INFG_API_KEY=<your-key> in .env\n"
        "\n"
        "   Optional path — Vertex AI:\n"
        "     1. Enable Vertex AI and run: gcloud auth application-default login\n"
        "     2. Set INFG_VERTEX_PROJECT=<your-project-id> in .env\n"
        "\n"
        "   See README.md for the supported setup paths."
    )
    sys.exit(1)


def _vertex_policy_warning() -> None:
    """
    Quick inline check: warns if Vertex AI credentials appear invalid.
    Does not block execution.
    """
    try:
        import google.auth
        import google.auth.transport.requests

        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(google.auth.transport.requests.Request())
        # Credentials OK — silent so we don't clutter output
    except ImportError:
        print("⚠️  google-auth not installed → pip install google-auth")
        print("   Vertex AI policy check skipped.")
        print()
    except Exception as e:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("⚠️  WARNING: Vertex AI credentials appear invalid")
        print(f"   Error: {e}")
        print()
        print("   Try one of these:")
        print("     gcloud auth application-default login")
        print("     unset INFG_VERTEX_PROJECT to fall back to AI Studio")
        print("   See README.md for supported setup instructions.")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

# ── Reuse layer-string parser ─────────────────────────────────────────────────

sys.path.insert(0, str(_SKILL_DIR / "scripts"))
try:
    from generate_linkedin_arch import layers_from_string  # type: ignore
except ImportError:
    def layers_from_string(s: str) -> list:
        layers = []
        for part in s.split("|"):
            if ":" in part:
                label, items_str = part.split(":", 1)
                items = [i.strip() for i in items_str.split(",") if i.strip()]
                layers.append({"label": label.strip(), "items": items, "category": "other"})
        return layers

# ── Pricing table (USD, verified Feb 2026 — always re-check ai.google.dev/pricing) ──

# (input_per_1M_tokens, output_per_1M_tokens, output_per_image)
_PRICING: dict[str, tuple[float, float, float]] = {
    "gemini-3.1-flash-image-preview": (0.075, 0.30, 0.039),  # newest image gen model
    "gemini-2.5-flash-image":    (0.075,  0.30,  0.039),   # stable image gen model
    "gemini-2.5-flash":          (0.075,  0.30,  0.0),
    "gemini-2.5-flash-lite":     (0.02,   0.08,  0.0),
    "gemini-2.5-pro":            (1.25,   10.0,  0.0),
    "gemini-3-pro-preview":      (1.25,   5.0,   0.0),
    "gemini-3.1-pro-preview":    (1.25,   5.0,   0.0),
    "gemini-2.0-flash":          (0.10,   0.40,  0.0),
    "gemini-2.0-flash-lite":     (0.025,  0.10,  0.0),
}
_DEFAULT_PRICING = (1.0, 4.0, 0.0)   # conservative fallback for unknown models


# ── Model version helpers ─────────────────────────────────────────────────────

def _gemini_version(model: str) -> tuple[int, int]:
    """Extract (major, minor) version tuple from a Gemini model name."""
    name = model.replace("models/", "").lower()
    m = re.search(r"gemini-(\d+)(?:\.(\d+))?", name)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2) or 0))


def _model_family(model: str) -> str:
    """Return the model family string: 'gemini', 'dalle', 'sd', or first token of unknown models."""
    name = model.lower().replace("models/", "")
    if name.startswith("gemini"):
        return "gemini"
    if name.startswith("dall") or name.startswith("dall-e"):
        return "dalle"
    if name.startswith("stable-diffusion") or name.startswith("sd-"):
        return "sd"
    return name.split("-")[0]


# ── Model quality tiers ──────────────────────────────────────────────────────
# Imported from shared model_quality module — single source of truth for
# tier definitions, classification, and CLI warning messages.

try:
    from model_quality import classify_model_quality as _classify_model_quality
    from model_quality import quality_warning as _quality_warning
except ImportError:
    # Fallback: if model_quality.py is not on sys.path yet, try relative import
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from model_quality import classify_model_quality as _classify_model_quality
    from model_quality import quality_warning as _quality_warning

_IMAGE_ICON_GUIDE = """
━━━ ICON GUIDE — draw recognizable brand logos inside each chip ━━━━━━━━━━━━━━
UPGRADE (Gemini 2.5+): Each technology chip MUST display its recognizable brand
icon/logo drawn inside or directly above its text label.
Use simplified but immediately recognizable shapes in official brand colors.

FRONTEND / MOBILE
  React / React Native → blue atomic orbital (3 ellipses + central dot) #61DAFB
  Next.js              → bold black "N" lettermark #000000
  Vue                  → green layered V-diamond logo #42B883
  Angular              → red shield with angular "A" cutout #DD0031
  Svelte               → curved orange bracket/flame mark #FF3E00
  Flutter              → blue diagonal F-shape (3 horizontal bars) #54C5F8
  Tailwind CSS         → cyan stacked wave/fan of 3 arcs #06B6D4
  TypeScript           → blue square with bold white "TS" #3178C6
  JavaScript           → yellow square with black "JS" #F7DF1E

BACKEND / API
  FastAPI              → teal diamond with lightning bolt inside #009688
  Django               → dark green "Dj" lettermark #0C4B33
  Node.js              → green hexagon outline #339933
  NestJS               → red cat-paw / N in red circle #E0234E
  Spring               → light green coiled leaf spiral #6DB33F
  Flask                → minimal dark flask bottle silhouette

DATABASE
  PostgreSQL           → dark blue elephant head facing right #4169E1
  MySQL                → blue dolphin leaping right #4479A1
  MongoDB              → green stylized leaf/sprout #47A248
  Redis                → dark red brick/diamond grid pattern #DC382D
  Supabase             → teal lightning bolt #3ECF8E
  Firebase             → orange/yellow campfire flame #FFCA28

CLOUD / INFRA / DEVOPS
  AWS                  → orange curved smile swoosh below "aws" text #FF9900
  GCP / Google Cloud   → colorful 4-segment "G" #4285F4
  Azure                → blue stylized angular "A" wave #0078D4
  Docker               → blue whale with 3 white container blocks on back #2496ED
  Kubernetes           → blue ship helm/wheel (circle + 6 spokes + center dot) #326CE5
  Terraform            → purple stacked crystal/diamond cluster #7B42BC
  GitHub / Actions     → black octocat (cat body + octopus tentacles) #181717
  GitLab               → orange fox-head triangle #FC6D26

MESSAGING / QUEUE
  Kafka                → black bold "K" lettermark with angular strokes #000000
  RabbitMQ             → orange rabbit silhouette in speech bubble #FF6600
  Celery               → green gradient "C" or leaf stalk #37814A

AUTH / AI
  Auth0                → orange rounded "A" in circle #EB5424
  Clerk                → purple rounded "C" mark #6C47FF
  OpenAI               → black "O" swirl/bloom mark #000000
  Anthropic / Claude   → warm beige/brown stylized "A" lettermark #D4A27F
  LangChain            → teal chain-link icon

Rendering rules:
• Place icon centered above the chip's text label, approximately 22–26px equivalent
• Use the brand's listed primary color — never gray placeholders
• Approximate shapes are fine — recognizability over pixel-perfection
• For unlisted technologies: bold initial letter(s) in the layer's accent color
  styled into a small rounded badge
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

_HTML_ICON_GUIDE = """
━━━ ICON EMBEDDING (Gemini 2.5+ mode) — add inline SVG brand icons to chips ━━
UPGRADE: Redesign each technology chip to display its brand icon as an inline
SVG (16×16 px) BEFORE the name text. Use Simple Icons paths you know.
Emoji fallback when SVG path is uncertain — never invent broken paths.

Updated chip layout:
  <div class="chip">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="#[BRAND_COLOR]"
         style="flex-shrink:0;vertical-align:middle;">
      <path d="[SIMPLE_ICONS_SVG_PATH]"/>
    </svg>
    <span>[TechName]</span>
  </div>

Update .chip CSS to include: display:flex; align-items:center; gap:5px; padding:4px 10px 4px 7px;

Brand color reference (use as SVG fill):
  React #61DAFB · TypeScript #3178C6 · Next.js #000000 · Vue #42B883
  Angular #DD0031 · Svelte #FF3E00 · Tailwind #06B6D4 · JavaScript #F7DF1E
  FastAPI #009688 · Node.js #339933 · Django #092E20 · NestJS #E0234E
  PostgreSQL #4169E1 · MySQL #4479A1 · MongoDB #47A248 · Redis #DC382D
  Supabase #3ECF8E · Firebase #FFCA28 · Cassandra #1287B1
  Docker #2496ED · Kubernetes #326CE5 · AWS #FF9900 · GCP #4285F4
  Azure #0078D4 · Terraform #7B42BC · GitHub #181717 · GitLab #FC6D26
  Kafka #000000 · RabbitMQ #FF6600 · Auth0 #EB5424 · Clerk #6C47FF
  OpenAI #000000 · Anthropic #D4A27F

FALLBACK RULE: If you cannot recall an exact SVG path, use an emoji instead:
  React→⚛️  PostgreSQL→🐘  Redis→🔴  Docker→🐳  FastAPI→⚡  AWS→☁️
  Kubernetes→⚙️  MongoDB→🍃  GitHub→🐙  Python→🐍  Firebase→🔥  Terraform→💎
  Kafka→📨  Node.js→💚  Supabase→⚡  Auth0→🔐  TypeScript→🔷  Angular→🔴
Use emoji as a styled <span style="font-size:14px"> in place of the SVG element.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


# ── Prompt strategy registry ──────────────────────────────────────────────────

_PROMPT_STRATEGIES: dict[str, dict] = {
    "gemini": {
        "supports_icons": True,
        "context_window": 1_000_000,
        "style_vocabulary": ["glassmorphism", "gradient", "dark-background"],
        "prompt_fragments": {
            "image_icon_guide": _IMAGE_ICON_GUIDE,
            "html_icon_guide": _HTML_ICON_GUIDE,
        },
        "last_verified": "2026-03-25",
    },
    "dalle": {
        "supports_icons": False,
        "context_window": 4096,
        "style_vocabulary": [],
        "prompt_fragments": {},
        "last_verified": "2026-03-25",
    },
    "sd": {
        "supports_icons": False,
        "context_window": 2048,
        "style_vocabulary": [],
        "prompt_fragments": {},
        "last_verified": "2026-03-25",
    },
}


def _get_strategy(model: str) -> dict:
    """Return the prompt strategy dict for the given model, falling back to gemini."""
    family = _model_family(model)
    if family not in _PROMPT_STRATEGIES:
        print(f"\u26a0\ufe0f  Unrecognized model family '{family}' \u2014 falling back to gemini strategy.")
        family = "gemini"
    return _PROMPT_STRATEGIES[family]


_STALE_THRESHOLD_DAYS = 90


def _warn_if_stale(strategy: dict, family: str) -> None:
    """Print a warning if the strategy entry has not been verified recently."""
    lv = strategy.get("last_verified", "")
    if not lv:
        return
    try:
        verified = date.fromisoformat(lv)
        age = (date.today() - verified).days
        if age > _STALE_THRESHOLD_DAYS:
            print(
                f"\u26a0\ufe0f  Strategy for '{family}' was last verified {age} days ago ({lv}) "
                f"\u2014 consider updating _PROMPT_STRATEGIES."
            )
    except ValueError:
        pass


def _lookup_pricing(model: str) -> tuple[float, float, float]:
    # strip "models/" prefix if present
    key = model.replace("models/", "")
    # exact match first
    if key in _PRICING:
        return _PRICING[key]
    # prefix match (handles versioned names like gemini-2.5-flash-001)
    for k, v in _PRICING.items():
        if key.startswith(k) or k.startswith(key):
            return v
    return _DEFAULT_PRICING


# ── Cost calculation & display ────────────────────────────────────────────────

def _compute_cost(model: str, usage: dict) -> dict:
    inp_per_1m, out_per_1m, per_image = _lookup_pricing(model)
    inp_tok  = usage.get("prompt_tokens", 0) or 0
    out_tok  = usage.get("output_tokens", 0) or 0
    thk_tok  = usage.get("thoughts_tokens", 0) or 0
    n_images = usage.get("images_generated", 0) or 0

    input_cost    = (inp_tok  / 1_000_000) * inp_per_1m
    output_cost   = (out_tok  / 1_000_000) * out_per_1m
    thinking_cost = (thk_tok  / 1_000_000) * out_per_1m   # thoughts billed as output
    image_cost    = n_images * per_image
    total         = input_cost + output_cost + thinking_cost + image_cost

    return {
        "input_tokens":    inp_tok,
        "output_tokens":   out_tok,
        "thoughts_tokens": thk_tok,
        "images_generated": n_images,
        "input_cost":      input_cost,
        "output_cost":     output_cost,
        "thinking_cost":   thinking_cost,
        "image_cost":      image_cost,
        "total_cost":      total,
        "currency":        "USD",
    }


def print_cost_report(model: str, usage: dict, backend: str = "aistudio") -> None:
    """Print a formatted cost breakdown box to stdout."""
    c = _compute_cost(model, usage)
    W = 48  # box width

    def row(label: str, value: str) -> str:
        pad = W - 4 - len(label) - len(value)
        return f"│  {label}{' ' * pad}{value}  │"

    backend_label = "Vertex AI" if backend == "vertex" else "AI Studio"
    pricing_url = (
        "https://cloud.google.com/vertex-ai/generative-ai/pricing"
        if backend == "vertex"
        else "https://ai.google.dev/pricing"
    )

    line  = "─" * (W - 2)
    print()
    print(f"┌{line}┐")
    print(f"│{'  ⚡ Gemini Generation Cost':^{W-2}}│")
    print(f"├{line}┤")
    print(row("Model", model))
    print(row("Backend", backend_label))
    print(f"├{line}┤")
    if c["input_tokens"]:
        print(row(f"  Input    {c['input_tokens']:>7,} tok", f"${c['input_cost']:.6f}"))
    if c["output_tokens"]:
        print(row(f"  Output   {c['output_tokens']:>7,} tok", f"${c['output_cost']:.6f}"))
    if c["thoughts_tokens"]:
        print(row(f"  Thinking {c['thoughts_tokens']:>7,} tok", f"${c['thinking_cost']:.6f}"))
    if c["images_generated"]:
        print(row(f"  Image(s) {c['images_generated']:>7,} img", f"${c['image_cost']:.6f}"))
    print(f"├{line}┤")
    print(row("  TOTAL", f"${c['total_cost']:.6f} USD"))
    print(f"└{line}┘")
    print(f"  ⚠  Estimates — verify at: {pricing_url}")
    print()


# ── Model routing ─────────────────────────────────────────────────────────────

def _is_image_model(model: str) -> bool:
    """True for models that natively output images (response_modalities=IMAGE)."""
    name = model.replace("models/", "").lower()
    return "image" in name


# ── Prompt builders ───────────────────────────────────────────────────────────

def _layers_description(layers: list[dict]) -> str:
    parts = []
    for layer in layers:
        items = ", ".join(layer.get("items", []))
        parts.append(f"  • {layer['label']}: {items}")
    return "\n".join(parts) if parts else "  (no layers specified)"


def _build_image_prompt(config: dict, viz_type: str, use_icons: bool = False) -> str:
    """
    Visual prompt for native image generation models (*-image).
    Describes the desired output visually instead of asking for code.
    """
    title    = config.get("title", "System Architecture")
    subtitle = config.get("subtitle", "")
    author   = config.get("author", "")
    cta      = config.get("linkedin_cta", "Follow for more architecture content")
    layers   = config.get("layers", [])
    conns    = config.get("connections", [])
    desc     = config.get("description", "")

    layer_txt = _layers_description(layers)
    conn_txt  = (
        "  " + ", ".join(f"{c['from']} → {c['to']}" for c in conns)
        if conns else "  (auto-infer from layer order)"
    )
    learnings = config.get("learnings", "")
    learnings_block = (
        f"\nKey learnings / technologies featured:\n{learnings}\n"
        "The infographic should highlight these specific technologies and insights.\n"
        if learnings else ""
    )

    icon_appendix = _IMAGE_ICON_GUIDE if use_icons else ""

    if viz_type == "dashboard":
        base = f"""\
Create a STUNNING, professional LinkedIn infographic image at exactly 1080×1080 pixels.

━━━ CONTENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {title}
Data / metrics:
{desc or layer_txt}{learnings_block}
Footer CTA: {cta}
Author: {author}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ VISUAL DESIGN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Exactly 1080×1080 px square — LinkedIn post format
• Background: deep dark gradient (#0A0F1E → #111827), 2-3 large soft blurred blobs
• Bold title strip at top on dark navy, gradient white text
• KPI metric cards in grid (glassmorphism: translucent dark, frosted glass edge,
  colored glow shadow): one per metric with a GIANT hero number in vivid gradient
  color, trend arrow (↑ green / ↓ red), metric name in small muted uppercase
• Radial SVG progress ring around each hero number
• Footer dark strip with CTA text
• Colors per card: #3B82F6 blue, #10B981 emerald, #F59E0B amber, #EF4444 red,
  #8B5CF6 violet, #06B6D4 cyan — assign one per metric
• Typography: ultra-bold modern sans-serif, clean and readable
• Style: Vercel dashboard meets Linear.app meets Stripe — premium $5,000 design

CRITICAL STYLE CONSTRAINTS — DO NOT VIOLATE:
• This is NOT a sketch, NOT hand-drawn, NOT a wireframe, NOT a whiteboard drawing
• Render as a PIXEL-PERFECT digital UI design — crisp vector edges, no pencil textures
• Use FLAT or subtle gradient fills — never hatching, crosshatch, or pencil shading
• All text must be sharp, anti-aliased, horizontal, and perfectly legible
• Colors must be SATURATED and VIBRANT (not muted, pastel, or washed-out)
• Backgrounds must be smooth gradients — no paper texture, no grain, no noise
• Think: Figma mockup, Dribbble top shot, Apple keynote slide — NOT napkin sketch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""" + icon_appendix

    else:
        base = f"""\
Create a STUNNING, professional LinkedIn architecture infographic image at exactly 1080×1080 pixels.

━━━ ARCHITECTURE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {title}
{f'Subtitle: {subtitle}' if subtitle else ''}
Component layers:
{layer_txt}
Data flows / connections:
{conn_txt}{learnings_block}
Footer CTA: {cta}
{f'Author: {author}' if author else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ VISUAL DESIGN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Exactly 1080×1080 px square — LinkedIn post format
• Background: deep space dark gradient (#0A0F1E → #0D1B2A) with 2-3 large
  blurred accent-colored blob shapes in background at low opacity
• Layout top-to-bottom:
    ① Title strip (≈13%): dark navy bar, bold white title with gradient highlight,
      subtitle in muted slate, left 4px colored accent bar
    ② Component grid (≈78%): balanced grid of glassmorphism cards
    ③ Footer strip (≈9%): dark bar, centered CTA text, muted
• Each component group card:
    – Rounded frosted-glass panel (dark translucent bg, subtle white border)
    – 4px vivid top-border in layer's accent color
    – Layer label: small UPPERCASE bold text in accent color
    – Technology chips: dark pill badges with colored border, white text
    – Soft colored glow/shadow matching accent
• Accent colors per layer type:
    Frontend → #3B82F6 blue       Mobile   → #8B5CF6 violet
    Backend  → #F59E0B amber      Database → #10B981 emerald
    Auth     → #FBBF24 yellow     Queue    → #A855F7 purple
    Storage  → #6366F1 indigo     Cloud    → #06B6D4 cyan
    Infra    → #EF4444 red        AI/ML    → #22C55E green
    CI/CD    → #64748B slate      Monitor  → #F97316 orange
• Dashed glowing arrows between connected layer cards showing data flow
• Typography: ultra-bold modern sans-serif, clean, high contrast, readable
• Style: Vercel + Linear + Stripe design system — premium $5,000 design quality

CRITICAL STYLE CONSTRAINTS — DO NOT VIOLATE:
• This is NOT a sketch, NOT hand-drawn, NOT a wireframe, NOT a whiteboard drawing
• Render as a PIXEL-PERFECT digital UI design — crisp vector edges, no pencil textures
• Use FLAT or subtle gradient fills — never hatching, crosshatch, or pencil shading
• All text must be sharp, anti-aliased, horizontal, and perfectly legible
• Colors must be SATURATED and VIBRANT (not muted, pastel, or washed-out)
• Backgrounds must be smooth gradients — no paper texture, no grain, no noise
• Think: Figma mockup, Dribbble top shot, Apple keynote slide — NOT napkin sketch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""" + icon_appendix
    return base


_ARCH_HTML_PROMPT = """\
You are a world-class UI/data-visualization designer who creates stunning LinkedIn
architecture infographics used as reference-quality visuals by senior engineers at
companies like Vercel, Stripe, and Linear.

Create a PRODUCTION-READY, self-contained HTML file visualizing the system
architecture below as a professional 1080×1080 px LinkedIn infographic.

━━━ ARCHITECTURE DATA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{data}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ DESIGN REQUIREMENTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CANVAS: 1080×1080 px fixed, overflow:hidden
BACKGROUND: rich dark gradient (#0A0F1E → #0D1B2A) + 2-3 blurred blob shapes
LAYOUT: title bar (13%) → glassmorphism card grid (78%) → footer bar (9%)
CARDS: rgba(255,255,255,0.05) bg, backdrop-filter:blur(12px), colored top border
CHIPS: rounded rectangle (not pill) inside each card. Each chip has TWO lines:
  Line 1 — technology name: 11-12px bold, white, colored left-border accent
  Line 2 — benefit tagline: 9px, rgba(255,255,255,0.55), italic, max 8 words
  Use YOUR KNOWLEDGE to write a concise, accurate benefit for each technology
  in the context of this specific project. Examples of good benefit taglines:
    Flutter App   → "Cross-platform iOS · Android · Web"
    FastAPI       → "Async Python · auto OpenAPI docs"
    PostgreSQL    → "Relational store for user records"
    Redis         → "Pub/Sub event bus + response cache"
    LangChain     → "LLM orchestration & agent chains"
    JWT           → "Stateless auth · HS256 signed tokens"
    Terraform IaC → "Declarative AWS infra as code"
    EC2           → "t3.micro compute · eu-west-1"
  Keep taglines SHORT (≤8 words), factual, and specific to the architecture shown.
  If fewer than 6 items total: make the chips taller and use 10px for the tagline.
ACCENT COLORS: Frontend #3B82F6, Backend #F59E0B, DB #10B981, Cloud #06B6D4,
               AI #22C55E, Auth #FBBF24, Queue #A855F7, Infra #EF4444, Mobile #8B5CF6
LAYOUT NOTES:
  • Because chips are taller (two lines), space cards generously — 3×3 max grid.
  • If ≤6 groups: use 2-column or 2×3 layout with larger cards to fill the space.
  • Connections between groups: thin dashed SVG lines with animated draw-on.
ANIMATIONS (CSS only, no JS):
  @keyframes float — translateY -6px ↔ 0, 4s ease-in-out infinite alternate, staggered
  @keyframes blob  — scale + rotation, 18s linear infinite
  SVG connection lines: stroke-dashoffset draw-on animation
TYPOGRAPHY: system-ui; title 32-38px 800 gradient clip; group label 11px 700 uppercase
OUTPUT RULES:
  • Output ONLY the complete HTML. No markdown fences, no explanation.
  • All CSS in <style>. Zero external CDN dependencies.
  • No JavaScript — CSS animations only.
  • Renders correctly at exactly 1080×1080 px in Chromium.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

_DASHBOARD_HTML_PROMPT = """\
You are a world-class data visualization designer creating stunning LinkedIn KPI infographics.

Create a PRODUCTION-READY, self-contained HTML dashboard infographic (1080×1080 px).

━━━ DATA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{data}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CANVAS: 1080×1080 px, dark gradient bg (#0A0F1E → #111827)
LAYOUT: title strip (12%) → KPI grid (78%) → footer (10%)
CARDS: glassmorphism, hero number 52-64px 900 weight in vivid gradient,
       trend indicator ↑/↓, animated radial SVG progress ring
COLORS per card: #3B82F6, #10B981, #F59E0B, #EF4444, #8B5CF6, #06B6D4
OUTPUT: complete HTML only, no fences, no JS, no CDN, renders at 1080×1080.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def _build_html_prompt(config: dict, viz_type: str, use_icons: bool = False) -> str:
    data_str = json.dumps(config, indent=2, ensure_ascii=False)
    learnings = config.get("learnings", "")
    if learnings:
        data_str = (
            data_str
            + f"\n\nKey learnings / technologies featured:\n{learnings}\n"
            + "The infographic should highlight these specific technologies and insights."
        )
    tmpl = _DASHBOARD_HTML_PROMPT if viz_type == "dashboard" else _ARCH_HTML_PROMPT
    prompt = tmpl.format(data=data_str)
    if use_icons:
        prompt += _HTML_ICON_GUIDE
    return prompt


# ── Gemini API calls ──────────────────────────────────────────────────────────

def _extract_usage(response) -> dict:
    """Pull token counts out of a GenerateContentResponse."""
    um = getattr(response, "usage_metadata", None)
    if um is None:
        return {}
    return {
        "prompt_tokens":    getattr(um, "prompt_token_count",    None),
        "output_tokens":    getattr(um, "candidates_token_count", None),
        "thoughts_tokens":  getattr(um, "thoughts_token_count",  None),
        "total_tokens":     getattr(um, "total_token_count",     None),
    }


def _call_image_mode(
    prompt: str, client, model: str
) -> tuple[bytes | None, dict]:
    """
    Call Gemini with response_modalities=['IMAGE'].
    Returns (image_bytes_or_None, usage_dict).
    """
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    usage = _extract_usage(response)

    image_bytes: bytes | None = None
    images_found = 0
    for cand in response.candidates:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None):
                image_bytes  = part.inline_data.data
                images_found = 1
                break
        if image_bytes:
            break

    usage["images_generated"] = images_found
    return image_bytes, usage


def _call_gemini_text_mode(
    prompt: str, client, model: str
) -> tuple[str, dict]:
    """
    Call Gemini for HTML text output.
    Returns (html_text, usage_dict).
    """
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.85,
            top_p=0.95,
            # Thinking models (2.5+, 3+) need high output limits; 2.0 and older cap at 8192
            max_output_tokens=65536 if ("2.5" in model or re.search(r"gemini-[3-9]", model)) else 8192,
        ),
    )
    usage = _extract_usage(response)
    usage["images_generated"] = 0
    return response.text, usage


def _call_openrouter_text_mode(
    prompt: str, model: str, api_key: str
) -> tuple[str, dict]:
    """
    Call OpenRouter chat completions API for HTML text output.
    Returns (html_text, usage_dict).
    """
    resp = _requests_lib.post(
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

    # ── Status-first error handling (check before JSON parse) ──
    if resp.status_code == 401:
        print("❌  OpenRouter API key is invalid (401) — check INFG_OPENROUTER_API_KEY in your .env")
        sys.exit(1)
    if resp.status_code == 402:
        print("❌  OpenRouter account has insufficient credits (402) — add credits at openrouter.ai/credits")
        sys.exit(1)
    if resp.status_code != 200:
        print(f"❌  OpenRouter API error ({resp.status_code}): {_redact_key(resp.text[:200])}")
        sys.exit(1)

    data = resp.json()
    html_text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return html_text, {
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "total_cost": usage.get("total_cost"),  # None in practice — not in chat completions response
    }


# ── HTML helpers ──────────────────────────────────────────────────────────────

def _strip_fences(raw: str) -> str:
    """Strip markdown code fences and any LLM preamble before them.

    Many models emit conversational text before the HTML code block, e.g.:
      "Here's the production-ready HTML file: ```html\n<html>..."
    This function strips everything up to and including the opening fence,
    and any trailing closing fence.
    """
    raw = raw.strip()
    # --- Strip preamble: find the first code fence and discard everything before it ---
    for fence in ("```html\n", "```HTML\n", "```html\r\n", "```\n"):
        idx = raw.find(fence)
        if idx != -1:
            raw = raw[idx + len(fence):]
            break
    # --- Strip trailing fence ---
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def _playwright_screenshot(html_path: Path) -> Path | None:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return None
    png_path = html_path.with_suffix(".png")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page    = browser.new_page(viewport={"width": 1080, "height": 1080})
            page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
            page.wait_for_timeout(2000)
            page.screenshot(
                path=str(png_path),
                clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
            )
            browser.close()
        return png_path
    except Exception as exc:
        print(f"⚠️   Playwright screenshot failed: {exc}")
        return None


# ── Public entry point ────────────────────────────────────────────────────────

_IMAGE_FALLBACK = "gemini-2.5-flash-image"   # used when the primary image model returns 404


def _resolve_llm_provider(args) -> tuple[str, str | None]:
    """Resolve LLM provider and model from CLI flags and env vars.

    Precedence: CLI flag > env var > default ("gemini").
    Auto-detects OpenRouter when model contains '/' and provider was not
    explicitly configured (e.g. INFG_LLM_MODEL=provider/model without
    setting INFG_LLM_PROVIDER=openrouter).
    Returns (provider, model_or_None).
    """
    explicit_provider = getattr(args, "llm_provider", None) or _LLM_PROVIDER
    model    = getattr(args, "llm_model", None) or _LLM_MODEL or None
    if explicit_provider:
        provider = explicit_provider.lower()
    elif model and "/" in model:
        provider = "openrouter"
    else:
        provider = "gemini"
    return provider, model


def generate_pretty(
    config: dict,
    output: str = "pretty_infographic.png",
    viz_type: str = "architecture",
    model_name: str = "gemini-3.1-flash-image-preview",
    llm_provider: str = "gemini",
    llm_model: str | None = None,
) -> Path:
    """
    Generate a Gemini-powered pretty infographic and print a cost report.

    Parameters
    ----------
    config     : arch JSON dict or free-form data dict
    output     : destination file path
    viz_type   : "architecture" | "dashboard"
    model_name : Gemini model identifier (default: gemini-3.1-flash-image-preview)
    """
    # ── Provider-specific setup ────────────────────────────────────────────────
    if llm_provider == "openrouter":
        client = None
        backend = None
        use_icons = False
    else:
        if not _GENAI_OK:
            print(
                "❌  google-genai is not installed (required for pretty mode only).\n"
                "   Install the SDK with: pip install google-genai\n"
                "   Optional HTML screenshot support: pip install playwright && playwright install chromium\n"
                "\n"
                "   Note: Core matplotlib generation (generate.py) works without any extra packages."
            )
            sys.exit(1)

        # ── Build client with smart backend routing ────────────────────────────────
        # AI-Studio-only models go to AI Studio; stable models go to Vertex AI.
        client, backend = _build_genai_client(model_name)

        # ── Detect icon mode (registry-based strategy lookup) ─────────────────
        strategy = _get_strategy(model_name)
        _warn_if_stale(strategy, _model_family(model_name))
        use_icons = strategy["supports_icons"]
        if use_icons:
            maj, min_ = _gemini_version(model_name)
            print(f"🎨  Icon mode: enabled (Gemini {maj}.{min_}+ detected — brand logos will be included)")

        # ── Report which backend is active and check credentials ──────────────────
        if backend == "vertex":
            print(f"🌐  Backend: Vertex AI  (project={_VERTEX_PROJECT}, region={_VERTEX_LOCATION})")
            _vertex_policy_warning()
        else:
            print("🔑  Backend: AI Studio (API key)")

    out_path = Path(output)

    # ── Image generation path (for *-image models, Gemini only) ───────────────
    if llm_provider != "openrouter" and _is_image_model(model_name):
        print(f"🎨  Calling {model_name} (image generation mode) …")
        prompt = _build_image_prompt(config, viz_type, use_icons=use_icons)
        try:
            img_bytes, usage = _call_image_mode(prompt, client, model_name)
        except Exception as e:
            if "404" in str(e) and model_name != _IMAGE_FALLBACK:
                print(f"⚠️  {model_name} not available on this endpoint — falling back to {_IMAGE_FALLBACK}")
                model_name = _IMAGE_FALLBACK
                img_bytes, usage = _call_image_mode(prompt, client, model_name)
            else:
                _handle_credential_error(e)
                raise

        print_cost_report(model_name, usage, backend)

        if img_bytes:
            png_path = out_path.with_suffix(".png")
            png_path.parent.mkdir(parents=True, exist_ok=True)
            png_path.write_bytes(img_bytes)
            print(f"✅  Pretty PNG → {png_path.resolve()}")
            print(f"    1080×1080 px — ready to post on LinkedIn!")
            return png_path
        else:
            print("⚠️   No image returned — falling back to HTML mode.")
            # fall through to HTML path

    # ── HTML generation path (text models or image-mode fallback) ────────────
    print(f"🤖  Calling {model_name} (HTML generation mode) …")
    prompt   = _build_html_prompt(config, viz_type, use_icons=use_icons)
    try:
        if llm_provider == "gemini":
            if llm_model:
                effective_model = llm_model
            elif _model_family(model_name) == "gemini":
                effective_model = model_name
            else:
                effective_model = "gemini-2.5-flash"
            # ── Quality tier advisory ──
            tier = _classify_model_quality(effective_model)
            _quality_warning(effective_model, tier)
            raw_html, usage = _call_gemini_text_mode(prompt, client, effective_model)
        elif llm_provider == "openrouter":
            # ── Requests library guard ──
            if not _REQUESTS_OK:
                print(
                    "❌  requests is not installed (required for OpenRouter).\n"
                    "   Install with: pip install requests"
                )
                sys.exit(1)

            # ── Model format validation (must have provider/model slash) ──
            effective_model = llm_model or _LLM_MODEL
            if not effective_model:
                print("❌  OpenRouter requires a model — set INFG_LLM_MODEL or pass --llm-model")
                sys.exit(1)
            if "/" not in effective_model:
                print(
                    f"❌  OpenRouter model must include provider prefix: "
                    f"'openai/gpt-4o', got {effective_model!r}"
                )
                sys.exit(1)

            # ── API key resolution (provider-specific > generic) ──
            or_api_key = _OPENROUTER_API_KEY or _LLM_API_KEY
            if not or_api_key:
                print("❌  OpenRouter requires an API key — set INFG_OPENROUTER_API_KEY or INFG_LLM_API_KEY in your .env")
                sys.exit(1)

            print(f"🤖  Calling {effective_model} via OpenRouter …")
            # ── Quality tier advisory ──
            tier = _classify_model_quality(effective_model)
            _quality_warning(effective_model, tier)
            raw_html, or_usage = _call_openrouter_text_mode(prompt, effective_model, or_api_key)
        else:
            print(f"❌  Unknown LLM provider: {llm_provider!r}. Supported: gemini, openrouter")
            sys.exit(1)
    except Exception as e:
        _handle_credential_error(e)
        raise
    html     = _strip_fences(raw_html)

    # ── Cost report ──
    if llm_provider == "openrouter":
        print()
        print(f"  Model:         {effective_model}")
        print(f"  Input tokens:  {or_usage['input_tokens']}")
        print(f"  Output tokens: {or_usage['output_tokens']}")
        if or_usage.get("total_cost") is not None:
            print(f"  Cost:          ${or_usage['total_cost']:.5f}")
        print()
    else:
        print_cost_report(model_name, usage, backend)

    html_path = out_path.with_suffix(".html")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    print(f"✅  Pretty HTML → {html_path.resolve()}")

    png_path = _playwright_screenshot(html_path)
    if png_path:
        print(f"📸  PNG → {png_path.resolve()}")
        print(f"    1080×1080 px — ready to post on LinkedIn!")
    else:
        print()
        print("💡  To export to PNG, install Playwright:")
        print("    pip install playwright && playwright install chromium")
        print(f"    Then rerun, or open {html_path.resolve()} in Chrome and screenshot.")

    return html_path


# ── Codebase-to-config mapping ────────────────────────────────────────────────


def _config_from_codebase_report(
    report: dict,
    title: str = "System Architecture",
    subtitle: str = "Technical Architecture Overview",
    author: str = "",
    cta: str = "Follow for more software architecture content",
) -> tuple:
    """Convert a CodebaseReport dict into a (config, viz_type) tuple.

    Per D-05: viz_type is always "arch" for codebase infographics.
    Per D-06: report["layers"] -> config["layers"],
              report["summary_text"] -> config["description"],
              report["connections"] -> config["connections"].
    Per D-07: Title derived from directory name when title is the argparse default.
    """
    # D-07: derive title from directory name if user didn't set --title
    if title == "System Architecture":
        raw_name = Path(report.get("root", "unknown")).resolve().name
        title = raw_name.replace("-", " ").replace("_", " ").title()

    config = {
        "title":        title,
        "subtitle":     subtitle,
        "author":       author,
        "linkedin_cta": cta,
        "description":  report.get("summary_text", ""),   # D-06: summary_text, NOT "summary"
        "layers":       report.get("layers", []),          # D-06: direct, arch.json-compatible
        "connections":  report.get("connections", []),     # D-06: connections if present
    }
    viz_type = "arch"  # D-05: always architecture diagram
    return config, viz_type


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Gemini 'pretty' infographic generator — prints cost after every run"
    )
    ap.add_argument("--config",   help="Path to arch.json (from parse_context.py)")
    ap.add_argument("--layers",   help="Quick layers: 'Frontend:React,Next.js|Backend:FastAPI'")
    ap.add_argument("--text",     help="Free-form architecture or data description")
    ap.add_argument("--codebase", help="Path to codebase directory (uses read_codebase.py)")
    ap.add_argument("--type",     default="architecture",
                    choices=["architecture", "dashboard"],
                    help="Visualization type (default: architecture)")
    ap.add_argument("--title",    default="System Architecture")
    ap.add_argument("--subtitle", default="Technical Architecture Overview")
    ap.add_argument("--author",   default="")
    ap.add_argument("--cta",      default="Follow for more software architecture content")
    ap.add_argument("--model",    default="gemini-3.1-flash-image-preview",
                    help="Gemini model (default: gemini-3.1-flash-image-preview)")
    ap.add_argument("--llm-provider", default=None,
                    help="LLM provider for text/HTML path: gemini (default) or openrouter")
    ap.add_argument("--llm-model",    default=None,
                    help="LLM model override for text/HTML path (e.g. gemini-2.5-pro)")
    ap.add_argument("--output",   default="pretty_infographic.png",
                    help="Output file (.png for image models, .html for text models)")
    ap.add_argument("--learnings", default="",
                    help="Technologies or learnings this post is about (drives infographic content focus)")
    ap.add_argument("--template", default="arch-dark-glassmorphism",
                    help="Jinja2 template name for template-based rendering (default: arch-dark-glassmorphism)")
    ap.add_argument("--legacy-html", action="store_true",
                    help="Use legacy LLM-generated HTML instead of template-based rendering")
    ap.add_argument("--infographic-type", default="architecture",
                    choices=["architecture", "comparison", "feature", "process", "cheatsheet"],
                    help="Type of infographic to generate (default: architecture)")
    ap.add_argument("--style", default="modern-dark",
                    choices=["modern-dark", "modern-light", "illustrated"],
                    help="Visual style preset (default: modern-dark)")
    args = ap.parse_args()

    # Build config dict -------------------------------------------------------
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            config = json.load(fh)
        if args.title != "System Architecture":
            config["title"] = args.title
        if args.author:
            config["author"] = args.author
        if args.cta:
            config["linkedin_cta"] = args.cta

    elif args.layers:
        config = {
            "title":        args.title,
            "subtitle":     args.subtitle,
            "author":       args.author,
            "linkedin_cta": args.cta,
            "layers":       layers_from_string(args.layers),
            "connections":  [],
        }

    elif args.text:
        config = {
            "title":        args.title,
            "subtitle":     args.subtitle,
            "author":       args.author,
            "linkedin_cta": args.cta,
            "description":  args.text,
            "layers":       [],
            "connections":  [],
        }
        viz_type = args.type

    elif args.codebase:
        try:
            from read_codebase import read_codebase as _read_codebase  # type: ignore
        except ImportError:
            ap.error("read_codebase.py not found — ensure Phase 4 scripts are available")
        report = _read_codebase(args.codebase)

        # ── v2 template-based rendering (default) ────────────────────────
        if not args.legacy_html:
            try:
                from content_structurer import structure_codebase  # type: ignore
                from template_renderer import render_infographic   # type: ignore
                from image_prompt_builder import build_image_prompt as _build_v2_image_prompt  # type: ignore
            except ImportError:
                print("⚠️  Template modules not found — falling back to legacy HTML mode.")
                print("   Install jinja2 and simplepycons for template-based rendering.")
                args.legacy_html = True

        if not args.legacy_html:
            llm_provider, llm_model = _resolve_llm_provider(args)
            effective_model = llm_model or _LLM_MODEL or "google/gemini-2.0-flash-001"
            or_api_key = _OPENROUTER_API_KEY or _LLM_API_KEY
            structured_data = structure_codebase(
                report, model=effective_model, api_key=or_api_key or None,
            )
            # Override title if user specified
            if args.title != "System Architecture":
                structured_data["title"] = args.title
            if args.author:
                structured_data["author"] = args.author
            if args.cta:
                structured_data["footer_cta"] = args.cta

            # ── Choose rendering path: AI image vs HTML template ──────────
            image_model = _IMAGE_MODEL_ENV if (_IMAGE_MODEL_ENV and args.model == "gemini-3.1-flash-image-preview") else args.model

            # Path A: AI image generation (Gemini image models → PNG directly)
            if _GENAI_OK and _is_image_model(image_model):
                print(f"🎨  Building designer-quality image prompt ({args.infographic_type} / {args.style})...")
                img_prompt = _build_v2_image_prompt(
                    structured_data,
                    infographic_type=args.infographic_type,
                    style=args.style,
                )
                client, backend = _build_genai_client(image_model)
                if backend == "vertex":
                    print(f"🌐  Backend: Vertex AI  (project={_VERTEX_PROJECT}, region={_VERTEX_LOCATION})")
                else:
                    print("🔑  Backend: AI Studio (API key)")
                print(f"🎨  Calling {image_model} (AI image generation)...")
                try:
                    img_bytes, usage = _call_image_mode(img_prompt, client, image_model)
                except Exception as e:
                    if "404" in str(e) and image_model != _IMAGE_FALLBACK:
                        print(f"⚠️  {image_model} not available — falling back to {_IMAGE_FALLBACK}")
                        image_model = _IMAGE_FALLBACK
                        img_bytes, usage = _call_image_mode(img_prompt, client, image_model)
                    else:
                        _handle_credential_error(e)
                        raise

                print_cost_report(image_model, usage, backend)

                if img_bytes:
                    out_path = Path(args.output).with_suffix(".png")
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_bytes(img_bytes)
                    print(f"✅  AI Infographic → {out_path.resolve()}")
                    print(f"    1080×1080 px — ready to post on LinkedIn!")
                    sys.exit(0)
                else:
                    print("⚠️  No image returned — falling back to HTML template.")

            # Path B: HTML template rendering (OpenRouter or non-image models)
            html_path = render_infographic(
                structured_data,
                template_name=args.template,
                output=args.output,
            )
            print(f"✅  Pretty HTML → {html_path.resolve()}")
            png_path = _playwright_screenshot(html_path)
            if png_path:
                print(f"📸  PNG → {png_path.resolve()}")
                print(f"    1080×1080 px — ready to post on LinkedIn!")
            else:
                print()
                print("💡  To export to PNG, install Playwright:")
                print("    pip install playwright && playwright install chromium")
                print(f"    Then rerun, or open {html_path.resolve()} in Chrome and screenshot.")
            sys.exit(0)

        # ── Legacy path: LLM generates HTML from scratch ─────────────────
        config, viz_type = _config_from_codebase_report(
            report,
            title=args.title,
            subtitle=args.subtitle,
            author=args.author,
            cta=args.cta,
        )

    else:
        ap.error("Provide --config arch.json, --layers '...', --text '...', or --codebase <dir>")

    # Set viz_type for branches that haven't set it yet (config and layers)
    if not args.codebase and not args.text:
        viz_type = args.type

    if args.learnings:
        config["learnings"] = args.learnings

    llm_provider, llm_model = _resolve_llm_provider(args)
    image_model = _IMAGE_MODEL_ENV if (_IMAGE_MODEL_ENV and args.model == "gemini-3.1-flash-image-preview") else args.model
    generate_pretty(config, args.output, viz_type, image_model,
                    llm_provider=llm_provider, llm_model=llm_model)
