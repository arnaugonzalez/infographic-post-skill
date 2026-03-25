#!/usr/bin/env python3
"""
Infographic Skill — Codebase Reader

Reads a directory tree with noise filtering (build artifacts, binary files,
gitignore patterns) and credential safety (unconditional credential file skip
+ content redaction at read time).

Usage:
    python scripts/read_codebase.py --root /path/to/project [--budget 40000]
    python scripts/read_codebase.py --root . --output report.json
"""

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path

try:
    import pathspec
    _PATHSPEC_OK = True
except ImportError:
    _PATHSPEC_OK = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SKIP_DIRS: frozenset = frozenset({
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "dist", "build", ".tox", ".eggs", ".mypy_cache",
    ".pytest_cache", "htmlcov", ".coverage", ".ruff_cache",
    ".github", ".gitlab", ".husky", ".vscode", ".idea", ".claude",
    "out", "target", ".next", ".nuxt", ".nyc_output",
})

DEFAULT_SKIP_EXTENSIONS: frozenset = frozenset({
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".bin",
    ".lock", ".min.js", ".min.css",
})

DEFAULT_CREDENTIAL_FILES: frozenset = frozenset({
    ".env", ".env.local", ".env.production", ".env.staging",
    "credentials.json", "service_account.json",
})

CREDENTIAL_EXTENSIONS: frozenset = frozenset({
    ".pem", ".key", ".p12", ".pfx", ".jks",
})

TOKEN_BUDGET_DEFAULT: int = 40_000
MAX_FILE_BYTES: int = 100_000


# ---------------------------------------------------------------------------
# Secret patterns — do NOT import from generate_pretty.py; keep independent
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    re.compile(r"AIza[a-zA-Z0-9_-]{30,}"),
    re.compile(r"sk-or-v1-[a-zA-Z0-9_-]{30,}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36,}"),
    re.compile(
        r"(?i)(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?([A-Za-z0-9_/+=]{16,})['\"]?"
    ),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _is_binary(path: Path) -> bool:
    """Return True if the file appears to be binary (contains null bytes)."""
    try:
        chunk = path.read_bytes()[:1024]
        return b"\x00" in chunk
    except Exception:
        return True


def _is_credential_file(path: Path) -> bool:
    """Return True if the file is a known credential file that must be skipped."""
    name = path.name
    suffix = path.suffix.lower()
    # Exact name match against known credential files
    if name in DEFAULT_CREDENTIAL_FILES:
        return True
    # Credential extensions (.pem, .key, etc.)
    if suffix in CREDENTIAL_EXTENSIONS:
        return True
    # service_account*.json pattern
    if name.startswith("service_account") and suffix == ".json":
        return True
    return False


def _redact_content(text: str) -> str:
    """Apply all secret patterns to text, replacing matches with [REDACTED]."""
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def _build_noise_filter(root: Path):
    """Load .gitignore as a pathspec filter. Returns None if pathspec unavailable or no .gitignore."""
    if not _PATHSPEC_OK:
        return None
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return None
    try:
        lines = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
        return pathspec.PathSpec.from_lines("gitignore", lines)
    except Exception:
        return None


def _read_file_safe(path: Path, max_bytes: int = MAX_FILE_BYTES) -> str:
    """Read a text file safely, returning empty string on error."""
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except Exception:
        return ""


def _should_skip_dir(dirname: str) -> bool:
    """Return True if a directory name should be pruned during walking."""
    return dirname in DEFAULT_SKIP_DIRS


def _should_skip_file(path: Path, gitignore_spec, root: Path) -> bool:
    """Return True if the file should be excluded from the report."""
    # Extension-based skip
    suffix = path.suffix.lower()
    # Handle compound extensions like .min.js
    name = path.name
    if suffix in DEFAULT_SKIP_EXTENSIONS:
        return True
    if name.endswith(".min.js") or name.endswith(".min.css"):
        return True
    # Credential file skip
    if _is_credential_file(path):
        return True
    # Gitignore pattern match
    if gitignore_spec is not None:
        try:
            rel = str(path.relative_to(root))
            if gitignore_spec.match_file(rel):
                return True
        except ValueError:
            pass
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_codebase(root, token_budget: int = TOKEN_BUDGET_DEFAULT) -> dict:
    """Read a codebase directory tree with noise filtering and credential safety.

    Args:
        root: Path (or str) to the directory root.
        token_budget: Approximate token budget for summary_text (placeholder for Plan 02).

    Returns:
        A dict with keys:
            files_included  -- list of relative path strings that were read
            files_excluded  -- list of relative path strings that were skipped
            summary_text    -- concatenated file contents with redaction applied
            layers          -- [] (populated in Plan 02)
            connections     -- [] (populated in Plan 02)
            root            -- str(root)
            title           -- directory name
            token_estimate  -- rough character count / 4
            format          -- "codebase"
    """
    root = Path(root)
    gitignore_spec = _build_noise_filter(root)

    files_included = []
    files_excluded = []
    content_parts = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip directories in-place so os.walk does not descend into them
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]

        current_dir = Path(dirpath)

        for filename in sorted(filenames):
            file_path = current_dir / filename
            try:
                rel = str(file_path.relative_to(root))
            except ValueError:
                rel = str(file_path)

            # Check extension and credential rules
            if _should_skip_file(file_path, gitignore_spec, root):
                files_excluded.append(rel)
                continue

            # Binary detection
            if _is_binary(file_path):
                files_excluded.append(rel)
                continue

            # Read and redact content
            content = _read_file_safe(file_path)
            content = _redact_content(content)

            files_included.append(rel)
            content_parts.append(f'<file path="{rel}">\n{content}\n</file>')

    summary_text = "\n".join(content_parts)
    token_estimate = len(summary_text) // 4

    return {
        "files_included": files_included,
        "files_excluded": files_excluded,
        "summary_text": summary_text,
        "layers": [],
        "connections": [],
        "root": str(root),
        "title": root.name,
        "token_estimate": token_estimate,
        "format": "codebase",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Read a codebase directory with noise filtering and credential safety."
    )
    parser.add_argument("--root", default=".", help="Directory to read (default: .)")
    parser.add_argument(
        "--budget", type=int, default=TOKEN_BUDGET_DEFAULT,
        help=f"Token budget (default: {TOKEN_BUDGET_DEFAULT})"
    )
    parser.add_argument("--output", help="Write JSON report to this file (default: stdout)")
    args = parser.parse_args()

    report = read_codebase(Path(args.root), token_budget=args.budget)
    output = json.dumps(report, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report written to {args.output}")
        print(f"Files included: {len(report['files_included'])}")
        print(f"Files excluded: {len(report['files_excluded'])}")
        print(f"Token estimate: {report['token_estimate']:,}")
    else:
        print(output)


if __name__ == "__main__":
    _main()
