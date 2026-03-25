#!/usr/bin/env python3
"""OSS Quality Audit — produces QUALITY_AUDIT.md."""
import argparse
import ast
import json
import subprocess
import sys
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


# ---------------------------------------------------------------------------
# Orchestrator helpers
# ---------------------------------------------------------------------------

def _collect_docstring_gaps(scripts_dir: Path) -> list[str]:
    """Glob scripts_dir for *.py files and return all missing-docstring entries."""
    gaps: list[str] = []
    if scripts_dir.is_dir():
        for py_file in sorted(scripts_dir.glob("*.py")):
            gaps.extend(_check_docstrings(py_file))
    return gaps


def _collect_hotspots(scripts_dir: Path) -> list[dict]:
    """Glob scripts_dir for *.py files and return all high-complexity function entries."""
    hotspots: list[dict] = []
    if scripts_dir.is_dir():
        for py_file in sorted(scripts_dir.glob("*.py")):
            hotspots.extend(_branch_complexity(py_file))
    return hotspots


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_audit(root: Path) -> dict:
    """Collect all five audit sections into a single dict.

    Returns dict with keys: coverage, docstrings_missing, oss_files,
    flake8_issues, complexity_hotspots.
    """
    scripts_dir = root / "scripts"
    return {
        "coverage": _run_coverage(root),
        "docstrings_missing": _collect_docstring_gaps(scripts_dir),
        "oss_files": _check_oss_files(root),
        "flake8_issues": _run_flake8(scripts_dir),
        "complexity_hotspots": _collect_hotspots(scripts_dir),
    }


def _render(audit: dict) -> str:
    """Build a Markdown Quality Audit Report string from audit dict."""
    lines: list[str] = []

    lines.append("# Quality Audit Report")
    lines.append("")
    lines.append("*Generated by oss_audit.py*")
    lines.append("")

    # --- Test Coverage ---
    lines.append("## Test Coverage")
    lines.append("")
    coverage = audit.get("coverage", {})
    if coverage:
        lines.append("| Module | Coverage |")
        lines.append("|--------|----------|")
        for path, pct in sorted(coverage.items()):
            lines.append(f"| {path} | {pct:.1f}% |")
    else:
        lines.append(
            "No coverage data available."
            " Install `requirements-audit.txt` and run again."
        )
    lines.append("")

    # --- Docstring Coverage ---
    lines.append("## Docstring Coverage")
    lines.append("")
    missing_docs = audit.get("docstrings_missing", [])
    if missing_docs:
        lines.append("Functions/classes missing docstrings:")
        lines.append("")
        for entry in missing_docs:
            lines.append(f"- {entry}")
    else:
        lines.append("All functions and classes have docstrings.")
    lines.append("")

    # --- OSS Baseline Files ---
    lines.append("## OSS Baseline Files")
    lines.append("")
    oss_files = audit.get("oss_files", {})
    if oss_files:
        lines.append("| File | Present |")
        lines.append("|------|---------|")
        for name, present in sorted(oss_files.items()):
            status = "Yes" if present else "**MISSING**"
            lines.append(f"| {name} | {status} |")
    lines.append("")

    # --- Code Quality (Flake8) ---
    lines.append("## Code Quality (Flake8)")
    lines.append("")
    flake8_issues = audit.get("flake8_issues", [])
    if flake8_issues:
        lines.append("| File | Line | Code | Message |")
        lines.append("|------|------|------|---------|")
        for issue in flake8_issues:
            lines.append(
                f"| {issue['file']} | {issue['line']} | {issue['code']} | {issue['message']} |"
            )
    else:
        lines.append("No logical errors found.")
    lines.append("")

    # --- Complexity Hotspots ---
    lines.append("## Complexity Hotspots")
    lines.append("")
    hotspots = audit.get("complexity_hotspots", [])
    lines.append(f"Functions with >= {COMPLEXITY_THRESHOLD} branch nodes:")
    lines.append("")
    if hotspots:
        lines.append("| File | Function | Line | Branches |")
        lines.append("|------|----------|------|----------|")
        for h in hotspots:
            lines.append(f"| {h['file']} | {h['name']} | {h['line']} | {h['branches']} |")
    else:
        lines.append("No high-complexity functions found.")
    lines.append("")

    return "\n".join(lines)


def write_report(audit: dict, out_path: Path) -> None:
    """Write the rendered Markdown audit report to out_path."""
    out_path.write_text(_render(audit), encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> None:
    """CLI entry point: parse --root, run audit, write QUALITY_AUDIT.md."""
    parser = argparse.ArgumentParser(description="OSS Quality Audit")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    audit = run_audit(root)
    write_report(audit, root / "QUALITY_AUDIT.md")


if __name__ == "__main__":
    main()
