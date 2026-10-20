"""Tests for the Oct 2026 pipeline pieces: project digest, provider resolution,
Claude HTML renderer helpers."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "infographic" / "scripts"))

from claude_html_renderer import build_brief, inject_logos  # noqa: E402
from content_structurer import resolve_provider  # noqa: E402
from project_digest import build_digest  # noqa: E402


@pytest.fixture
def monorepo(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# Demo\nA demo platform.")
    api = tmp_path / "api"
    api.mkdir()
    (api / "requirements.txt").write_text("fastapi>=0.110\nsqlalchemy[asyncio]==2.0  # orm\n-r base.txt\n")
    (api / "main.py").write_text("print('hi')\n")
    app = tmp_path / "app"
    app.mkdir()
    (app / "pubspec.yaml").write_text("name: demo_app\ndependencies:\n  flutter:\n    sdk: flutter\n  dio: ^5.0\n"
                                      "dev_dependencies:\n  lints: any\n")
    (app / "main.dart").write_text("void main() {}\n")
    web = tmp_path / "web"
    web.mkdir()
    (web / "package.json").write_text(json.dumps({"name": "web", "dependencies": {"astro": "4"}}))
    (tmp_path / "docker-compose.yml").write_text("services:\n  api:\n    image: demo/api:1\n  db:\n"
                                                 "    image: postgres:16\n    environment:\n      X: 1\n")
    (tmp_path / ".env").write_text("SECRET=1")
    return tmp_path


class TestProjectDigest:
    def test_covers_every_subproject_manifest(self, monorepo):
        d = build_digest(monorepo)
        assert set(d["manifests"]) == {"api/requirements.txt", "app/pubspec.yaml",
                                       "web/package.json", "docker-compose.yml"}

    def test_reduces_manifests_to_dependency_names(self, monorepo):
        text = build_digest(monorepo)["summary_text"]
        assert "dependencies: fastapi, sqlalchemy" in text
        assert "dependencies: flutter, dio" in text  # dev_dependencies excluded
        assert "services: api, db" in text and "postgres:16" in text

    def test_language_histogram_includes_non_python(self, monorepo):
        langs = build_digest(monorepo)["languages"]
        assert langs == {"Python": 1, "Dart": 1}

    def test_never_reads_credential_files(self, monorepo):
        assert "SECRET" not in build_digest(monorepo)["summary_text"]

    def test_respects_char_budget(self, monorepo):
        text = build_digest(monorepo, char_budget=200)["summary_text"]
        assert len(text) < 260 and text.endswith("[digest truncated]")

    def test_idempotent(self, monorepo):
        assert build_digest(monorepo) == build_digest(monorepo)


class TestResolveProvider:
    @pytest.fixture(autouse=True)
    def _env(self, monkeypatch):
        monkeypatch.setattr("content_structurer._load_dotenv", lambda _p: None)
        for k in ("ANTHROPIC_API_KEY", "INFG_API_KEY", "INFG_OPENROUTER_API_KEY", "INFG_LLM_API_KEY",
                  "INFG_LLM_MODEL"):
            monkeypatch.delenv(k, raising=False)

    def test_auto_prefers_anthropic_haiku(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
        monkeypatch.setenv("INFG_API_KEY", "g")
        assert resolve_provider() == ("anthropic", "claude-haiku-5-5", "a")

    def test_auto_falls_back_to_gemini(self, monkeypatch):
        monkeypatch.setenv("INFG_API_KEY", "g")
        assert resolve_provider() == ("gemini", "gemini-3.8-flash", "g")

    @pytest.mark.parametrize("model,provider", [("claude-opus-5-5", "anthropic"),
                                                ("gemini-3.8-flash", "gemini"),
                                                ("anthropic/claude-sonnet-5.5", "openrouter")])
    def test_model_name_selects_provider(self, model, provider):
        assert resolve_provider(model)[0] == provider

    def test_no_keys_no_model_exits(self):
        with pytest.raises(SystemExit):
            resolve_provider()


class TestClaudeHtmlRenderer:
    def test_inject_replaces_placeholders_with_svg(self):
        html = '<div><span class="logo" data-icon="FastAPI"></span><span class="logo" data-icon="Acme Bus"> </span></div>'
        out = inject_logos(html)
        assert out.count("<svg") == 2
        assert 'width="100%"' in out and ">AB</text>" in out

    def test_inject_leaves_non_empty_spans(self):
        html = '<span data-icon="FastAPI">FastAPI</span>'
        assert inject_logos(html) == html

    def test_brief_embeds_exact_spec_and_style(self):
        brief = build_brief({"title": "Ünïcode Ñame", "layers": []}, style="modern-light")
        assert "Ünïcode Ñame" in brief and "clean light" in brief and "1080×1080" in brief
