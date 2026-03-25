"""Unit tests for oss_audit.py core functions.

Covers AUDIT-01, AUDIT-02, AUDIT-03.
All subprocess calls are mocked — no live coverage/flake8 needed.
"""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, ".")

from oss_audit import (
    COMPLEXITY_THRESHOLD,
    _branch_complexity,
    _check_docstrings,
    _check_oss_files,
    _run_coverage,
    _run_flake8,
)


# ---------------------------------------------------------------------------
# TestCoverage (AUDIT-01)
# ---------------------------------------------------------------------------

class TestCoverage:
    """AUDIT-01: _run_coverage returns dict mapping module paths to float percentages."""

    def test_returns_dict_with_module_percentages(self, tmp_path):
        """_run_coverage returns {"scripts/foo.py": 85.0} when coverage JSON has that data."""
        fake_coverage_data = {
            "files": {
                "scripts/foo.py": {
                    "summary": {"percent_covered": 85.0}
                }
            }
        }

        def fake_subprocess_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            result.stdout = ""
            if "json" in cmd:
                # Write fake coverage.json into cwd (project_root)
                cwd = kwargs.get("cwd", tmp_path)
                output_path = None
                for i, arg in enumerate(cmd):
                    if arg == "-o" and i + 1 < len(cmd):
                        output_path = Path(cmd[i + 1])
                        break
                if output_path is None:
                    output_path = Path(cwd) / "coverage.json"
                output_path.write_text(json.dumps(fake_coverage_data), encoding="utf-8")
            return result

        with patch("subprocess.run", side_effect=fake_subprocess_run):
            result = _run_coverage(tmp_path)

        assert isinstance(result, dict)
        assert "scripts/foo.py" in result
        assert result["scripts/foo.py"] == 85.0

    def test_graceful_when_coverage_missing(self, tmp_path):
        """_run_coverage returns {} when subprocess stderr contains 'No module named coverage'."""
        def fake_subprocess_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 1
            result.stderr = "No module named coverage"
            result.stdout = ""
            return result

        with patch("subprocess.run", side_effect=fake_subprocess_run):
            result = _run_coverage(tmp_path)

        assert result == {}


# ---------------------------------------------------------------------------
# TestDocstringCoverage (AUDIT-02)
# ---------------------------------------------------------------------------

class TestDocstringCoverage:
    """AUDIT-02: _check_docstrings returns list of qualified names missing docstrings."""

    def test_finds_missing_docstrings(self, tmp_path):
        """Returns ["test_file.py::bar (line N)"] for file with function bar missing docstring."""
        py_file = tmp_path / "test_file.py"
        py_file.write_text(
            'def foo():\n    """Has a docstring."""\n    pass\n\ndef bar():\n    pass\n',
            encoding="utf-8",
        )
        result = _check_docstrings(py_file)
        assert isinstance(result, list)
        assert len(result) == 1
        assert "bar" in result[0]
        assert "test_file.py" in result[0]

    def test_skips_documented_functions(self, tmp_path):
        """Returns [] when all functions have docstrings."""
        py_file = tmp_path / "test_file.py"
        py_file.write_text(
            'def foo():\n    """Has a docstring."""\n    pass\n\ndef bar():\n    """Also documented."""\n    pass\n',
            encoding="utf-8",
        )
        result = _check_docstrings(py_file)
        assert result == []


# ---------------------------------------------------------------------------
# TestOSSFiles (AUDIT-02)
# ---------------------------------------------------------------------------

class TestOSSFiles:
    """AUDIT-02: _check_oss_files returns dict mapping filenames to boolean presence."""

    def test_present_and_missing(self, tmp_path):
        """Returns {"README.md": True, "LICENSE": False, ...} based on which files exist."""
        (tmp_path / "README.md").write_text("readme", encoding="utf-8")
        # LICENSE not created — should be False
        result = _check_oss_files(tmp_path)
        assert isinstance(result, dict)
        assert result["README.md"] is True
        assert result["LICENSE"] is False
        # All expected OSS files are in result
        for key in ["README.md", "LICENSE", ".env.example", "CHANGELOG.md", "CHANGELOG"]:
            assert key in result


# ---------------------------------------------------------------------------
# TestFlake8 (AUDIT-03)
# ---------------------------------------------------------------------------

class TestFlake8:
    """AUDIT-03: _run_flake8 returns list of dicts with file/line/col/code/message."""

    def test_parses_output(self, tmp_path):
        """Returns list of dicts with correct keys when flake8 output matches expected format."""
        fake_stdout = "scripts/foo.py:1:1: F401 'os' imported but unused\n"

        def fake_subprocess_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 1
            result.stdout = fake_stdout
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=fake_subprocess_run):
            result = _run_flake8(tmp_path)

        assert isinstance(result, list)
        assert len(result) == 1
        entry = result[0]
        assert "file" in entry
        assert "line" in entry
        assert "col" in entry
        assert "code" in entry
        assert "message" in entry
        assert entry["code"] == "F401"
        assert entry["line"] == "1"

    def test_graceful_when_flake8_missing(self, tmp_path):
        """Returns [] when subprocess returncode is not 0 or 1."""
        def fake_subprocess_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 127  # command not found
            result.stdout = ""
            result.stderr = "command not found: flake8"
            return result

        with patch("subprocess.run", side_effect=fake_subprocess_run):
            result = _run_flake8(tmp_path)

        assert result == []


# ---------------------------------------------------------------------------
# TestComplexity (AUDIT-03)
# ---------------------------------------------------------------------------

class TestComplexity:
    """AUDIT-03: _branch_complexity returns list of dicts with file/name/line/branches."""

    def test_flags_high_branch_functions(self, tmp_path):
        """Returns entry with branches=6 for function with 6 branch nodes (>= COMPLEXITY_THRESHOLD=5)."""
        py_file = tmp_path / "complex.py"
        # Build a function with 6 branch nodes (if, for, while, try, with, if)
        src = (
            "def complex_func(x):\n"
            "    if x:\n"
            "        pass\n"
            "    for i in range(x):\n"
            "        pass\n"
            "    while x:\n"
            "        pass\n"
            "    try:\n"
            "        pass\n"
            "    except Exception:\n"
            "        pass\n"
            "    with open('/dev/null') as f:\n"
            "        pass\n"
            "    if not x:\n"
            "        pass\n"
        )
        py_file.write_text(src, encoding="utf-8")
        result = _branch_complexity(py_file)
        assert isinstance(result, list)
        assert len(result) == 1
        entry = result[0]
        assert entry["name"] == "complex_func"
        assert entry["branches"] >= COMPLEXITY_THRESHOLD
        assert "file" in entry
        assert "line" in entry

    def test_ignores_simple_functions(self, tmp_path):
        """Returns [] for file with only simple functions (< COMPLEXITY_THRESHOLD branches)."""
        py_file = tmp_path / "simple.py"
        src = "def simple_func(x):\n    if x:\n        return x\n    return 0\n"
        py_file.write_text(src, encoding="utf-8")
        result = _branch_complexity(py_file)
        assert result == []
