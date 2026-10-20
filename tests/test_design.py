"""Art direction: archetypes, formats, reference pages and the generic-design linter."""
import pytest

import design
from slop_lint import lint_html

DECIDED = "<!-- thesis: x\n hero: y\n archetype: editorial\n cut: none -->"


class TestDesign:
    def test_five_archetypes_parsed(self):
        assert set(design.ARCHETYPES) == {"editorial", "blueprint", "terminal", "swiss", "brutalist"}
        assert all(len(body) > 100 for body in design.ARCHETYPES.values())

    @pytest.mark.parametrize("legacy,archetype", list(design.LEGACY_STYLES.items()))
    def test_legacy_styles_map_to_archetypes(self, legacy, archetype):
        assert design.resolve_archetype(legacy) == archetype

    def test_unknown_style_and_format_fail_loudly(self):
        with pytest.raises(ValueError, match="editorial"):
            design.resolve_archetype("glassmorphism")
        with pytest.raises(ValueError, match="portrait"):
            design.canvas_size("a4")

    def test_brief_has_archetype_canvas_and_examples(self):
        brief = design.render_brief({"title": "Ñandú {x}"}, style="terminal", fmt="landscape")
        assert "archetype: terminal" in brief and "1280×640" in brief
        assert "Ñandú {x}" in brief and "REFERENCE PAGES" in brief

    def test_custom_style_dir_replaces_examples(self, tmp_path):
        (tmp_path / "mine.html").write_text("<html>MY-OWN-STYLE</html>", encoding="utf-8")
        brief = design.render_brief({}, style_dir=tmp_path)
        assert "MY-OWN-STYLE" in brief and "Fraunces" not in brief.split("REFERENCE PAGES")[1]

    def test_empty_style_dir_drops_examples_block(self, tmp_path):
        assert "REFERENCE PAGES" not in design.render_brief({}, style_dir=tmp_path)


class TestSlopLint:
    def test_clean_editorial_page_passes(self):
        html = (DECIDED + '<link href="https://fonts.googleapis.com/css2?family=Fraunces&family=Inter">'
                "<style>h1{font-family:Fraunces}</style>")
        assert lint_html(html) == []

    def test_generic_ai_page_is_flagged(self):
        html = ('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400">'
                "<style>body{background:linear-gradient(#0a0f1e,#4f46e5)}"
                ".c{box-shadow:0 4px 20px #000;border-radius:16px}.d{border-radius:16px}"
                ".e{border-radius:16px}.f{border-radius:16px}h1{background-clip:text}</style>"
                "<p>Technical Architecture Overview 🚀</p>")
        found = set(lint_html(html))
        assert {"gradient", "box-shadow", "gradient text", "purple/indigo palette", "emoji",
                "generic subtitle / CTA", "only generic fonts (Inter)",
                "many rounded cards (border-radius ≥ 12px)",
                "missing thesis/hero/archetype comment"} <= found

    def test_shipped_reference_pages_have_no_banned_patterns(self):
        for page in design.load_examples():
            assert [w for w in lint_html(page) if not w.startswith("missing")] == []


class TestLogoColors:
    def test_monogram_uses_current_color(self):
        from icon_registry import _monogram_svg
        svg = _monogram_svg("AWS EC2", 40)
        assert 'stroke="currentColor"' in svg and 'fill="currentColor"' in svg and "#" not in svg

    def test_logos_are_monochrome_unless_brand_colors(self):
        from claude_html_renderer import inject_logos
        page = '<span class="logo" data-icon="FastAPI"></span>'
        assert 'fill="currentColor"' in inject_logos(page)
        assert 'fill="#' in inject_logos(page, brand_colors=True)


class TestLayoutCheck:
    """Runs headless Chromium; skipped when Playwright's browser is not installed."""

    def _issues(self, tmp_path, capsys, body: str) -> str:
        pytest.importorskip("playwright")
        from claude_html_renderer import screenshot
        page = tmp_path / "p.html"
        page.write_text(f"<!doctype html><html><body style='margin:0;width:1080px;height:1080px'>{body}"
                        "</body></html>", encoding="utf-8")
        try:
            screenshot(page, tmp_path / "p.png")
        except Exception as exc:  # browser binary missing on this machine
            pytest.skip(f"chromium unavailable: {exc}")
        return capsys.readouterr().err

    def test_overlapping_blocks_are_reported(self, tmp_path, capsys):
        err = self._issues(tmp_path, capsys, "<h1 style='font-size:80px;line-height:.5'>Headline</h1>"
                                             "<p style='margin-top:-60px;font-size:30px'>Label</p>")
        assert 'text overlaps: "Headline" / "Label"' in err

    def test_tight_lines_of_one_heading_are_not_reported(self, tmp_path, capsys):
        err = self._issues(tmp_path, capsys, "<h1 style='font-size:80px;line-height:.9;width:400px'>"
                                             "Two lines of <b>one heading</b></h1>")
        assert "overlaps" not in err

    def test_text_outside_canvas_is_reported(self, tmp_path, capsys):
        err = self._issues(tmp_path, capsys, "<p style='position:absolute;left:1050px'>Overflowing</p>")
        assert 'outside the canvas: "Overflowing"' in err
