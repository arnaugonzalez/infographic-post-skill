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
    "gpt-4o-mini": 2,           # 'gpt-4o' substring hits tier 1, but mini is tier 2
    "claude-3.5-haiku": 2,      # 'claude-3.5' substring could hit tier 1
}

_QUALITY_TIER_1: frozenset[str] = frozenset({
    # Flagship models — best at structured HTML, design fidelity, and following
    # complex layout constraints.  Low hallucination on tech names.
    "claude-sonnet-4",
    "claude-3.5-sonnet",
    "claude-3-5-sonnet",
    "claude-opus-4",
    "gpt-4o",
    "gpt-4-turbo",
    "gemini-2.5-pro",
    "gemini-3-pro",
    "gemini-3.1-pro",
})

_QUALITY_TIER_3: frozenset[str] = frozenset({
    # Small / cheap / old models — known issues: preamble leakage, sparse layouts,
    # hallucinated tech names, poor HTML structure, missing sections.
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
            f"   Model '{model}' is classified as tier 3 (budget/small model).\n"
            f"   Known issues with this tier:\n"
            f"     • Preamble text leaking into the output\n"
            f"     • Sparse/empty layouts with wasted space\n"
            f"     • Hallucinated technology names\n"
            f"     • Missing sections, icons, or design elements\n"
            f"\n"
            f"   💡 For publication-quality {context}s, use a tier-1 model:\n"
            f"      INFG_LLM_MODEL=anthropic/claude-sonnet-4-20250514\n"
            f"      INFG_LLM_MODEL=google/gemini-2.5-pro\n"
            f"      INFG_LLM_MODEL=openai/gpt-4o\n",
            file=sys.stderr,
        )
    elif tier == 2:
        print(
            f"ℹ️  Model '{model}' is tier 2 (mid-range) — "
            f"results are usually good but may need minor cleanup.\n"
            f"   Upgrade to a tier-1 model for best results: "
            f"claude-sonnet-4, gemini-2.5-pro, or gpt-4o.",
            file=sys.stderr,
        )
