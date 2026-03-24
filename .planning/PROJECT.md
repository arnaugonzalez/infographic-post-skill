# Infographic Skill

## What This Is

A Claude Code skill that generates professional infographics, LinkedIn architecture diagrams, and AI-powered "pretty mode" visuals. Built for engineers and PMs who want publication-quality graphics from structured data or free-form context — with Google Gemini as the default image model and a matplotlib fallback for offline use.

## Core Value

Turn any data or context into a publication-ready infographic with one command — no design tools required.

## Current Milestone: v1.0 — Multi-Provider Model Support

**Goal:** Make the infographic skill production-ready for OSS deployment by adding configurable LLM and image model providers, with `gemini-3.1-flash-image-preview` as the hardened default and OpenRouter as the path to any LLM.

**Target features:**
- `gemini-3.1-flash-image-preview` hardened as the default image model
- Configurable LLM provider + model via env var (swap text generation backend)
- Configurable image model + API key (use any image GenAI model per invocation)
- OpenRouter integration (OpenAI-compatible LLM provider for text tasks)
- Deploy readiness audit (credentials, error messages, docs, .env.example)

## Requirements

### Validated

<!-- Shipped quick tasks — confirmed working -->

- ✓ Matplotlib-based infographic canvas with palettes and layout primitives — quick tasks
- ✓ LinkedIn architecture diagram generator (`generate_linkedin_arch.py`) — quick tasks
- ✓ AI Studio pretty mode via `google-genai` SDK (`generate_pretty.py`) — quick tasks
- ✓ Vertex AI routing fallback for stable Gemini models — quick tasks
- ✓ OSS foundations: MIT LICENSE, README.md, .env.example, requirements.txt — quick tasks
- ✓ Version output manager (`scripts/version_output.py`) — quick tasks
- ✓ HTML output path via Playwright for text models — quick tasks

### Active

- ✓ Configurable LLM provider (env var to set provider + model for text generation) — Validated in Phase 1: Provider Resolution Infrastructure
- ✓ Configurable image model + API key per invocation or env — Validated in Phase 1: Provider Resolution Infrastructure
- ✓ OpenRouter integration (OpenAI-compatible API for LLM text tasks) — Validated in Phase 2: OpenRouter Text Adapter
- ✓ `gemini-3.1-flash-image-preview` hardened as default with clear docs — Validated in Phase 3: Deploy Readiness and OSS Hardening
- ✓ Deploy readiness: clean credentials, error guidance, .env.example complete — Validated in Phase 3: Deploy Readiness and OSS Hardening

### Out of Scope

- Native Stable Diffusion / DALL-E image generation — different SDK entirely; out of scope for v1.0
- Web UI or dashboard — CLI/skill interface is the contract; GUI adds scope creep
- Video/animation output — static infographics only for v1.0

## Context

- Stack: Python 3.8+, matplotlib, google-genai SDK, Pillow, numpy, Playwright
- Pretty mode routes between AI Studio (INFG_API_KEY) and Vertex AI (INFG_VERTEX_PROJECT + ADC)
- AI-Studio-only models (like `gemini-3.1-flash-image-preview`) are hard-coded in `_AI_STUDIO_ONLY` list
- OpenRouter uses an OpenAI-compatible API (`openai` Python package or `requests`)
- The skill is invoked from Claude Code via SKILL.md; all scripts are called via Bash
- OSS prep was completed in quick tasks (Mar 2026) — ready to publish pending model flexibility

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
| Playwright for HTML→PNG | Required for text-model (non-image) Gemini output | — Pending review |
| OpenRouter via OpenAI-compatible API | Gives access to 100+ LLMs with one integration | ✓ Shipped — `requests.post()`, slash validation, 401/402 errors, token counts |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-24 — Phase 3 complete: Deploy Readiness and OSS Hardening delivered — all v1.0 phases complete*
