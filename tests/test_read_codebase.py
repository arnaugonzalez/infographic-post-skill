"""Tests for scripts/read_codebase.py — CODEBASE-01 and CODEBASE-03."""
import sys
from pathlib import Path

# Add scripts/ to path for direct import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from read_codebase import read_codebase


class TestNoiseFilter:
    """CODEBASE-01: Noise filter skips build artifacts."""

    def test_pycache_excluded(self, tmp_path):
        """Files under __pycache__ must not appear in files_included."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "foo.pyc").write_bytes(b"fake bytecode")
        # Add a real source file so there is something to read
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("__pycache__" in p for p in included), (
            f"__pycache__ path appeared in files_included: {included}"
        )

    def test_git_dir_excluded(self, tmp_path):
        """Files under .git must not appear in files_included."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]\n    bare = false\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any(".git" in p for p in included), (
            f".git path appeared in files_included: {included}"
        )

    def test_node_modules_excluded(self, tmp_path):
        """Files under node_modules must not appear in files_included."""
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {};\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("node_modules" in p for p in included), (
            f"node_modules path appeared in files_included: {included}"
        )

    def test_venv_excluded(self, tmp_path):
        """Files under .venv must not appear in files_included."""
        venv_lib = tmp_path / ".venv" / "lib"
        venv_lib.mkdir(parents=True)
        (venv_lib / "site.py").write_text("# site customization\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any(".venv" in p for p in included), (
            f".venv path appeared in files_included: {included}"
        )

    def test_source_file_included(self, tmp_path):
        """A regular Python source file must appear in files_included."""
        (tmp_path / "main.py").write_text("def hello(): return 'hi'\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert any("main.py" in p for p in included), (
            f"main.py not found in files_included: {included}"
        )

    def test_gitignore_pattern_honored(self, tmp_path):
        """Files matching .gitignore patterns must be excluded when pathspec is available."""
        (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")
        (tmp_path / "tmp.log").write_text("log output here\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("tmp.log" in p for p in included), (
            f"tmp.log (gitignored) appeared in files_included: {included}"
        )


class TestBinaryFilter:
    """CODEBASE-01: Binary file detection."""

    def test_binary_null_byte_excluded(self, tmp_path):
        """Files containing null bytes must not appear in files_included."""
        (tmp_path / "file.dat").write_bytes(b"\x00\x01\x02\x03binary content")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("file.dat" in p for p in included), (
            f"Binary file.dat appeared in files_included: {included}"
        )

    def test_pyc_extension_excluded(self, tmp_path):
        """Files with .pyc extension must not appear in files_included."""
        (tmp_path / "cache.pyc").write_bytes(b"fake bytecode data")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("cache.pyc" in p for p in included), (
            f"cache.pyc appeared in files_included: {included}"
        )

    def test_text_file_included(self, tmp_path):
        """Plain text file must appear in files_included."""
        (tmp_path / "readme.txt").write_text("hello world\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert any("readme.txt" in p for p in included), (
            f"readme.txt not found in files_included: {included}"
        )


class TestCredentialSkip:
    """CODEBASE-03: Credential files unconditionally skipped."""

    def test_env_file_skipped(self, tmp_path):
        """The .env file must never appear in files_included."""
        (tmp_path / ".env").write_text(
            "FAKE_KEY=AIzaSyTEST_this_is_not_real_1234567890\n", encoding="utf-8"
        )
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any(p.endswith(".env") or p == ".env" for p in included), (
            f".env appeared in files_included: {included}"
        )

    def test_credentials_json_skipped(self, tmp_path):
        """credentials.json must never appear in files_included."""
        (tmp_path / "credentials.json").write_text(
            '{"type": "service_account"}\n', encoding="utf-8"
        )
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("credentials.json" in p for p in included), (
            f"credentials.json appeared in files_included: {included}"
        )

    def test_pem_file_skipped(self, tmp_path):
        """PEM certificate files must never appear in files_included."""
        (tmp_path / "server.pem").write_text(
            "-----BEGIN CERTIFICATE-----\nfakecert\n-----END CERTIFICATE-----\n",
            encoding="utf-8",
        )
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("server.pem" in p for p in included), (
            f"server.pem appeared in files_included: {included}"
        )

    def test_service_account_json_skipped(self, tmp_path):
        """service_account*.json files must never appear in files_included."""
        (tmp_path / "service_account_prod.json").write_text(
            '{"type": "service_account", "project_id": "my-project"}\n', encoding="utf-8"
        )
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        report = read_codebase(tmp_path)
        included = report["files_included"]
        assert not any("service_account_prod.json" in p for p in included), (
            f"service_account_prod.json appeared in files_included: {included}"
        )


class TestContentRedaction:
    """CODEBASE-03: Secret patterns redacted from file content in summary_text."""

    def test_google_api_key_redacted(self, tmp_path):
        """Google API key (AIza...) in file content must be replaced with [REDACTED]."""
        (tmp_path / "config.py").write_text(
            'key = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234"\n', encoding="utf-8"
        )

        report = read_codebase(tmp_path)
        assert "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234" not in report["summary_text"], (
            "Google API key was not redacted from summary_text"
        )
        assert "[REDACTED]" in report["summary_text"], (
            "Expected [REDACTED] in summary_text but not found"
        )

    def test_openrouter_key_redacted(self, tmp_path):
        """OpenRouter key (sk-or-v1-...) in file content must be replaced with [REDACTED]."""
        (tmp_path / "config.py").write_text(
            "api_key = 'sk-or-v1-abcdefghijklmnopqrstuvwxyz123456'\n", encoding="utf-8"
        )

        report = read_codebase(tmp_path)
        assert "sk-or-v1-abcdefghijklmnopqrstuvwxyz123456" not in report["summary_text"], (
            "OpenRouter key was not redacted from summary_text"
        )
        assert "[REDACTED]" in report["summary_text"], (
            "Expected [REDACTED] in summary_text but not found"
        )

    def test_github_pat_redacted(self, tmp_path):
        """GitHub PAT (ghp_...) in file content must be replaced with [REDACTED]."""
        (tmp_path / "config.py").write_text(
            "token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl'\n", encoding="utf-8"
        )

        report = read_codebase(tmp_path)
        assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl" not in report["summary_text"], (
            "GitHub PAT was not redacted from summary_text"
        )
        assert "[REDACTED]" in report["summary_text"], (
            "Expected [REDACTED] in summary_text but not found"
        )

    def test_generic_key_value_redacted(self, tmp_path):
        """Generic api_key = 'VALUE' pattern must be replaced with [REDACTED]."""
        (tmp_path / "config.py").write_text(
            "api_key = 'ABCDEF1234567890GHIJ'\n", encoding="utf-8"
        )

        report = read_codebase(tmp_path)
        assert "ABCDEF1234567890GHIJ" not in report["summary_text"], (
            "Generic api_key value was not redacted from summary_text"
        )
        assert "[REDACTED]" in report["summary_text"], (
            "Expected [REDACTED] in summary_text but not found"
        )

    def test_normal_code_not_redacted(self, tmp_path):
        """Normal code without secrets must appear unchanged in summary_text."""
        code = "def calculate(x): return x * 2\n"
        (tmp_path / "calc.py").write_text(code, encoding="utf-8")

        report = read_codebase(tmp_path)
        assert "def calculate(x): return x * 2" in report["summary_text"], (
            "Normal code was incorrectly redacted or missing from summary_text"
        )
