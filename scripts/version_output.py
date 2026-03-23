#!/usr/bin/env python3
"""
Infographic Skill — Versioned Output Directory Manager

Manages versioned output directories for infographic iterations.
Supports "next version" / "nueva version" / any language trigger.

Usage:
    # Create or advance to next version (prints path to stdout):
    OUTPUT=$(python scripts/version_output.py --root .)

    # List existing versions:
    python scripts/version_output.py --root . --list

    # Override output subdirectory name:
    python scripts/version_output.py --root . --dir designs

Directory structure managed:
    infographics/        <- or designs/, generated/, output/ if already exists
    ├── v1/              <- archived versions (read-only history)
    ├── v2/
    ├── v3/
    └── v4_last/         <- always the current / latest version
"""

import argparse
import re
import sys
from pathlib import Path


# Candidate subdirectory names (in preference order)
_CANDIDATE_DIRS = ["infographics", "designs", "generated", "output"]


def _find_output_base(root: Path, dir_override: str | None = None) -> Path:
    """Resolve the output base directory under root.

    If --dir is given, use that name directly.
    Otherwise auto-detect an existing candidate directory, defaulting to
    'infographics/' if none exists yet.
    """
    if dir_override:
        return root / dir_override
    for name in _CANDIDATE_DIRS:
        candidate = root / name
        if candidate.is_dir():
            return candidate
    return root / "infographics"


def _scan_versions(base: Path) -> dict[int, Path]:
    """Return mapping of version number -> directory path for all v{N} and v{N}_last dirs."""
    versions: dict[int, Path] = {}
    if not base.exists():
        return versions
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        # Match v{N} or v{N}_last
        m = re.fullmatch(r"v(\d+)(?:_last)?", entry.name)
        if m:
            n = int(m.group(1))
            # Prefer _last over archived when same number (shouldn't occur)
            if n not in versions or entry.name.endswith("_last"):
                versions[n] = entry
    return versions


def _last_dir(base: Path) -> Path | None:
    """Return the v{N}_last directory if it exists, else None."""
    if not base.exists():
        return None
    for entry in base.iterdir():
        if entry.is_dir() and re.fullmatch(r"v\d+_last", entry.name):
            return entry
    return None


def _count_files(d: Path) -> tuple[int, list[str]]:
    """Return (count, sorted unique extensions) for files directly in d."""
    if not d.exists():
        return 0, []
    files = [f for f in d.iterdir() if f.is_file()]
    exts = sorted({f.suffix for f in files if f.suffix})
    return len(files), exts


def cmd_list(base: Path) -> None:
    """Print a formatted version table to stdout."""
    versions = _scan_versions(base)
    if not versions:
        print(f"  No versions found in: {base}")
        return
    print(f"  Versions in: {base}")
    print("  " + "\u2500" * 42)
    for n in sorted(versions):
        d = versions[n]
        count, exts = _count_files(d)
        ext_str = f"  [{', '.join(exts)}]" if exts else ""
        current_marker = "  <- current" if d.name.endswith("_last") else ""
        print(f"  {d.name:<16}{count} file(s){ext_str}{current_marker}")


def cmd_next(base: Path) -> None:
    """Create the next version directory, archive the previous _last, print path to stdout."""
    existing_last = _last_dir(base)

    if existing_last is None:
        # First call — no versions yet
        base.mkdir(parents=True, exist_ok=True)
        new_dir = base / "v1_last"
        new_dir.mkdir(exist_ok=True)
        print(str(new_dir.resolve()))
    else:
        # Parse current version number
        m = re.fullmatch(r"v(\d+)_last", existing_last.name)
        n = int(m.group(1))

        # Archive: rename v{N}_last -> v{N}
        archived = existing_last.parent / f"v{n}"
        existing_last.rename(archived)
        print(f"Archived v{n}_last -> v{n}", file=sys.stderr)

        # Create v{N+1}_last
        new_dir = base / f"v{n + 1}_last"
        new_dir.mkdir(parents=True, exist_ok=True)
        print(str(new_dir.resolve()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage versioned output directories for infographic iterations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--root",
        required=True,
        metavar="PATH",
        help="Project root directory to manage versions in.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing versions and exit.",
    )
    parser.add_argument(
        "--dir",
        metavar="NAME",
        default=None,
        help=(
            "Override the output subdirectory name "
            "(default: auto-detect from infographics/, designs/, generated/, output/)."
        ),
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    base = _find_output_base(root, args.dir)

    if args.list:
        cmd_list(base)
    else:
        cmd_next(base)


if __name__ == "__main__":
    main()
