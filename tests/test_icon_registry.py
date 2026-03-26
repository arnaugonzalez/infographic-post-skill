"""Tests for scripts/icon_registry.py."""

from __future__ import annotations

import re
import sys
import types
from unittest import mock

import pytest

sys.path.insert(0, "scripts")
from icon_registry import (  # noqa: E402
    _ALIAS_MAP,
    _EMOJI_FALLBACK,
    _extract_path,
    _normalize_slug,
    get_icon_svg,
)


# ── _normalize_slug ──────────────────────────────────────────────────────

class TestNormalizeSlug:
    """Edge-cases for slug normalisation."""

    def test_alias_hit_react(self):
        assert _normalize_slug("React") == "react"

    def test_alias_nextjs(self):
        assert _normalize_slug("Next.js") == "nextdotjs"

    def test_alias_nodejs(self):
        assert _normalize_slug("Node.js") == "nodedotjs"

    def test_alias_vuejs(self):
        assert _normalize_slug("Vue.js") == "vuedotjs"

    def test_dot_replacement(self):
        """Dots are replaced with 'dot' for names not in the alias map."""
        assert _normalize_slug("Some.lib") == "somedotlib"

    def test_strip_whitespace(self):
        assert _normalize_slug("  react  ") == "react"

    def test_special_chars_stripped(self):
        assert _normalize_slug("C++") == "c"

    def test_spaces_removed(self):
        # "Tailwind CSS" is in alias map → tailwindcss
        assert _normalize_slug("Tailwind CSS") == "tailwindcss"

    def test_unknown_with_spaces(self):
        # Not in alias map → programmatic normalisation
        assert _normalize_slug("My Cool Lib") == "mycoollib"


# ── _extract_path ────────────────────────────────────────────────────────

class TestExtractPath:
    def test_extracts_d_attribute(self):
        svg = '<svg><path d="M0 0L10 10Z"/></svg>'
        assert _extract_path(svg) == "M0 0L10 10Z"

    def test_returns_empty_on_no_match(self):
        assert _extract_path("<svg></svg>") == ""


# ── get_icon_svg — real simplepycons ─────────────────────────────────────

class TestGetIconSvgReal:
    """Integration tests using the real simplepycons library."""

    @pytest.mark.parametrize("tech", ["React", "Docker", "PostgreSQL", "FastAPI"])
    def test_known_icons_return_svg(self, tech: str):
        result = get_icon_svg(tech)
        assert result.startswith("<svg ")
        assert 'viewBox="0 0 24 24"' in result
        assert "<path d=" in result
        assert 'fill="#' in result

    def test_svg_respects_size(self):
        result = get_icon_svg("React", size=32)
        assert 'width="32"' in result
        assert 'height="32"' in result

    def test_default_size_is_20(self):
        result = get_icon_svg("React")
        assert 'width="20"' in result

    @pytest.mark.parametrize(
        "name,expected_slug",
        [
            ("Next.js", "nextdotjs"),
            ("Node.js", "nodedotjs"),
            ("Vue.js", "vuedotjs"),
        ],
    )
    def test_alias_resolution_produces_svg(self, name: str, expected_slug: str):
        result = get_icon_svg(name)
        assert result.startswith("<svg "), f"Expected SVG for {name}, got: {result}"


# ── get_icon_svg — emoji fallbacks ───────────────────────────────────────

class TestGetIconSvgFallback:
    """Test emoji fallback when icon is not found."""

    def test_unknown_tech_returns_emoji_span(self):
        result = get_icon_svg("TotallyMadeUpTech12345")
        assert "<span " in result
        assert "font-size:" in result

    def test_unknown_tech_uses_default_emoji(self):
        result = get_icon_svg("TotallyMadeUpTech12345")
        assert "🔧" in result

    def test_emoji_fallback_docker_when_simplepycons_unavailable(self):
        """Simulate simplepycons being unavailable."""
        with mock.patch.dict("sys.modules", {"simplepycons": None}):
            # Force ImportError by making import fail
            with mock.patch(
                "builtins.__import__",
                side_effect=_import_blocker("simplepycons"),
            ):
                result = get_icon_svg("Docker")
                assert "🐳" in result
                assert "<span " in result

    @pytest.mark.parametrize(
        "tech,emoji",
        [
            ("docker", "🐳"),
            ("python", "🐍"),
            ("github", "🐙"),
            ("aws", "☁️"),
            ("firebase", "🔥"),
        ],
    )
    def test_emoji_map_entries(self, tech: str, emoji: str):
        """Verify _EMOJI_FALLBACK contains expected entries."""
        assert _EMOJI_FALLBACK.get(tech) == emoji


# ── Alias map coverage ───────────────────────────────────────────────────

class TestAliasMapCoverage:
    """Verify the alias map has entries for all required technologies."""

    REQUIRED_KEYS = [
        "react", "react native", "next.js", "vue", "vue.js", "angular",
        "svelte", "tailwind css", "typescript", "javascript", "html5",
        "css3", "vite", "webpack", "expo",
        "fastapi", "django", "flask", "node.js", "nestjs", "express",
        "spring", "go", "rust", "ruby on rails", "laravel", ".net",
        "postgresql", "mysql", "mongodb", "redis", "sqlite", "supabase",
        "firebase", "cassandra", "dynamodb", "drizzle orm",
        "docker", "kubernetes", "aws", "google cloud", "azure",
        "terraform", "github", "github actions", "gitlab", "vercel",
        "netlify", "cloudflare", "nginx", "railway",
        "openai", "langchain", "anthropic", "hugging face", "pytorch",
        "tensorflow",
        "auth0", "clerk",
        "kafka", "rabbitmq", "celery",
        "python", "playwright", "numpy", "pandas", "elasticsearch",
        "grafana", "prometheus", "sentry",
    ]

    @pytest.mark.parametrize("key", REQUIRED_KEYS)
    def test_key_in_alias_map(self, key: str):
        assert key in _ALIAS_MAP, f"Missing alias map entry: {key!r}"


# ── helpers ──────────────────────────────────────────────────────────────

def _import_blocker(blocked_module: str):
    """Return a side_effect function that blocks *blocked_module* imports."""
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def _blocker(name, *args, **kwargs):
        if name == blocked_module or name.startswith(f"{blocked_module}."):
            raise ImportError(f"Mocked: {name} not available")
        return real_import(name, *args, **kwargs)

    return _blocker
