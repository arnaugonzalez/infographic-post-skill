"""Tests for scripts/backends.py, doctor.py, and selectable backend integration."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "infographic" / "scripts"))

import backends  # noqa: E402
import claude_html_renderer  # noqa: E402
import content_structurer  # noqa: E402
from backends import (  # noqa: E402
    BACKENDS,
    BackendError,
    build_argv,
    build_prompt,
    detect,
    extract_html,
    extract_json,
    resolve,
    run,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in (
        "INFG_BACKEND",
        "INFG_MODEL",
        "CLAUDECODE",
        "ANTHROPIC_API_KEY",
        "INFG_API_KEY",
        "INFG_OPENROUTER_API_KEY",
        "INFG_LLM_API_KEY",
        "INFG_LLM_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(content_structurer, "_load_dotenv", lambda _p: None)


class TestDetectAndResolve:
    def test_argument_beats_env_and_auto(self, monkeypatch):
        monkeypatch.setenv("INFG_BACKEND", "agy")
        monkeypatch.setenv("INFG_MODEL", "gemini-4-argon-high")
        monkeypatch.setenv("CLAUDECODE", "1")
        assert resolve("codex", "gpt-5") == ("codex", "gpt-5")

    def test_env_beats_auto(self, monkeypatch):
        monkeypatch.setenv("INFG_BACKEND", "agy")
        monkeypatch.setenv("INFG_MODEL", "gemini-4-argon-high")
        monkeypatch.setenv("CLAUDECODE", "1")
        assert resolve(None, None) == ("agy", "gemini-4-argon-high")

    def test_claudecode_selects_session_in_auto(self, monkeypatch):
        monkeypatch.setenv("CLAUDECODE", "1")
        monkeypatch.setattr("shutil.which", lambda b: f"/usr/bin/{b}")
        assert resolve(None, None) == ("session", None)

    def test_auto_picks_first_detected_cli(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda b: "/usr/bin/agy" if b == "agy" else None)
        assert resolve(None, None) == ("agy", "claude-opus-5-5-low")

    def test_auto_never_returns_api_even_with_keys(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _b: None)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
        monkeypatch.setenv("INFG_API_KEY", "AIzaSecret")
        assert "api" in detect()
        with pytest.raises(SystemExit) as exc:
            resolve(None, None)
        assert "claude" in str(exc.value) and "agy" in str(exc.value)

    def test_no_clis_and_no_keys_exits_with_install_help(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _b: None)
        with pytest.raises(SystemExit) as exc:
            resolve(None, None)
        msg = str(exc.value)
        for name in ("claude", "agy", "codex", "copilot", "opencode"):
            assert name in msg


class TestArgvAndStdin:
    def test_argv_with_and_without_model(self):
        assert build_argv("claude", None, "P") == [
            "claude", "-p", "--model", "claude-opus-5-5", "--tools", "", "--strict-mcp-config"
        ]
        assert build_argv("claude", "claude-sonnet-5-5", "P") == [
            "claude", "-p", "--model", "claude-sonnet-5-5", "--tools", "", "--strict-mcp-config"
        ]
        assert build_argv("agy", None, "P") == ["agy", "-p", "P", "-m", "claude-opus-5-5-low"]
        assert build_argv("agy", "gemini-4-argon-high", "P") == [
            "agy", "-p", "P", "-m", "gemini-4-argon-high"
        ]
        # codex and opencode omit -m and {model} when model is None
        assert build_argv("codex", None, "P") == ["codex", "exec", "--skip-git-repo-check", "-"]
        assert build_argv("codex", "gpt-5", "P") == [
            "codex", "exec", "--skip-git-repo-check", "-m", "gpt-5", "-"
        ]
        assert build_argv("opencode", None, "P") == ["opencode", "run", "P"]
        assert build_argv("opencode", "glm-5", "P") == ["opencode", "run", "-m", "glm-5", "P"]
        assert build_argv("copilot", None, "P") == ["copilot", "-p", "P", "--model", "auto"]
        assert build_argv("copilot", "gpt-5", "P") == ["copilot", "-p", "P", "--model", "gpt-5"]

    def test_stdin_used_only_for_claude_and_codex(self, monkeypatch):
        calls: list[tuple[str, dict]] = []

        def fake_run(cmd, **kwargs):
            calls.append((cmd[0], kwargs))
            res = MagicMock()
            res.returncode = 0
            res.stdout = "<!doctype html><html><body>ok</body></html>"
            res.stderr = ""
            return res

        monkeypatch.setattr("subprocess.run", fake_run)
        for name in ("claude", "agy", "codex", "copilot", "opencode"):
            run(name, None, "PROMPT_TEXT")

        by_bin = dict(calls)
        assert by_bin["claude"].get("input") == "PROMPT_TEXT"
        assert by_bin["codex"].get("input") == "PROMPT_TEXT"
        for name in ("agy", "copilot", "opencode"):
            assert "input" not in by_bin[name]
            assert by_bin[name].get("stdin") == subprocess.DEVNULL

    def test_nonzero_exit_raises_backend_error(self, monkeypatch):
        def fake_run(_cmd, **_kwargs):
            res = MagicMock()
            res.returncode = 2
            res.stdout = ""
            res.stderr = "fatal error from cli"
            return res

        monkeypatch.setattr("subprocess.run", fake_run)
        with pytest.raises(BackendError) as exc:
            run("claude", None, "hi")
        assert "fatal error from cli" in str(exc.value)


class TestExtractHtmlAndJson:
    def test_extract_html_with_fences_and_surrounding_text(self):
        raw = "Here is the code:\n```html\n<!DOCTYPE html><html><body><h1>Hi</h1></body></html>\n```\nDone!"
        assert extract_html(raw) == "<!DOCTYPE html><html><body><h1>Hi</h1></body></html>"

    def test_extract_html_from_html_tag_without_doctype(self):
        raw = "Preamble <HTML lang='en'><body>ok</body></HTML> trailing"
        assert extract_html(raw) == "<HTML lang='en'><body>ok</body></HTML>"

    def test_extract_html_raises_when_missing(self):
        with pytest.raises(BackendError):
            extract_html("No HTML tags in this response at all.")

    def test_extract_json_reuses_strip_fences(self):
        raw = "Sure:\n```json\n{\"title\": \"Demo\", \"layers\": []}\n```"
        assert extract_json(raw) == {"title": "Demo", "layers": []}


class TestBuildPrompt:
    @pytest.mark.parametrize(
        "model,expected_note",
        [
            ("gemini-4-argon-high", "No repitas párrafos ni rellenes para alcanzar mínimos."),
            ("claude-opus-5-5-low", "Effort bajo basta. Respeta el lienzo exacto."),
            ("gpt-5", "No añadas texto fuera del HTML. Respeta el lienzo exacto."),
            ("glm-5", "Usa solo los datos de la spec. No añadas texto fuera del HTML."),
        ],
    )
    def test_includes_brief_backend_and_model_family_note(self, model, expected_note):
        spec = {"title": "MySystem", "layers": []}
        prompt = build_prompt("render", "agy", model, spec)
        # 1. Brief content + spec JSON
        assert "1080×1080" in prompt and '"MySystem"' in prompt
        # 2. Backend contract (agy includes working-dir restriction)
        assert "No edites ni crees ficheros en el directorio de trabajo." in prompt
        # 3. Model family note
        assert expected_note in prompt


class TestResolveProviderNoAutoOpenRouter:
    def test_resolve_provider_never_returns_openrouter_automatically(self, monkeypatch):
        monkeypatch.setenv("INFG_OPENROUTER_API_KEY", "sk-or-v1-key")
        with pytest.raises(SystemExit):
            content_structurer.resolve_provider()

    def test_resolve_provider_forbids_gemini_on_openrouter(self):
        with pytest.raises(SystemExit):
            content_structurer.resolve_provider("google/gemini-2.5-flash")


class TestClaudeHtmlRendererBackendIntegration:
    def test_backend_claude_produces_logo_injected_html(self, monkeypatch, tmp_path):
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(
            json.dumps({"title": "Demo", "layers": [{"label": "API", "items": [{"name": "FastAPI"}]}]}),
            encoding="utf-8",
        )
        out_png = tmp_path / "out.png"

        def fake_subprocess_run(cmd, **kwargs):
            assert cmd[0] == "claude"
            assert kwargs.get("input")
            res = MagicMock()
            res.returncode = 0
            res.stdout = (
                "<!doctype html><html><body>"
                '<span class="logo" data-icon="FastAPI"></span>'
                "</body></html>"
            )
            res.stderr = ""
            return res

        def fake_screenshot(html_path: Path, png_path: Path) -> Path:
            png_path.write_bytes(b"FAKE_PNG")
            return png_path

        monkeypatch.setattr("subprocess.run", fake_subprocess_run)
        monkeypatch.setattr(claude_html_renderer, "screenshot", fake_screenshot)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "claude_html_renderer.py",
                "--backend",
                "claude",
                "--spec",
                str(spec_file),
                "--output",
                str(out_png),
            ],
        )

        claude_html_renderer.main()

        html_out = out_png.with_suffix(".html")
        assert html_out.exists()
        html_text = html_out.read_text(encoding="utf-8")
        assert "<svg " in html_text
        assert 'width="100%" height="100%"' in html_text
        assert out_png.exists()
