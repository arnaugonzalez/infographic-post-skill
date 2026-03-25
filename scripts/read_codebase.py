#!/usr/bin/env python3
"""
Infographic Skill — Codebase Reader

Reads a directory tree with noise filtering and credential safety,
returning a structured report suitable for LLM context injection.

Usage:
    python scripts/read_codebase.py --root /path/to/project
"""

from pathlib import Path

# Stub: minimal exports so tests can import the module.
# Task 1 (RED phase): This stub intentionally returns empty data so tests fail.

DEFAULT_SKIP_DIRS = frozenset()
DEFAULT_CREDENTIAL_FILES = frozenset()


def read_codebase(root, token_budget=40_000):
    """Read a codebase directory tree with noise filtering and credential safety.

    Returns a dict with keys: files_included, files_excluded, summary_text,
    layers, connections, root, title, token_estimate, format.
    """
    return {
        "files_included": [],
        "files_excluded": [],
        "summary_text": "",
        "layers": [],
        "connections": [],
        "root": str(root),
        "title": "",
        "token_estimate": 0,
        "format": "codebase",
    }
