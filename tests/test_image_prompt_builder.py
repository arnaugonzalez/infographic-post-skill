"""Tests for scripts/image_prompt_builder.py"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from image_prompt_builder import (
    INFOGRAPHIC_TYPES,
    _describe_brand_icon,
    build_image_prompt,
)

# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_DATA = {
    "title": "Knowy App",
    "subtitle": "AI-Powered Journal Architecture",
    "layers": [
        {
            "label": "FRONTEND",
            "color": "#3B82F6",
            "items": [
                {"name": "React Native", "description": "Cross-platform mobile SDK"},
                {"name": "Expo", "description": "Build pipeline"},
            ],
        },
        {
            "label": "BACKEND",
            "color": "#F59E0B",
            "items": [
                {"name": "FastAPI", "description": "Async Python API"},
                {"name": "LangChain", "description": "Agent orchestration"},
            ],
        },
        {
            "label": "DATABASE",
            "color": "#10B981",
            "items": [
                {"name": "Supabase", "description": "PostgreSQL + Auth"},
                {"name": "Redis", "description": "Cache layer"},
            ],
        },
    ],
    "connections": [
        {"from_layer": 0, "to_layer": 1, "label": "REST API"},
        {"from_layer": 1, "to_layer": 2, "label": "SQL queries"},
    ],
    "footer_cta": "Follow for more architecture content",
    "footer_summary": "AI journal · Offline-first · Supabase PostgreSQL",
}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBuildImagePrompt:
    """Main public API tests."""

    @pytest.mark.parametrize("infographic_type", list(INFOGRAPHIC_TYPES.keys()))
    def test_returns_nonempty_string(self, infographic_type: str) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, infographic_type)
        assert isinstance(prompt, str)
        assert len(prompt) > 200

    @pytest.mark.parametrize("infographic_type", list(INFOGRAPHIC_TYPES.keys()))
    def test_includes_title(self, infographic_type: str) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, infographic_type)
        assert "Knowy App" in prompt

    def test_includes_tech_names(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "architecture")
        assert "React Native" in prompt
        assert "FastAPI" in prompt
        assert "Supabase" in prompt

    def test_includes_brand_icon_descriptions(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "architecture")
        assert "atomic orbital" in prompt  # React Native icon
        assert "lightning bolt" in prompt or "teal diamond" in prompt  # FastAPI icon

    def test_includes_connections(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "architecture")
        assert "REST API" in prompt
        assert "SQL queries" in prompt

    def test_includes_style_constraints(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "architecture")
        assert "PIXEL-PERFECT" in prompt
        assert "NOT a sketch" in prompt

    def test_includes_1080_dimension(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "architecture")
        assert "1080" in prompt

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown infographic type"):
            build_image_prompt(SAMPLE_DATA, "invalid_type")

    @pytest.mark.parametrize("style", ["modern-dark", "modern-light", "illustrated"])
    def test_style_presets(self, style: str) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "architecture", style=style)
        assert len(prompt) > 200

    def test_different_types_produce_different_prompts(self) -> None:
        arch = build_image_prompt(SAMPLE_DATA, "architecture")
        comp = build_image_prompt(SAMPLE_DATA, "comparison")
        feat = build_image_prompt(SAMPLE_DATA, "feature")
        # Each should have unique structural markers
        assert "ARCHITECTURE DIAGRAM" in arch or "architecture" in arch.lower()
        assert "split-screen" in comp.lower() or "comparison" in comp.lower()
        assert "step" in feat.lower() or "STEP" in feat

    def test_comparison_uses_two_columns(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "comparison")
        assert "LEFT" in prompt or "left" in prompt.lower()
        assert "RIGHT" in prompt or "right" in prompt.lower()

    def test_cheatsheet_encourages_saving(self) -> None:
        prompt = build_image_prompt(SAMPLE_DATA, "cheatsheet")
        assert "save" in prompt.lower() or "SAVE" in prompt


class TestDescribeBrandIcon:
    """Brand icon description lookup tests."""

    @pytest.mark.parametrize(
        "tech,expected_fragment",
        [
            ("React", "atomic orbital"),
            ("Docker", "whale"),
            ("PostgreSQL", "elephant"),
            ("FastAPI", "teal diamond"),
            ("Python", "snakes"),
            ("TypeScript", "TS"),
            ("Kubernetes", "wheel"),
            ("AWS", "swoosh"),
            ("GitHub", "octocat"),
            ("Supabase", "lightning"),
        ],
    )
    def test_known_icons(self, tech: str, expected_fragment: str) -> None:
        desc = _describe_brand_icon(tech)
        assert expected_fragment.lower() in desc.lower()

    def test_unknown_tech_fallback(self) -> None:
        desc = _describe_brand_icon("SomeUnknownFramework")
        assert "SomeUnknownFramework" in desc
        assert "icon" in desc.lower()

    def test_case_insensitive(self) -> None:
        desc1 = _describe_brand_icon("react")
        desc2 = _describe_brand_icon("React")
        desc3 = _describe_brand_icon("REACT")
        assert desc1 == desc2 == desc3

    def test_suffix_stripping(self) -> None:
        desc = _describe_brand_icon("Node.js")
        assert "node" in desc.lower() or "hexagonal" in desc.lower()
