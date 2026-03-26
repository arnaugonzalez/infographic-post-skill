"""Tests for scripts/content_structurer.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from content_structurer import _strip_json_fences, structure_codebase, LAYER_PALETTE


# ── _strip_json_fences ────────────────────────────────────────────────────────


class TestStripJsonFences:
    """Tests for _strip_json_fences helper."""

    def test_plain_json_unchanged(self):
        raw = '{"title": "Test"}'
        assert _strip_json_fences(raw) == '{"title": "Test"}'

    def test_strips_markdown_fences(self):
        raw = '```json\n{"title": "Test"}\n```'
        assert json.loads(_strip_json_fences(raw)) == {"title": "Test"}

    def test_strips_preamble_text(self):
        raw = 'Here is the JSON output:\n\n{"layers": []}'
        assert json.loads(_strip_json_fences(raw)) == {"layers": []}

    def test_strips_trailing_text(self):
        raw = '{"title": "X"}\n\nLet me know if you need changes!'
        assert json.loads(_strip_json_fences(raw)) == {"title": "X"}

    def test_strips_preamble_and_trailing(self):
        raw = 'Sure! Here you go:\n```json\n{"a": 1}\n```\nHope this helps.'
        assert json.loads(_strip_json_fences(raw)) == {"a": 1}

    def test_whitespace_only(self):
        raw = "   \n  "
        # No braces → returns stripped string
        result = _strip_json_fences(raw)
        assert result == ""

    def test_nested_braces(self):
        obj = {"layers": [{"label": "FE", "items": [{"name": "React"}]}]}
        raw = f"```\n{json.dumps(obj)}\n```"
        assert json.loads(_strip_json_fences(raw)) == obj


# ── Valid JSON response ───────────────────────────────────────────────────────

_VALID_RESPONSE = json.dumps({
    "title": "MyProject",
    "subtitle": "Technical Architecture Overview",
    "layers": [
        {
            "label": "FRONTEND",
            "items": [
                {"name": "React", "description": "UI framework"},
                {"name": "TypeScript", "description": "Type-safe code"},
            ],
        },
        {
            "label": "BACKEND",
            "items": [
                {"name": "Node.js", "description": "API server"},
            ],
        },
    ],
    "connections": [
        {"from_layer": 0, "to_layer": 1, "label": "REST API"},
    ],
    "footer_cta": "Follow for more",
    "footer_summary": "A sample project",
})

_SAMPLE_REPORT = {"summary_text": "Project uses React and Node.js"}


class TestStructureCodebase:
    """Tests for structure_codebase with mocked API calls."""

    @patch("content_structurer._call_openrouter", return_value=_VALID_RESPONSE)
    def test_valid_json_returns_parsed_dict(self, mock_call):
        result = structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test")
        assert result["title"] == "MyProject"
        assert len(result["layers"]) == 2
        assert result["layers"][0]["label"] == "FRONTEND"
        assert len(result["layers"][0]["items"]) == 2
        mock_call.assert_called_once()

    @patch("content_structurer._call_openrouter")
    def test_json_with_markdown_fences_parses(self, mock_call):
        fenced = f"```json\n{_VALID_RESPONSE}\n```"
        mock_call.return_value = fenced
        result = structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test")
        assert result["title"] == "MyProject"
        assert len(result["layers"]) == 2

    @patch("content_structurer._call_openrouter")
    def test_validates_required_layers_key(self, mock_call):
        # Response missing 'layers'
        mock_call.return_value = json.dumps({"title": "X"})
        with pytest.raises(SystemExit):
            structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test", max_retries=0)

    @patch("content_structurer._call_openrouter")
    def test_validates_required_title_key(self, mock_call):
        # Response missing 'title'
        mock_call.return_value = json.dumps({"layers": [{"label": "FE", "items": []}]})
        with pytest.raises(SystemExit):
            structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test", max_retries=0)

    @patch("content_structurer._call_openrouter")
    def test_validates_layers_must_be_list(self, mock_call):
        mock_call.return_value = json.dumps({"title": "X", "layers": "not-a-list"})
        with pytest.raises(SystemExit):
            structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test", max_retries=0)

    @patch("content_structurer._call_openrouter")
    def test_sets_defaults_for_missing_optional_keys(self, mock_call):
        minimal = json.dumps({
            "title": "Minimal",
            "layers": [{"label": "APP", "items": [{"name": "Go", "description": "Main language"}]}],
        })
        mock_call.return_value = minimal
        result = structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test")
        assert result["subtitle"] == "Technical Architecture Overview"
        assert result["connections"] == []
        assert result["footer_cta"] == "Follow for more software architecture content"
        assert result["footer_summary"] == ""

    @patch("content_structurer._call_openrouter")
    def test_retries_on_json_parse_failure(self, mock_call):
        # First call returns garbage, second returns valid JSON
        mock_call.side_effect = [
            "This is not JSON at all!!! no braces here",
            _VALID_RESPONSE,
        ]
        result = structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test", max_retries=1)
        assert result["title"] == "MyProject"
        assert mock_call.call_count == 2

    @patch("content_structurer._call_openrouter")
    def test_exits_after_exhausting_retries(self, mock_call):
        mock_call.return_value = "totally broken output with no json"
        with pytest.raises(SystemExit):
            structure_codebase(_SAMPLE_REPORT, model="test/model", api_key="sk-test", max_retries=1)
        # Called original + 1 retry = 2 total
        assert mock_call.call_count == 2

    def test_exits_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True), \
             patch("content_structurer._load_dotenv"):
            with pytest.raises(SystemExit):
                structure_codebase(_SAMPLE_REPORT, model="test/model")

    @patch("content_structurer._call_openrouter", return_value=_VALID_RESPONSE)
    def test_uses_summary_text_from_report(self, mock_call):
        report = {"summary_text": "Custom summary content"}
        structure_codebase(report, model="test/model", api_key="sk-test")
        prompt_arg = mock_call.call_args[0][0]
        assert "Custom summary content" in prompt_arg

    @patch("content_structurer._call_openrouter", return_value=_VALID_RESPONSE)
    def test_falls_back_to_json_dump_without_summary_text(self, mock_call):
        report = {"project_name": "foo", "languages": ["Python"]}
        structure_codebase(report, model="test/model", api_key="sk-test")
        prompt_arg = mock_call.call_args[0][0]
        assert "foo" in prompt_arg
        assert "Python" in prompt_arg


# ── Module-level constants ────────────────────────────────────────────────────


class TestConstants:
    def test_layer_palette_has_eight_colors(self):
        assert len(LAYER_PALETTE) == 8

    def test_palette_colors_are_hex(self):
        import re
        for color in LAYER_PALETTE:
            assert re.match(r"^#[0-9A-Fa-f]{6}$", color), f"Invalid hex color: {color}"
