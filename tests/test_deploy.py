"""Tests for deploy readiness: key redaction, env var audit, docs accuracy, offline path."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")

SKILL_ROOT = Path(__file__).resolve().parent.parent


class TestKeyRedaction:
    """DEPLOY-01: OpenRouter and Google keys redacted in output."""

    def test_openrouter_key_redacted(self):
        from scripts.generate_pretty import _redact_key
        text = "Error: sk-or-v1-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
        result = _redact_key(text)
        assert "sk-or-v1-[REDACTED]" in result
        assert "sk-or-v1-abc123" not in result

    def test_google_key_still_redacted(self):
        from scripts.generate_pretty import _redact_key
        text = "key=AIzaSyD_example_key_1234567890abcdefghij"
        result = _redact_key(text)
        assert "[REDACTED]" in result
        assert "AIzaSyD_example_key" not in result

    def test_both_keys_in_same_string(self):
        from scripts.generate_pretty import _redact_key
        text = "google=AIzaSyD_example_key_1234567890abcdefghij or=sk-or-v1-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
        result = _redact_key(text)
        assert "AIzaSyD_example_key" not in result
        assert "sk-or-v1-abc123" not in result
        assert "sk-or-v1-[REDACTED]" in result
        assert "[REDACTED]" in result


class TestEnvVarAudit:
    """DEPLOY-02: All env vars documented in .env.example."""

    def test_all_env_vars_documented(self):
        gen_pretty = (SKILL_ROOT / "scripts" / "generate_pretty.py").read_text()
        env_example = (SKILL_ROOT / ".env.example").read_text()
        # Find all os.environ.get("INFG_...") calls
        pattern = re.compile(r'os\.environ\.get\(\s*["\'](\w+)["\']')
        env_vars = set(pattern.findall(gen_pretty))
        assert len(env_vars) >= 8, f"Expected at least 8 env vars, found {len(env_vars)}: {env_vars}"
        for var in env_vars:
            assert var in env_example, f"{var} not documented in .env.example"


class TestDocsAccuracy:
    """DEPLOY-03: Docs have correct Python version and OpenRouter section."""

    def test_skill_python_version(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        assert '">=' in skill or ">=3.9" in skill
        assert ">=3.8" not in skill, "SKILL.md still says 3.8"

    def test_readme_python_version(self):
        readme = (SKILL_ROOT / "README.md").read_text()
        assert "3.9" in readme
        assert "3.8+" not in readme, "README.md still says 3.8+"

    def test_skill_openrouter_section(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        assert "openrouter" in skill.lower(), "SKILL.md missing OpenRouter section"

    def test_readme_openrouter_section(self):
        readme = (SKILL_ROOT / "README.md").read_text()
        assert "openrouter" in readme.lower(), "README.md missing OpenRouter section"


class TestOfflinePath:
    """DEPLOY-04: Offline path works without openai installed."""

    def test_generate_loads_without_openai(self):
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.modules['openai'] = None; "
             "from scripts.generate_pretty import _redact_key; "
             "print('OK')"],
            capture_output=True, text=True, timeout=15,
            cwd=str(SKILL_ROOT),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "ImportError" not in result.stderr
