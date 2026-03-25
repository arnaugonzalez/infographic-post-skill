# Infographic Skill

## What This Is

A Claude Code skill that generates professional infographics, LinkedIn architecture diagrams, and AI-powered "pretty mode" visuals. Built for engineers and PMs who want publication-quality graphics from structured data or free-form context — with Google Gemini as the default image model, OpenRouter for any text LLM, and a matplotlib fallback for offline use.

## Core Value

Turn any data or context into a publication-ready infographic with one command — no design tools required.

## Shipped: v1.0 — Multi-Provider Model Support

**Delivered:** Added configurable LLM provider (OpenRouter + any model) and hardened the skill for OSS publication — clean credentials, accurate docs, offline safety.

## Requirements

### Validated

- ✓ Matplotlib-based infographic canvas with palettes and layout primitives — quick tasks
- ✓ LinkedIn architecture diagram generator (`generate_linkedin_arch.py`) — quick tasks
- ✓ AI Studio pretty mode via `google-genai` SDK (`generate_pretty.py`) — quick tasks
- ✓ Vertex AI routing fallback for stable Gemini models — quick tasks
- ✓ OSS foundations: MIT LICENSE, README.md, .env.example, requirements.txt — quick tasks
- ✓ Version output manager (`scripts/version_output.py`) — quick tasks
- ✓ HTML output path via Playwright for text models — quick tasks
- ✓ Configurable LLM provider (env var to set provider + model for text generation) — v1.0
- ✓ Configurable image model + API key per invocation or env — v1.0
- ✓ OpenRouter integration (OpenAI-compatible API for LLM text tasks) — v1.0
- ✓ `gemini-3.1-flash-image-preview` hardened as default with clear docs — v1.0
- ✓ Deploy readiness: clean credentials, error guidance, .env.example complete — v1.0

### Active

*(none — v1.0 fully shipped; next requirements defined in v1.1 milestone)*

### Out of Scope

- Native Stable Diffusion / DALL-E image generation — different SDK entirely; deferred to v2
- Web UI or dashboard — CLI/skill interface is the contract; GUI adds scope creep
- Video/animation output — static infographics only
- OpenRouter for image generation — incompatible response format with Gemini `inline_data`; Gemini image quality is the differentiator
- Abstract provider base classes / LiteLLM — two providers don't justify ABC or registry; flat `if/elif` is correct scope

## Context

- Stack: Python 3.9+, matplotlib, google-genai SDK, Pillow, numpy, Playwright, requests
- Pretty mode routes between AI Studio (INFG_API_KEY) and Vertex AI (INFG_VERTEX_PROJECT + ADC)
- AI-Studio-only models (like `gemini-3.1-flash-image-preview`) are hard-coded in `_AI_STUDIO_ONLY` list
- OpenRouter uses `requests.post()` to the OpenAI-compatible API — no `openai` package required
- `openai` package is guarded by `_OPENAI_OK` lazy import — matplotlib offline path works without it
- The skill is invoked from Claude Code via SKILL.md; all scripts are called via Bash
- ~10,700 LOC Python (including tests); 17 pytest tests passing

## Constraints

- **Tech stack**: Python only — no Node.js or other runtimes in the skill scripts
- **Backwards compatibility**: Existing `.env` users must not break; new vars are additive
- **Offline mode**: matplotlib path must always work without any API key
- **Security**: No API keys in code; all via env vars; .env.example must be safe to commit

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| google-genai SDK for Gemini | Official SDK, handles AI Studio + Vertex AI routing | ✓ Good |
| gemini-3.1-flash-image-preview as default | Best quality/cost for image generation in Feb 2026 | ✓ Good |
| matplotlib as offline fallback | Zero-credential path for all users | ✓ Good |
| Playwright for HTML→PNG | Required for text-model (non-image) Gemini output | ⚠️ Revisit — heavy dependency |
| OpenRouter via `requests.post()` | Zero new required dependency; openai SDK deferred | ✓ Shipped v1.0 |
| Flat `if/elif` provider dispatch | Two providers don't justify ABC/registry overhead | ✓ Good |
| Inline `re.sub()` in `_redact_key` | Simpler multi-pattern extension than compiled module-level regex | ✓ Good |
| `sk-or-v1-` prefix retained in redaction | Users can identify which key leaked | ✓ Good |
| Removed google-genai/playwright from required pip deps in SKILL.md | They are optional; required listing caused unnecessary installs | ✓ Good |

---
*Last updated: 2026-03-25 — v1.0 milestone complete*
