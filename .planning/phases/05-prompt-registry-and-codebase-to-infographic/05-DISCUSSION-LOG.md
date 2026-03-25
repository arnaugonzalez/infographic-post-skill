# Phase 5: Prompt Registry and Codebase-to-Infographic - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 05-prompt-registry-and-codebase-to-infographic
**Areas discussed:** Registry shape, --codebase mapping, Unrecognized model fallback

---

## Registry Shape

### Entry contents

| Option | Description | Selected |
|--------|-------------|----------|
| Structural constraints only | supports_icons, context_window, style_vocabulary, last_verified — no prompt text | |
| Constraints + prompt fragments | Same + model-specific prompt snippets; registry is single source of truth | ✓ |
| Minimal — icons + last_verified only | Just boolean + date; keep context_window/vocabulary out | |

**User's choice:** Constraints + prompt fragments
**Notes:** Registry should be the single source of truth for all model-specific prompt content, including icon guide text.

---

### Registry keys

| Option | Description | Selected |
|--------|-------------|----------|
| gemini only | One entry; no stubs | |
| gemini + stubs for dalle/sd | Three keys; dalle and sd have placeholder entries | ✓ |
| Per-version (gemini-2.5, gemini-3) | More granular; higher maintenance | |

**User's choice:** gemini + empty stubs for dalle/sd

---

## --codebase Mapping

### Infographic type and field mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Arch type, layers direct-map | viz_type='arch'; layers→layers, summary→description | ✓ |
| Dashboard type | Uses file_count, signal counts as KPI metrics | |
| Auto-detect by content | arch if layers non-empty, dashboard otherwise | |

**User's choice:** Arch type, layers direct-map

---

### Title derivation

| Option | Description | Selected |
|--------|-------------|----------|
| Dir name, title-cased | e.g. ./infographic-skill → "Infographic Skill" | ✓ |
| From summary (first sentence) | More descriptive; depends on summary quality | |
| Static: 'Codebase Architecture' | Generic; same every time | |

**User's choice:** Dir name, title-cased

---

### Integration method

| Option | Description | Selected |
|--------|-------------|----------|
| Import read_codebase directly | sys.path insert pattern; same as generate_linkedin_arch | ✓ |
| Subprocess, parse JSON | Decoupled; process overhead + tmp file | |

**User's choice:** Import directly

---

## Unrecognized Model Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Print warning, use gemini entry | ⚠️ warn + continue with gemini strategy | ✓ |
| Print warning, use no-icons defaults | Safe minimum; no wrong model content injected | |
| Print warning and exit | Strict; forces user to update registry | |

**User's choice:** Print warning, use gemini entry

---

## Claude's Discretion

- Staleness threshold for `last_verified` warnings (not discussed)
- Exact family extraction from full model string

## Deferred Ideas

None
