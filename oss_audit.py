#!/usr/bin/env python3
"""OSS Quality Audit — produces QUALITY_AUDIT.md."""
import ast
import json
import subprocess
from pathlib import Path

_OSS_FILES = ["README.md", "LICENSE", ".env.example", "CHANGELOG.md", "CHANGELOG"]
_BRANCH_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.With)
COMPLEXITY_THRESHOLD = 5


def _run_coverage(project_root: Path) -> dict:
    """Run coverage and return dict mapping module paths to float percentages.

    Returns {} if coverage is not installed or any unexpected error occurs.
    """
    try:
        run_result = subprocess.run(
            ["python3", "-m", "coverage", "run", "-m", "pytest", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if "No module named" in run_result.stderr:
            return {}

        json_path = project_root / "coverage.json"
        subprocess.run(
            ["python3", "-m", "coverage", "json", "-o", str(json_path)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        data = json.loads(json_path.read_text(encoding="utf-8"))
        result = {
            path: info["summary"]["percent_covered"]
            for path, info in data.get("files", {}).items()
        }
        json_path.unlink(missing_ok=True)
        return result
    except Exception:
        return {}


def _check_docstrings(py_file: Path) -> list[str]:
    """Return list of qualified names missing docstrings with line numbers.

    Returns [] on SyntaxError.
    """
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node) is None:
                missing.append(f"{py_file.name}::{node.name} (line {node.lineno})")
    return missing


def _check_oss_files(project_root: Path) -> dict[str, bool]:
    """Return dict mapping OSS filenames to boolean presence."""
    return {name: (project_root / name).exists() for name in _OSS_FILES}


def _run_flake8(scripts_dir: Path) -> list[dict]:
    """Run flake8 --select=F and return list of dicts with file/line/col/code/message.

    Returns [] if flake8 is not installed (returncode not in 0, 1).
    Never uses check=True.
    """
    result = subprocess.run(
        ["python3", "-m", "flake8", "--select=F", str(scripts_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        return []

    issues = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) < 4:
            continue
        file_path, line_num, col, code_msg = parts
        code_msg_stripped = code_msg.strip()
        code = code_msg_stripped.split()[0] if code_msg_stripped else ""
        issues.append({
            "file": Path(file_path).name,
            "line": line_num,
            "col": col,
            "code": code,
            "message": code_msg_stripped,
        })
    return issues


def _branch_complexity(py_file: Path) -> list[dict]:
    """Return list of dicts for functions above COMPLEXITY_THRESHOLD branch count.

    Returns [] on SyntaxError.
    """
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    hotspots = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count = sum(1 for n in ast.walk(node) if isinstance(n, _BRANCH_TYPES))
            if count >= COMPLEXITY_THRESHOLD:
                hotspots.append({
                    "file": py_file.name,
                    "name": node.name,
                    "line": node.lineno,
                    "branches": count,
                })
    return hotspots
