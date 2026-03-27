"""Model quality tier classification and CLI warnings.

Classifies LLM models into three quality tiers for infographic generation:
  Tier 1 — Flagship models (best structured HTML, layout fidelity, no hallucination)
  Tier 2 — Mid-range (usually good, occasional issues)
  Tier 3 — Budget/small (sparse layouts, preamble leaks, hallucinated tech names)

Usage:
    from model_quality import classify_model_quality, quality_warning
    tier = classify_model_quality("meta-llama/llama-3.3-70b-instruct")
    quality_warning("meta-llama/llama-3.3-70b-instruct", tier)
"""
from __future__ import annotations

import sys

# ── Tier definitions ──────────────────────────────────────────────────────────
# Substring-based matching: 'anthropic/claude-sonnet-4' matches 'claude-sonnet-4'.
# IMPORTANT: More specific patterns (e.g. 'gpt-4o-mini') are checked before
# less specific ones (e.g. 'gpt-4o') via _QUALITY_TIER_OVERRIDES to avoid
# false positives from substring matching.

# Models that would match a tier-1 pattern but belong to a lower tier.
_QUALITY_TIER_OVERRIDES: dict[str, int] = {
    "gpt-5.2-mini": 2,          # mini variants are tier 2
    "gemini-2.5-flash-lite": 3, # lite variants are tier 3
    "gemini-3-flash": 2,        # flash is tier 2, not tier 1 like pro
}

_QUALITY_TIER_1: frozenset[str] = frozenset({
    # Flagship models — best at structured output, design fidelity, and following
    # complex layout constraints.  Low hallucination on tech names.
    # Updated March 2026 from OpenRouter rankings + model pages.
    "claude-opus-4.6",
    "claude-opus-4.5",
    "claude-sonnet-4.6",
    "claude-sonnet-4.5",
    "gpt-5.4",
    "gpt-5.3",
    "gpt-5.2",
    "gemini-3.1-pro",
    "gemini-3-pro",
    "gemini-2.5-pro",
    "mimo-v2-pro",
    "glm-5",
    "minimax-m2.7",
    "deepseek-v3.2",
})

_QUALITY_TIER_3: frozenset[str] = frozenset({
    # Small / cheap / old models — known issues: preamble leakage, sparse layouts,
    # hallucinated tech names, poor structure, missing sections.
    # Updated March 2026.
    "llama-3.3-70b",
    "llama-3.1-70b",
    "llama-3.1-8b",
    "llama-3-70b",
    "llama-3-8b",
    "llama-2",
    "mistral-small",
    "mistral-7b",
    "mixtral-8x7b",
    "phi-4",
    "phi-3",
    "qwen-2.5-72b",
    "qwen-2.5-7b",
    "gemma-2",
    "gemma-3",
    "deepseek-r1-distill",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    # Legacy models (pre-2026)
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "claude-sonnet-4",
    "claude-3.5-sonnet",
    "claude-haiku-3.5",
})

# Tier 2 (mid-range — decent quality, occasional issues):
# gemini-2.0-flash, gemini-2.5-flash, claude-haiku-4-5, deepseek-chat-v3,
# gpt-4o-mini, and anything not explicitly listed above.


def classify_model_quality(model: str) -> int:
    """Return quality tier (1=best, 2=mid, 3=low) for the given model.

    Matching is substring-based: 'anthropic/claude-sonnet-4' matches 'claude-sonnet-4'.
    Overrides are checked first to handle cases like 'gpt-4o-mini' (tier 2)
    that would otherwise match 'gpt-4o' (tier 1).
    """
    name = model.lower().replace("models/", "")
    # Strip OpenRouter provider prefix (e.g. "meta-llama/" or "anthropic/")
    if "/" in name:
        name = name.split("/", 1)[1]

    # Check explicit overrides first (more specific patterns)
    for pattern, tier in _QUALITY_TIER_OVERRIDES.items():
        if pattern in name:
            return tier

    for pattern in _QUALITY_TIER_1:
        if pattern in name:
            return 1
    for pattern in _QUALITY_TIER_3:
        if pattern in name:
            return 3
    return 2


def quality_warning(model: str, tier: int, context: str = "infographic") -> None:
    """Print a quality advisory to stderr based on the model's tier.

    Parameters
    ----------
    model   : Full model identifier (e.g. 'meta-llama/llama-3.3-70b-instruct')
    tier    : Quality tier from classify_model_quality()
    context : What is being generated — 'infographic' or 'posts'
    """
    if tier == 3:
        print(
            f"\n⚠️  LOW-QUALITY MODEL WARNING\n"
            f"   Model '{model}' is classified as tier 3 (budget/small/legacy model).\n"
            f"   Known issues with this tier:\n"
            f"     • Preamble text leaking into the output\n"
            f"     • Sparse/empty layouts with wasted space\n"
            f"     • Hallucinated technology names\n"
            f"     • Missing sections, icons, or design elements\n"
            f"\n"
            f"   💡 For publication-quality {context}s, use a tier-1 model:\n"
            f"      INFG_LLM_MODEL=anthropic/claude-sonnet-4.6\n"
            f"      INFG_LLM_MODEL=google/gemini-2.5-pro\n"
            f"      INFG_LLM_MODEL=openai/gpt-5.2\n"
            f"      INFG_LLM_MODEL=deepseek/deepseek-v3.2\n",
            file=sys.stderr,
        )
    elif tier == 2:
        print(
            f"ℹ️  Model '{model}' is tier 2 (mid-range) — "
            f"results are usually good but may need minor cleanup.\n"
            f"   Upgrade to a tier-1 model for best results: "
            f"claude-sonnet-4.6, gemini-2.5-pro, gpt-5.2, or deepseek-v3.2.",
            file=sys.stderr,
        )
