"""Tests for scripts/template_renderer.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from template_renderer import _LAYER_PALETTE, render_infographic


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sample_data(*, with_colors: bool = False, with_icons: bool = False) -> dict:
    """Return minimal valid infographic data for testing."""
    items_frontend = [
        {"name": "React Native", "description": "Cross-platform mobile SDK"},
        {"name": "Expo", "description": "Build & deploy pipeline"},
    ]
    items_backend = [
        {"name": "FastAPI", "description": "Async Python API framework"},
    ]
    if with_icons:
        for item in items_frontend + items_backend:
            item["icon_svg"] = '<svg width="20" height="20"><circle r="5"/></svg>'

    layers = [
        {"label": "FRONTEND", "items": items_frontend},
        {"label": "BACKEND", "items": items_backend},
    ]
    if with_colors:
        layers[0]["color"] = "#FF0000"
        layers[1]["color"] = "#00FF00"

    return {
        "title": "Test App",
        "subtitle": "Architecture Overview",
        "layers": layers,
        "connections": [{"from_layer": 0, "to_layer": 1, "label": "REST API"}],
        "footer_cta": "Follow for more",
        "footer_summary": "Built with Python and React",
        "author": "",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRenderInfographic:
    """Core render_infographic() tests."""

    def test_produces_valid_html(self, tmp_path: Path) -> None:
        """Rendered output is a non-empty HTML file containing expected markers."""
        data = _sample_data()
        out = render_infographic(data, output=tmp_path / "out.html")

        assert out.exists()
        html = out.read_text(encoding="utf-8")
        assert len(html) > 500
        assert "<!DOCTYPE html>" in html
        assert "Test App" in html
        assert "FRONTEND" in html
        assert "BACKEND" in html
        assert "React Native" in html
        assert "FastAPI" in html

    def test_output_file_created_at_path(self, tmp_path: Path) -> None:
        """Output file is written to the exact path requested."""
        dest = tmp_path / "subdir" / "my_infographic.html"
        data = _sample_data()
        out = render_infographic(data, output=dest)

        assert out == dest
        assert dest.exists()

    def test_output_adds_html_suffix(self, tmp_path: Path) -> None:
        """If output has no .html suffix, it's appended."""
        dest = tmp_path / "report"
        data = _sample_data()
        out = render_infographic(data, output=dest)

        assert out.suffix == ".html"
        assert out.exists()


class TestColorAssignment:
    """Layer colors are auto-assigned from the palette."""

    def test_colors_auto_assigned(self, tmp_path: Path) -> None:
        """Layers without 'color' key get palette colours."""
        data = _sample_data(with_colors=False)
        render_infographic(data, output=tmp_path / "out.html")

        assert data["layers"][0]["color"] == _LAYER_PALETTE[0]
        assert data["layers"][1]["color"] == _LAYER_PALETTE[1]

    def test_existing_colors_preserved(self, tmp_path: Path) -> None:
        """Layers that already have a color keep it."""
        data = _sample_data(with_colors=True)
        render_infographic(data, output=tmp_path / "out.html")

        assert data["layers"][0]["color"] == "#FF0000"
        assert data["layers"][1]["color"] == "#00FF00"

    def test_palette_wraps_around(self, tmp_path: Path) -> None:
        """More layers than palette colours wraps around."""
        data = _sample_data()
        # Add enough layers to exceed palette length
        for i in range(len(_LAYER_PALETTE) + 1):
            data["layers"].append({"label": f"LAYER-{i}", "items": []})

        render_infographic(data, output=tmp_path / "out.html")

        last_layer = data["layers"][-1]
        expected_idx = (len(data["layers"]) - 1) % len(_LAYER_PALETTE)
        assert last_layer["color"] == _LAYER_PALETTE[expected_idx]


class TestIconEnrichment:
    """Items are enriched with SVG icons when missing."""

    def test_icons_added_when_missing(self, tmp_path: Path) -> None:
        """Items without icon_svg get one from icon_registry."""
        data = _sample_data(with_icons=False)
        render_infographic(data, output=tmp_path / "out.html")

        for layer in data["layers"]:
            for item in layer["items"]:
                assert "icon_svg" in item
                assert len(item["icon_svg"]) > 0

    def test_existing_icons_preserved(self, tmp_path: Path) -> None:
        """Items that already have icon_svg keep their original."""
        data = _sample_data(with_icons=True)
        render_infographic(data, output=tmp_path / "out.html")

        for layer in data["layers"]:
            for item in layer["items"]:
                assert "circle" in item["icon_svg"]


class TestTemplateNotFound:
    """Requesting a missing template raises an error."""

    def test_missing_template_raises(self, tmp_path: Path) -> None:
        """A non-existent template name raises TemplateNotFound."""
        import jinja2

        data = _sample_data()
        with pytest.raises(jinja2.TemplateNotFound):
            render_infographic(
                data,
                template_name="does-not-exist",
                output=tmp_path / "out.html",
            )


class TestConnectionsRendered:
    """Connection arrows appear in the rendered HTML."""

    def test_connections_in_output(self, tmp_path: Path) -> None:
        data = _sample_data()
        out = render_infographic(data, output=tmp_path / "out.html")
        html = out.read_text(encoding="utf-8")

        assert "arrowhead" in html
        assert "REST API" in html
        assert "stroke-dasharray" in html

    def test_no_connections_no_svg(self, tmp_path: Path) -> None:
        """When connections list is empty, no SVG overlay is rendered."""
        data = _sample_data()
        data["connections"] = []
        out = render_infographic(data, output=tmp_path / "out.html")
        html = out.read_text(encoding="utf-8")

        assert "arrowhead" not in html
