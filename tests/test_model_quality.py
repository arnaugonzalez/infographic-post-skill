"""Tests for scripts/model_quality.py — quality tier classification and warnings."""
from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pytest

# Ensure scripts/ is on sys.path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from model_quality import classify_model_quality, quality_warning


# ── classify_model_quality ────────────────────────────────────────────────────

class TestClassifyModelQuality:
    """Tier classification tests — tier 1, 2, 3 for various model strings."""

    # Tier 1 — flagship models
    @pytest.mark.parametrize("model", [
        "anthropic/claude-sonnet-4.6",
        "anthropic/claude-opus-4.6",
        "openai/gpt-5.2",
        "openai/gpt-5.4",
        "google/gemini-2.5-pro",
        "gemini-3-pro-preview",
        "gemini-3.1-pro-preview",
        "deepseek/deepseek-v3.2",
        "xiaomi/mimo-v2-pro",
    ])
    def test_tier_1_flagship(self, model: str) -> None:
        assert classify_model_quality(model) == 1

    # Tier 3 — budget / small / legacy models
    @pytest.mark.parametrize("model", [
        "meta-llama/llama-3.3-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct",
        "mistralai/mixtral-8x7b-instruct",
        "microsoft/phi-4",
        "google/gemma-3-27b-it",
        "deepseek/deepseek-r1-distill-llama-70b",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-lite",
        "qwen/qwen-2.5-72b-instruct",
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4",
    ])
    def test_tier_3_budget(self, model: str) -> None:
        assert classify_model_quality(model) == 3

    # Tier 2 — mid-range (default)
    @pytest.mark.parametrize("model", [
        "google/gemini-3-flash-preview",
        "google/gemini-2.5-flash",
        "stepfun/step-3.5-flash",
        "anthropic/claude-haiku-4.5",
        "some-unknown/model-xyz",
    ])
    def test_tier_2_midrange(self, model: str) -> None:
        assert classify_model_quality(model) == 2

    def test_strips_models_prefix(self) -> None:
        """models/ prefix (Gemini SDK format) should be stripped before matching."""
        assert classify_model_quality("models/gemini-2.5-pro") == 1
        assert classify_model_quality("models/gemini-2.0-flash-lite") == 3


# ── quality_warning ──────────────────────────────────────────────────────────

class TestQualityWarning:
    """Warning output tests — tier 3 warns, tier 2 advises, tier 1 is silent."""

    def test_tier_3_prints_warning(self) -> None:
        """Tier 3 should print a multi-line LOW-QUALITY warning to stderr."""
        buf = StringIO()
        old_stderr = sys.stderr
        sys.stderr = buf
        try:
            quality_warning("meta-llama/llama-3.3-70b-instruct", 3)
        finally:
            sys.stderr = old_stderr
        output = buf.getvalue()
        assert "LOW-QUALITY MODEL WARNING" in output
        assert "tier 3" in output
        assert "tier-1 model" in output
        assert "claude-sonnet-4.6" in output

    def test_tier_2_prints_info(self) -> None:
        """Tier 2 should print a brief info message to stderr."""
        buf = StringIO()
        old_stderr = sys.stderr
        sys.stderr = buf
        try:
            quality_warning("google/gemini-2.0-flash-001", 2)
        finally:
            sys.stderr = old_stderr
        output = buf.getvalue()
        assert "tier 2" in output
        assert "mid-range" in output

    def test_tier_1_silent(self) -> None:
        """Tier 1 should print nothing — no warning needed."""
        buf = StringIO()
        old_stderr = sys.stderr
        sys.stderr = buf
        try:
            quality_warning("anthropic/claude-sonnet-4", 1)
        finally:
            sys.stderr = old_stderr
        assert buf.getvalue() == ""

    def test_context_param_in_message(self) -> None:
        """The context parameter should appear in the tier 3 warning."""
        buf = StringIO()
        old_stderr = sys.stderr
        sys.stderr = buf
        try:
            quality_warning("meta-llama/llama-3.3-70b-instruct", 3, context="post")
        finally:
            sys.stderr = old_stderr
        output = buf.getvalue()
        assert "publication-quality posts" in output


# ── _strip_fences (imported from generate_pretty) ────────────────────────────

class TestStripFences:
    """Test that _strip_fences handles preamble text before code fences."""

    @pytest.fixture(autouse=True)
    def _import_strip_fences(self):
        from generate_pretty import _strip_fences
        self._strip_fences = _strip_fences

    def test_clean_html_passthrough(self) -> None:
        html = "<html><body>Hello</body></html>"
        assert self._strip_fences(html) == html

    def test_strips_fences_at_start(self) -> None:
        raw = "```html\n<html><body>Hello</body></html>\n```"
        assert self._strip_fences(raw) == "<html><body>Hello</body></html>"

    def test_strips_preamble_before_fence(self) -> None:
        """LLM preamble before ```html should be stripped."""
        raw = (
            "Here's the production-ready HTML file that meets the specifications. "
            'Here is the code: ```html\n'
            "<html><body>Hello</body></html>\n"
            "```"
        )
        assert self._strip_fences(raw) == "<html><body>Hello</body></html>"

    def test_strips_multiline_preamble(self) -> None:
        """Multi-line preamble before the code fence should be stripped."""
        raw = (
            "Based on the design requirements provided, I'll create a\n"
            "production-ready HTML file.\n\n"
            "```html\n"
            "<html><body>Content</body></html>\n"
            "```"
        )
        assert self._strip_fences(raw) == "<html><body>Content</body></html>"

    def test_no_fence_returns_raw(self) -> None:
        """If there's no code fence, return the raw string as-is."""
        raw = "<html><body>Direct HTML</body></html>"
        assert self._strip_fences(raw) == raw
