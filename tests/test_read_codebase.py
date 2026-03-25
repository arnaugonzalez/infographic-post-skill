"""Tests for scripts/read_codebase.py — CODEBASE-01, CODEBASE-02, CODEBASE-03, CODEBASE-04."""
import json
import subprocess
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


class TestTokenBudget:
    """CODEBASE-02: Token budget enforcement with explicit exclusion."""

    def test_budget_excludes_large_files(self, tmp_path):
        """Files that exceed the token budget are listed in files_excluded."""
        for i in range(5):
            (tmp_path / f"big_{i}.py").write_text("x" * 10_000)
        report = read_codebase(tmp_path, token_budget=5000)
        assert len(report["files_excluded"]) > 0
        assert len(report["files_included"]) < 5

    def test_budget_exclusion_message_printed(self, tmp_path, capsys):
        """Exceeding token budget must print explicit exclusion message to stderr."""
        for i in range(5):
            (tmp_path / f"big_{i}.py").write_text("x" * 10_000)
        read_codebase(tmp_path, token_budget=5000)
        captured = capsys.readouterr()
        assert "Token budget" in captured.err or "Excluded" in captured.err, (
            f"Expected exclusion message in stderr, got: {captured.err!r}"
        )

    def test_budget_warning_goes_to_stderr_not_stdout(self, tmp_path, capsys):
        """GAP-3: Budget warning must print to stderr, not stdout."""
        # Create enough files to exceed a tiny budget
        for i in range(10):
            (tmp_path / f"file_{i}.py").write_text("x" * 500)
        read_codebase(str(tmp_path), token_budget=100)
        captured = capsys.readouterr()
        # Warning must be in stderr
        assert "Token budget" in captured.err
        assert "Excluded" in captured.err
        # stdout must be clean
        assert "Token budget" not in captured.out
        assert "Excluded" not in captured.out

    def test_all_files_within_budget(self, tmp_path):
        """Small files that fit in budget must all be included and files_excluded empty."""
        for i in range(2):
            (tmp_path / f"small_{i}.py").write_text("x" * 100)
        report = read_codebase(tmp_path, token_budget=40_000)
        assert len(report["files_excluded"]) == 0
        assert len(report["files_included"]) == 2

    def test_token_estimate_in_report(self, tmp_path):
        """token_estimate must be at least chars // 4 of the file content."""
        (tmp_path / "file.py").write_text("x" * 400)
        report = read_codebase(tmp_path)
        assert report["token_estimate"] >= 100, (
            f"token_estimate too low: {report['token_estimate']}"
        )


class TestTokenBudgetEnvVar:
    """CODEBASE-02: INFG_CODEBASE_TOKEN_BUDGET env var override."""

    def test_env_var_overrides_default(self, tmp_path, monkeypatch):
        """Setting INFG_CODEBASE_TOKEN_BUDGET=500 forces a very tight budget."""
        monkeypatch.setenv("INFG_CODEBASE_TOKEN_BUDGET", "500")
        for i in range(3):
            (tmp_path / f"big_{i}.py").write_text("y" * 5_000)
        report = read_codebase(tmp_path)
        assert len(report["files_excluded"]) > 0, (
            "Expected files to be excluded with budget=500 but files_excluded is empty"
        )

    def test_env_var_not_set_uses_default(self, tmp_path, monkeypatch):
        """When INFG_CODEBASE_TOKEN_BUDGET is absent the default 40,000 budget is used."""
        monkeypatch.delenv("INFG_CODEBASE_TOKEN_BUDGET", raising=False)
        for i in range(2):
            (tmp_path / f"small_{i}.py").write_text("z" * 100)
        report = read_codebase(tmp_path)
        # With small files and 40k budget everything should be included
        assert len(report["files_excluded"]) == 0


class TestCodebaseReportSchema:
    """CODEBASE-04: CodebaseReport dict has correct structure."""

    def test_report_has_required_keys(self, tmp_path):
        """All 9 required keys must be present in the returned dict."""
        (tmp_path / "main.py").write_text("x = 1\n")
        report = read_codebase(tmp_path)
        required_keys = {
            "root", "title", "summary_text", "layers", "connections",
            "files_included", "files_excluded", "token_estimate", "format",
        }
        missing = required_keys - set(report.keys())
        assert not missing, f"Missing keys in report: {missing}"

    def test_format_is_codebase(self, tmp_path):
        """report['format'] must equal 'codebase'."""
        (tmp_path / "main.py").write_text("x = 1\n")
        report = read_codebase(tmp_path)
        assert report["format"] == "codebase", (
            f"Expected format='codebase', got {report['format']!r}"
        )

    def test_root_is_absolute_path(self, tmp_path):
        """report['root'] must be an absolute path (starts with '/')."""
        (tmp_path / "main.py").write_text("x = 1\n")
        report = read_codebase(tmp_path)
        assert report["root"].startswith("/"), (
            f"Expected absolute path for root, got: {report['root']!r}"
        )

    def test_title_is_dirname(self, tmp_path):
        """report['title'] must match the directory name."""
        (tmp_path / "main.py").write_text("x = 1\n")
        report = read_codebase(tmp_path)
        assert report["title"] == tmp_path.name, (
            f"Expected title={tmp_path.name!r}, got {report['title']!r}"
        )


class TestLayersFormat:
    """CODEBASE-04: layers key matches arch.json format."""

    def test_layers_is_list(self, tmp_path):
        """report['layers'] must be a list."""
        (tmp_path / "main.py").write_text("x = 1\n")
        report = read_codebase(tmp_path)
        assert isinstance(report["layers"], list), (
            f"Expected layers to be a list, got {type(report['layers'])}"
        )

    def test_layer_has_required_keys(self, tmp_path):
        """Each layer dict must have label, category, items, bg, border, label_color."""
        (tmp_path / "main.py").write_text("x = 1\n")
        report = read_codebase(tmp_path)
        required_layer_keys = {"label", "category", "items", "bg", "border", "label_color"}
        for layer in report["layers"]:
            missing = required_layer_keys - set(layer.keys())
            assert not missing, f"Layer missing keys {missing}: {layer}"


class TestASTExtraction:
    """CODEBASE-01/04: Python files get AST signal extraction."""

    def test_python_file_signals_extracted(self, tmp_path):
        """Class and function names from a .py file must appear in summary_text."""
        code = (
            "class MyService:\n"
            "    pass\n"
            "\n"
            "def process_data(x):\n"
            "    return x\n"
            "\n"
            "def helper_fn():\n"
            "    pass\n"
        )
        (tmp_path / "service.py").write_text(code)
        report = read_codebase(tmp_path)
        assert "MyService" in report["summary_text"], (
            "Class name 'MyService' not found in summary_text"
        )
        assert "process_data" in report["summary_text"], (
            "Function name 'process_data' not found in summary_text"
        )

    def test_non_python_file_raw_content(self, tmp_path):
        """Non-.py files must include their raw content in summary_text."""
        js_content = "function greet(name) { return 'hello ' + name; }\n"
        (tmp_path / "utils.js").write_text(js_content)
        report = read_codebase(tmp_path)
        assert "function greet" in report["summary_text"], (
            "Raw JS content not found in summary_text"
        )


class TestCLI:
    """CODEBASE-04: CLI entry point produces valid JSON."""

    def test_cli_json_output(self, tmp_path):
        """Running the script with a directory arg must print valid JSON to stdout."""
        (tmp_path / "hello.py").write_text("print('hello')")
        result = subprocess.run(
            [sys.executable, "scripts/read_codebase.py", str(tmp_path)],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent)
        )
        assert result.returncode == 0, f"Non-zero exit: {result.stderr}"
        data = json.loads(result.stdout)
        assert "files_included" in data

    def test_cli_output_flag(self, tmp_path):
        """Running with --output flag must write a valid JSON file."""
        (tmp_path / "hello.py").write_text("print('hello')")
        out_file = tmp_path / "report.json"
        result = subprocess.run(
            [sys.executable, "scripts/read_codebase.py", str(tmp_path),
             "--output", str(out_file)],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent)
        )
        assert result.returncode == 0, f"Non-zero exit: {result.stderr}"
        assert out_file.exists(), "Output file was not created"
        data = json.loads(out_file.read_text())
        assert "files_included" in data
