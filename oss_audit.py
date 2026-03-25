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
    raise NotImplementedError


def _check_docstrings(py_file: Path) -> list[str]:
    raise NotImplementedError


def _check_oss_files(project_root: Path) -> dict[str, bool]:
    raise NotImplementedError


def _run_flake8(scripts_dir: Path) -> list[dict]:
    raise NotImplementedError


def _branch_complexity(py_file: Path) -> list[dict]:
    raise NotImplementedError
