#!/usr/bin/env python3
"""
Infographic Skill — LinkedIn Post Generator

Reads a codebase via read_codebase(), makes two separate OpenRouter LLM calls
(technical angle + business angle) with structurally distinct system prompts,
enforces output language via system prompt with closing-line repetition,
retries once if character count is outside 800-1600, and writes both posts to
linkedin_posts.md + stdout.

Usage:
    python scripts/generate_posts.py <directory> [--language {en,es,fr,de,pt,it}]
"""
import argparse
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Skill root + env loader
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _SKILL_DIR / ".env"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "it"]

LANG_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
}

# ---------------------------------------------------------------------------
# Stubs (replaced in Task 2 GREEN phase)
# ---------------------------------------------------------------------------

import requests as _requests_lib  # noqa: E402


def _call_openrouter(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    raise NotImplementedError


def _build_technical_system_prompt(language: str) -> str:
    raise NotImplementedError


def _build_business_system_prompt(language: str) -> str:
    raise NotImplementedError


def _generate_post(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    raise NotImplementedError


def _write_output(tech_post: str, biz_post: str) -> None:
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate two LinkedIn posts (technical + business) from a codebase."
    )
    parser.add_argument("directory", help="Path to codebase directory to analyse.")
    parser.add_argument(
        "--language",
        choices=SUPPORTED_LANGUAGES,
        default="en",
        help="Output language for posts (default: en).",
    )
    return parser


if __name__ == "__main__":
    _parser = _build_parser()
    _args = _parser.parse_args()
    main()
