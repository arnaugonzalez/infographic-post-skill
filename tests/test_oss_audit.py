"""Unit tests for oss_audit.py core functions.

Covers AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04.
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
    run_audit,
    write_report,
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


# ---------------------------------------------------------------------------
# TestReportFile (AUDIT-04)
# ---------------------------------------------------------------------------

def _make_minimal_scripts_dir(tmp_path: Path) -> Path:
    """Create a minimal scripts/ directory with a simple .py file for test use."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "hello.py").write_text(
        'def greet():\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    return scripts_dir


def _make_audit_dict(**overrides) -> dict:
    """Build a minimal audit dict, with optional per-key overrides."""
    base = {
        "coverage": {},
        "docstrings_missing": [],
        "oss_files": {"README.md": True, "LICENSE": False, ".env.example": False,
                      "CHANGELOG.md": False, "CHANGELOG": False},
        "flake8_issues": [],
        "complexity_hotspots": [],
    }
    base.update(overrides)
    return base


class TestReportFile:
    """AUDIT-04: write_report writes QUALITY_AUDIT.md with all 5 sections."""

    def test_quality_audit_md_written(self, tmp_path):
        """run_audit returns dict; write_report creates QUALITY_AUDIT.md with all section headers."""
        audit = _make_audit_dict()
        out = tmp_path / "QUALITY_AUDIT.md"
        write_report(audit, out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# Quality Audit Report" in content
        assert "## Test Coverage" in content
        assert "## Docstring Coverage" in content
        assert "## OSS Baseline Files" in content
        assert "## Code Quality (Flake8)" in content
        assert "## Complexity Hotspots" in content

    def test_coverage_section_content(self, tmp_path):
        """When coverage has {'scripts/foo.py': 85.0}, report contains 'scripts/foo.py' and '85.0'."""
        audit = _make_audit_dict(coverage={"scripts/foo.py": 85.0})
        out = tmp_path / "QUALITY_AUDIT.md"
        write_report(audit, out)
        content = out.read_text(encoding="utf-8")
        assert "scripts/foo.py" in content
        assert "85.0" in content

    def test_missing_docstrings_listed(self, tmp_path):
        """When docstrings_missing has entries, report lists them."""
        audit = _make_audit_dict(docstrings_missing=["foo.py::bar (line 5)"])
        out = tmp_path / "QUALITY_AUDIT.md"
        write_report(audit, out)
        content = out.read_text(encoding="utf-8")
        assert "foo.py::bar (line 5)" in content

    def test_oss_files_present_absent(self, tmp_path):
        """When oss_files has README.md True and LICENSE False, report shows appropriate indicators."""
        audit = _make_audit_dict(oss_files={"README.md": True, "LICENSE": False})
        out = tmp_path / "QUALITY_AUDIT.md"
        write_report(audit, out)
        content = out.read_text(encoding="utf-8")
        # README.md should show present indicator
        assert "README.md" in content
        # LICENSE should show missing indicator
        assert "LICENSE" in content
        assert "MISSING" in content

    def test_flake8_issues_listed(self, tmp_path):
        """When flake8_issues has entries, report contains the code and message."""
        audit = _make_audit_dict(flake8_issues=[{
            "file": "foo.py", "line": "10", "col": "1",
            "code": "F401", "message": "F401 'os' imported but unused",
        }])
        out = tmp_path / "QUALITY_AUDIT.md"
        write_report(audit, out)
        content = out.read_text(encoding="utf-8")
        assert "F401" in content
        assert "imported but unused" in content

    def test_complexity_hotspots_listed(self, tmp_path):
        """When complexity_hotspots has entries, report contains function name and branch count."""
        audit = _make_audit_dict(complexity_hotspots=[{
            "file": "complex.py", "name": "big_func", "line": 3, "branches": 8,
        }])
        out = tmp_path / "QUALITY_AUDIT.md"
        write_report(audit, out)
        content = out.read_text(encoding="utf-8")
        assert "big_func" in content
        assert "8" in content


# ---------------------------------------------------------------------------
# TestCLI (AUDIT-04)
# ---------------------------------------------------------------------------

class TestCLI:
    """AUDIT-04: CLI accepts --root flag, exits 0, creates QUALITY_AUDIT.md."""

    def _make_project(self, tmp_path: Path) -> Path:
        """Create minimal project structure for CLI smoke test."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "hello.py").write_text(
            'def greet():\n    """Return a greeting."""\n    return "hello"\n',
            encoding="utf-8",
        )
        return tmp_path

    def test_cli_exits_zero(self, tmp_path):
        """subprocess.run(['python3', 'oss_audit.py', '--root', str(tmp_path)]) exits 0."""
        project = self._make_project(tmp_path)
        result = subprocess.run(
            ["python3", "oss_audit.py", "--root", str(project)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"CLI exited {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    def test_cli_creates_file(self, tmp_path):
        """After running CLI, tmp_path / 'QUALITY_AUDIT.md' exists."""
        project = self._make_project(tmp_path)
        subprocess.run(
            ["python3", "oss_audit.py", "--root", str(project)],
            capture_output=True,
            text=True,
        )
        assert (project / "QUALITY_AUDIT.md").exists()
