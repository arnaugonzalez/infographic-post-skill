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

TECH_SEPARATOR = "--- TECHNICAL POST ---"
BIZ_SEPARATOR = "--- BUSINESS POST ---"

# ---------------------------------------------------------------------------
# Cross-script imports
# ---------------------------------------------------------------------------

sys.path.insert(0, str(_SKILL_DIR / "scripts"))
from read_codebase import read_codebase  # noqa: E402

import requests as _requests_lib  # noqa: E402

# ---------------------------------------------------------------------------
# OpenRouter HTTP adapter
# ---------------------------------------------------------------------------


def _call_openrouter(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Call OpenRouter chat completions API and return the assistant message text.

    Exits with code 1 on auth or server errors.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    resp = _requests_lib.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=120,
    )
    if resp.status_code == 401:
        print("OpenRouter API key is invalid (401)")
        sys.exit(1)
    if resp.status_code == 402:
        print("OpenRouter: insufficient credits (402)")
        sys.exit(1)
    if resp.status_code != 200:
        print(f"OpenRouter error {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)
    return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# System prompt builders
# ---------------------------------------------------------------------------


def _build_technical_system_prompt(language: str) -> str:
    """Return system prompt for the technical-angle LinkedIn post."""
    lang_name = LANG_NAMES[language]
    return (
        f"Language directive: respond exclusively in {lang_name}. "
        "You are a LinkedIn content expert writing for software engineers. "
        "Open with a concrete implementation detail — a specific technology, "
        "architectural pattern, or engineering constraint that was solved. "
        "Hook the reader in the first line with a surprising fact or bold claim "
        "about the implementation. "
        "Do not use template placeholders or generic filler text. "
        "End with a specific call-to-action that invites engineers to comment "
        "or share their own implementation approach. "
        "Target length: your post must be 800 to 1,600 characters long. "
        f"CRITICAL REMINDER: Every sentence must be written in {lang_name} only."
    )


def _build_business_system_prompt(language: str) -> str:
    """Return system prompt for the business-angle LinkedIn post."""
    lang_name = LANG_NAMES[language]
    return (
        f"Output language: write the entire post in {lang_name}. "
        "You are a LinkedIn content strategist writing for product managers and executives. "
        "Lead with an outcome or result — what changed for the user, team, or product "
        "after this capability was shipped. "
        "Quantify the value wherever possible and frame it around business impact, "
        "not technical mechanics. "
        "Avoid jargon; speak the language of strategy and product delivery. "
        "Close with a call-to-action asking readers to share how they measure similar outcomes. "
        "Character range: aim for 800 to 1,600 characters in your response. "
        f"FINAL NOTE: All content must appear in {lang_name}, without exception."
    )


# ---------------------------------------------------------------------------
# Post generation with length retry
# ---------------------------------------------------------------------------


def _generate_post(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Generate a LinkedIn post, retrying once if length is outside 800-1600 chars."""
    post = _call_openrouter(user_prompt, system_prompt, model, api_key)
    char_count = len(post)
    if not (800 <= char_count <= 1600):
        retry_prompt = (
            user_prompt
            + f"\n\nYour previous response was {char_count} characters. "
            "Rewrite it to be between 800 and 1,600 characters, "
            "keeping the structure and language."
        )
        post = _call_openrouter(retry_prompt, system_prompt, model, api_key)
    return post


# ---------------------------------------------------------------------------
# Output writer
# ---------------------------------------------------------------------------


def _write_output(tech_post: str, biz_post: str) -> None:
    """Write both posts to linkedin_posts.md in cwd and print to stdout."""
    out_path = Path.cwd() / "linkedin_posts.md"
    content = (
        f"{TECH_SEPARATOR}\n\n{tech_post}\n\n"
        f"{BIZ_SEPARATOR}\n\n{biz_post}\n"
    )
    out_path.write_text(content, encoding="utf-8")

    tech_chars = len(tech_post)
    biz_chars = len(biz_post)
    print(f"{TECH_SEPARATOR} ({tech_chars:,} chars)\n")
    print(tech_post)
    print()
    print(f"{BIZ_SEPARATOR} ({biz_chars:,} chars)\n")
    print(biz_post)
    print()
    print(f"\u2713  Saved to linkedin_posts.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI args, read codebase, generate two posts, write output."""
    parser = _build_parser()
    args = parser.parse_args()

    _load_dotenv(_ENV_PATH)

    api_key = os.environ.get("INFG_OPENROUTER_API_KEY", "").strip()
    model = os.environ.get("INFG_LLM_MODEL", "").strip()

    if not api_key:
        print("Set INFG_OPENROUTER_API_KEY in .env or environment")
        sys.exit(1)
    if not model:
        print("Set INFG_LLM_MODEL in .env or environment")
        sys.exit(1)

    report = read_codebase(args.directory)
    user_prompt = (
        f"Here is a codebase summary:\n\n{report['summary_text']}\n\n"
        "Write a LinkedIn post about this project."
    )

    tech_post = _generate_post(
        user_prompt, _build_technical_system_prompt(args.language), model, api_key
    )
    biz_post = _generate_post(
        user_prompt, _build_business_system_prompt(args.language), model, api_key
    )
    _write_output(tech_post, biz_post)


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
    _build_parser().parse_args()
    main()
