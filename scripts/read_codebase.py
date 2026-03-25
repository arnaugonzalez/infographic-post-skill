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


def _token_estimate(text: str) -> int:
    """Rough token count: characters // 4 (GPT-style approximation)."""
    return len(text) // 4


def _extract_python_signals(source: str) -> str:
    """Extract class names and public function signatures via AST.

    Returns a compact signal string for use as a preamble in summary_text.
    Falls back to first 500 chars on syntax errors.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source[:500]
    lines: list = []
    docstring = ast.get_docstring(tree)
    if docstring:
        lines.append(f'"""{docstring[:200]}"""')
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}:")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                lines.append(f"def {node.name}(...):")
    return "\n".join(lines)


def _infer_layers(files: list) -> list:
    """Categorize included file paths into arch.json-compatible layer dicts.

    Each layer dict has exactly: label, category, items, bg, border, label_color.
    """
    CATEGORIES = {
        "testing": {
            "label": "Testing",
            "bg": "#E8F5E9",
            "border": "#388E3C",
            "label_color": "#1B5E20",
        },
        "backend": {
            "label": "Backend / Scripts",
            "bg": "#FFF3E0",
            "border": "#F57C00",
            "label_color": "#E65100",
        },
        "docs": {
            "label": "Documentation",
            "bg": "#E3F2FD",
            "border": "#1976D2",
            "label_color": "#0D47A1",
        },
        "config": {
            "label": "Configuration",
            "bg": "#F3E5F5",
            "border": "#7B1FA2",
            "label_color": "#4A148C",
        },
        "other": {
            "label": "Other",
            "bg": "#ECEFF1",
            "border": "#546E7A",
            "label_color": "#263238",
        },
    }

    DOC_EXTS = {".md", ".txt", ".rst"}
    CONFIG_EXTS = {".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"}

    buckets: dict = {cat: [] for cat in CATEGORIES}

    for rel in files:
        p = Path(rel)
        parts = p.parts
        name = p.name
        suffix = p.suffix.lower()

        # Testing: in tests/ directory or name contains test_
        if any(part in ("tests", "test") for part in parts) or "test_" in name:
            buckets["testing"].append(name)
        # Backend/scripts: in scripts/, src/, app/
        elif any(part in ("scripts", "src", "app") for part in parts):
            buckets["backend"].append(name)
        # Docs
        elif suffix in DOC_EXTS:
            buckets["docs"].append(name)
        # Config
        elif suffix in CONFIG_EXTS:
            buckets["config"].append(name)
        else:
            buckets["other"].append(name)

    layers = []
    for cat, meta in CATEGORIES.items():
        items = buckets[cat]
        if items:
            layers.append({
                "label": meta["label"],
                "category": cat,
                "items": items,
                "bg": meta["bg"],
                "border": meta["border"],
                "label_color": meta["label_color"],
            })

    return layers


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
        token_budget: Approximate token budget for summary_text. Overridden by
            INFG_CODEBASE_TOKEN_BUDGET env var if set.

    Returns:
        A dict with keys:
            files_included  -- list of relative path strings that were read
            files_excluded  -- list of relative path strings that were skipped
                               (includes both filtered and budget-excluded files)
            summary_text    -- concatenated file contents with redaction applied
            layers          -- list of arch.json-compatible layer dicts
            connections     -- [] (populated by downstream consumers)
            root            -- absolute str(root)
            title           -- directory name
            token_estimate  -- tokens used (chars of included content // 4)
            format          -- "codebase"
    """
    root = Path(root).resolve()
    # Env var override: INFG_CODEBASE_TOKEN_BUDGET takes precedence over argument
    budget = int(os.environ.get("INFG_CODEBASE_TOKEN_BUDGET", token_budget))
    gitignore_spec = _build_noise_filter(root)

    # Collect candidate files (all non-noise, non-binary, non-credential)
    candidate_files: list = []  # list of (file_path, rel_str)
    noise_excluded: list = []

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
                noise_excluded.append(rel)
                continue

            # Binary detection
            if _is_binary(file_path):
                noise_excluded.append(rel)
                continue

            candidate_files.append((file_path, rel))

    # Prioritize: main.py / app.py / __init__.py first, then .py by size ascending,
    # then non-.py files.
    def _sort_key(item):
        fp, rel = item
        name = fp.name
        if name in ("main.py", "app.py", "__init__.py"):
            return (0, 0)
        if fp.suffix == ".py":
            try:
                size = fp.stat().st_size
            except OSError:
                size = 0
            return (1, size)
        return (2, 0)

    candidate_files.sort(key=_sort_key)

    # Apply token budget
    files_included = []
    budget_excluded = []
    content_parts = []
    used = 0

    for file_path, rel in candidate_files:
        content = _read_file_safe(file_path)
        content = _redact_content(content)
        est = _token_estimate(content)

        if used + est > budget:
            budget_excluded.append(rel)
            continue

        used += est
        files_included.append(rel)

        # Build file block with AST signals for Python files
        if file_path.suffix == ".py":
            signals = _extract_python_signals(content)
            if signals:
                block = (
                    f'<file path="{rel}">\n'
                    f"## Signals\n{signals}\n\n"
                    f"## Source\n{content}\n"
                    f"</file>"
                )
            else:
                block = f'<file path="{rel}">\n{content}\n</file>'
        else:
            block = f'<file path="{rel}">\n{content}\n</file>'

        content_parts.append(block)

    # Print explicit exclusion message when budget is hit
    if budget_excluded:
        print(
            f"Token budget ({budget:,} tokens) reached. "
            f"Excluded {len(budget_excluded)} files:"
        )
        for f in budget_excluded:
            print(f"   - {f}")

    summary_text = "\n".join(content_parts)
    files_excluded = noise_excluded + budget_excluded

    return {
        "root": str(root),
        "title": root.name,
        "summary_text": summary_text,
        "layers": _infer_layers(files_included),
        "connections": [],
        "files_included": files_included,
        "files_excluded": files_excluded,
        "token_estimate": used,
        "format": "codebase",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Read and summarize a codebase."
    )
    # Positional directory argument (new interface)
    parser.add_argument("directory", nargs="?", type=Path, default=None,
                        help="Directory to read")
    # Legacy --root flag (backward compatibility)
    parser.add_argument("--root", default=None, help="Directory to read (legacy flag)")
    parser.add_argument(
        "--budget", type=int, default=TOKEN_BUDGET_DEFAULT,
        help=f"Token budget (default: {TOKEN_BUDGET_DEFAULT:,})"
    )
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Write JSON report to file (default: stdout)")
    args = parser.parse_args()

    # Resolve directory: positional arg takes priority, then --root, then cwd
    if args.directory is not None:
        target = args.directory
    elif args.root is not None:
        target = Path(args.root)
    else:
        target = Path(".")

    if not target.is_dir():
        print(f"Error: {target} is not a directory", file=sys.stderr)
        sys.exit(1)

    report = read_codebase(target, token_budget=args.budget)

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {args.output}")
        print(f"Files included: {len(report['files_included'])}")
        print(f"Files excluded: {len(report['files_excluded'])}")
        print(f"Token estimate: {report['token_estimate']:,}")
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    _main()
