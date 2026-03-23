# Roadmap: Infographic Skill

## Overview

v1.0 adds multi-provider LLM support to the infographic skill, making it production-ready for OSS deployment. Three phases deliver this in dependency order: first the provider resolver and env var wiring (everything else depends on it), then the OpenRouter text adapter (the user-facing capability), then a deploy readiness audit that hardens security and docs before publish.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Provider Resolution Infrastructure** - Wire env vars, rename existing text function, and build the resolver that dispatches between Gemini and OpenRouter (completed 2026-03-23)
- [x] **Phase 2: OpenRouter Text Adapter** - Implement the OpenRouter HTTP adapter, error handling, model validation, and cost reporting (completed 2026-03-23)
- [ ] **Phase 3: Deploy Readiness and OSS Hardening** - Extend key redaction, audit .env.example completeness, update docs, and verify offline mode

## Phase Details

### Phase 1: Provider Resolution Infrastructure
**Goal**: Users and scripts can configure LLM provider and model via env vars and CLI flags, with all existing Gemini paths working identically
**Depends on**: Nothing (first phase)
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, OROUTER-05
**Success Criteria** (what must be TRUE):
  1. User can set `INFG_LLM_PROVIDER=openrouter` in `.env` and the script routes text generation to the OpenRouter branch (even if it stubs to NotImplementedError at this phase)
  2. User can set `INFG_IMAGE_MODEL` to override the default image model without touching code
  3. User can pass `--llm-provider` and `--llm-model` CLI flags and they take precedence over env vars
  4. Existing users with only `INFG_API_KEY` or `INFG_VERTEX_PROJECT` set see no behavior change — Gemini routes as before
  5. `.env.example` contains entries for all new env vars (`INFG_LLM_PROVIDER`, `INFG_LLM_MODEL`, `INFG_LLM_API_KEY`, `INFG_OPENROUTER_API_KEY`, `INFG_IMAGE_MODEL`) with descriptions
**Plans:** 1/1 plans complete
Plans:
- [x] 01-01-PLAN.md — Wire provider resolver, env vars, CLI flags, function rename into generate_pretty.py + update .env.example

### Phase 2: OpenRouter Text Adapter
**Goal**: Users can generate infographics via the HTML-output path using any LLM on OpenRouter, with clear errors and token cost reporting
**Depends on**: Phase 1
**Requirements**: OROUTER-01, OROUTER-02, OROUTER-03, OROUTER-04
**Success Criteria** (what must be TRUE):
  1. User can run the HTML-output path with `INFG_LLM_PROVIDER=openrouter` and a valid OpenRouter key and receive a generated infographic
  2. User with an invalid OpenRouter key sees a clear error message identifying the key as invalid (401), not a raw stack trace
  3. User with an insufficient-credits account sees a clear message indicating billing action is needed (402)
  4. User who sets `INFG_LLM_MODEL` to a value without a slash (e.g. `gpt-4o` instead of `openai/gpt-4o`) sees a validation error with the correct format before any API call is made
  5. User sees input and output token counts in the cost report section after a successful OpenRouter run
**Plans:** 1/1 plans complete
Plans:
- [x] 02-01-PLAN.md — Implement _call_openrouter_text_mode, model validation, error handling, cost report, and pytest unit tests

### Phase 3: Deploy Readiness and OSS Hardening
**Goal**: The skill is safe to publish publicly — no API key leakage in output, all env vars documented, docs accurate, offline path isolated from optional packages
**Depends on**: Phase 2
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04
**Success Criteria** (what must be TRUE):
  1. An OpenRouter API key appearing in an error message or traceback is redacted to `sk-or-v1-[REDACTED]` matching the existing Google key redaction behavior
  2. Every env var consumed by `os.environ.get()` across all scripts has a corresponding entry in `.env.example`
  3. SKILL.md and README.md contain an OpenRouter setup section and correctly state Python 3.9+ as the minimum version
  4. Running the matplotlib offline path with the `openai` package uninstalled completes without `ImportError`
**Plans:** 1 plan
Plans:
- [ ] 03-01-PLAN.md — Extend key redaction, add openai import guard, update docs with OpenRouter setup and Python 3.9+, full test coverage

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Provider Resolution Infrastructure | 1/1 | Complete    | 2026-03-23 |
| 2. OpenRouter Text Adapter | 1/1 | Complete   | 2026-03-23 |
| 3. Deploy Readiness and OSS Hardening | 0/1 | Not started | - |
