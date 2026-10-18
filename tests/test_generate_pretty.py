"""
Tests for the _PROMPT_STRATEGIES prompt registry in generate_pretty.py.

Requirements: PROMPTREG-01, PROMPTREG-02, PROMPTREG-03
"""
import sys
from datetime import date

sys.path.insert(0, "scripts")

import generate_pretty
from generate_pretty import _PROMPT_STRATEGIES, _get_strategy, _model_family


class TestPromptRegistry:
    """Tests for the _PROMPT_STRATEGIES registry dict and helper functions."""

    def test_registry_has_required_families(self):
        """PROMPTREG-01: _PROMPT_STRATEGIES must have gemini, dalle, and sd keys."""
        assert "gemini" in _PROMPT_STRATEGIES
        assert "dalle" in _PROMPT_STRATEGIES
        assert "sd" in _PROMPT_STRATEGIES

    def test_supports_icons_removed(self):
        """D-03: _supports_icons must be removed from the module — registry is the new entry point."""
        assert not hasattr(generate_pretty, "_supports_icons"), (
            "_supports_icons must be removed; use _get_strategy() instead"
        )

    def test_get_strategy_gemini(self):
        """_get_strategy returns the gemini entry (supports_icons=True) for a gemini model."""
        result = _get_strategy("gemini-3.1-flash-image-preview")
        assert isinstance(result, dict)
        assert result["supports_icons"] is True

    def test_get_strategy_fallback(self, capsys):
        """D-09: _get_strategy falls back to gemini entry and prints warning for unknown model families."""
        result = _get_strategy("unknown-xyz")
        captured = capsys.readouterr()
        assert "Unrecognized model family" in captured.out
        # Should still return a valid strategy (the gemini fallback)
        assert isinstance(result, dict)
        assert "supports_icons" in result

    def test_registry_schema(self):
        """PROMPTREG-02: Every entry in _PROMPT_STRATEGIES must have exactly 5 required keys."""
        required_keys = {"supports_icons", "context_window", "style_vocabulary", "prompt_fragments", "last_verified"}
        for family, entry in _PROMPT_STRATEGIES.items():
            assert set(entry.keys()) == required_keys, (
                f"Entry '{family}' has keys {set(entry.keys())}, expected {required_keys}"
            )

    def test_last_verified_format(self):
        """PROMPTREG-03: Every entry's last_verified must parse as a valid ISO date."""
        for family, entry in _PROMPT_STRATEGIES.items():
            lv = entry["last_verified"]
            # Must not raise ValueError
            parsed = date.fromisoformat(lv)
            assert isinstance(parsed, date), f"Entry '{family}' last_verified '{lv}' did not parse as date"

    def test_gemini_prompt_fragments(self):
        """PROMPTREG-01: gemini entry prompt_fragments must have image_icon_guide and html_icon_guide."""
        fragments = _PROMPT_STRATEGIES["gemini"]["prompt_fragments"]
        assert "image_icon_guide" in fragments, "Missing image_icon_guide in gemini prompt_fragments"
        assert "html_icon_guide" in fragments, "Missing html_icon_guide in gemini prompt_fragments"
        assert len(fragments["image_icon_guide"]) > 100, "image_icon_guide is too short to be valid"
        assert len(fragments["html_icon_guide"]) > 100, "html_icon_guide is too short to be valid"

    def test_model_family_extraction(self):
        """_model_family must correctly classify model strings to family keys."""
        assert _model_family("gemini-3.1-flash-image-preview") == "gemini"
        assert _model_family("dall-e-3") == "dalle"
        assert _model_family("stable-diffusion-xl") == "sd"
        assert _model_family("unknown") == "unknown"


class TestCodebaseFlag:
    """Tests for the --codebase flag and CodebaseReport-to-config mapping."""

    def setup_method(self):
        """Standard mock CodebaseReport for testing mapping logic."""
        self.mock_report = {
            "root": "/tmp/test-project",
            "title": "test-project",
            "summary_text": "Test summary content",
            "layers": [
                {
                    "label": "Backend",
                    "category": "backend",
                    "items": ["app.py"],
                    "bg": "#1e3a5f",
                    "border": "#2196F3",
                    "label_color": "#fff",
                }
            ],
            "connections": [{"from": "A", "to": "B"}],
            "files_included": ["app.py"],
            "files_excluded": [],
            "token_estimate": 100,
            "format": "codebase",
        }

    def test_codebase_config_mapping(self):
        """D-06: report layers/summary_text/connections map correctly into config dict."""
        from generate_pretty import _config_from_codebase_report

        config, viz_type = _config_from_codebase_report(self.mock_report)

        assert config["layers"] == self.mock_report["layers"]
        assert config["description"] == self.mock_report["summary_text"]
        assert config["connections"] == self.mock_report["connections"]

    def test_codebase_title_derivation(self):
        """D-07: Title derived from directory name when --title is the argparse default."""
        from generate_pretty import _config_from_codebase_report

        # Use a report with a hyphenated root directory name
        report = dict(self.mock_report)
        report["root"] = "/tmp/my-cool-project"

        # When title == "System Architecture" (argparse default), derive from directory name
        config, viz_type = _config_from_codebase_report(report, title="System Architecture")
        assert config["title"] == "My Cool Project"

    def test_codebase_title_explicit(self):
        """D-07: When --title is explicitly set, use it as-is."""
        from generate_pretty import _config_from_codebase_report

        config, viz_type = _config_from_codebase_report(self.mock_report, title="Custom Title")
        assert config["title"] == "Custom Title"

    def test_codebase_viz_type_forced_arch(self):
        """D-05: viz_type is always 'arch' for codebase infographics."""
        from generate_pretty import _config_from_codebase_report

        _, viz_type = _config_from_codebase_report(self.mock_report)
        assert viz_type == "arch"
