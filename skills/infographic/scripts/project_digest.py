"""Project digest — a compact, architecture-first summary of a codebase.

read_codebase.py concatenates raw source until a token budget runs out, which
drops exactly the files that describe architecture (README, package.json,
pubspec.yaml, docker-compose, Terraform) and whole non-Python sub-projects.
This module builds a small digest from those high-signal files instead:

  1. directory tree (depth-limited, with file counts per directory)
  2. language histogram
  3. README / CLAUDE.md excerpts
  4. dependency manifests reduced to dependency names
  5. deployment files reduced to services / images / resources

Typical output is 4-10k tokens, ~5x smaller than the raw-source report, and it
covers every sub-project of a monorepo.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from read_codebase import (
    _build_noise_filter,
    _is_binary,
    _read_file_safe,
    _redact_content,
    _should_skip_dir,
    _should_skip_file,
)

DIGEST_CHAR_BUDGET = 36_000
TREE_MAX_DEPTH = 3
TREE_MAX_LINES = 140
MANIFEST_MAX_DEPTH = 4

_DOC_FILES = ("README.md", "README.rst", "README", "CLAUDE.md", "ARCHITECTURE.md")
_DOC_CHARS = {0: 3500, 1: 1500}  # root docs get more room than nested ones

_LANG_BY_EXT = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
    ".jsx": "JavaScript", ".dart": "Dart", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".swift": "Swift", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".tf": "Terraform", ".sql": "SQL",
    ".vue": "Vue", ".svelte": "Svelte", ".sh": "Shell", ".html": "HTML",
    ".css": "CSS", ".scss": "CSS",
}


def _dep_names_from_package_json(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ""
    parts = [f"name: {data.get('name', '?')}"]
    for key in ("dependencies", "devDependencies"):
        deps = data.get(key) or {}
        if deps:
            parts.append(f"{key}: {', '.join(sorted(deps))}")
    scripts = data.get("scripts") or {}
    if scripts:
        parts.append(f"scripts: {', '.join(sorted(scripts))}")
    return "\n".join(parts)


def _dep_names_from_requirements(text: str) -> str:
    names = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        names.append(re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0])
    return "dependencies: " + ", ".join(names) if names else ""


def _yaml_section_keys(text: str, section: str) -> list[str]:
    """Return the direct child keys of a top-level YAML section (no yaml dependency)."""
    keys, inside, indent = [], False, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(rf"^{section}:\s*$", line):
            inside, indent = True, None
            continue
        if inside:
            if not line.startswith((" ", "\t")):
                break
            cur = len(line) - len(line.lstrip())
            if indent is None:
                indent = cur
            if cur == indent:
                m = re.match(r"\s*([\w.\-/]+):", line)
                if m:
                    keys.append(m.group(1))
    return keys


def _summarize_pubspec(text: str) -> str:
    deps = _yaml_section_keys(text, "dependencies")
    name = re.search(r"^name:\s*(\S+)", text, re.M)
    return f"name: {name.group(1) if name else '?'}\ndependencies: {', '.join(deps)}"


def _summarize_compose(text: str) -> str:
    services = _yaml_section_keys(text, "services")
    images = sorted(set(re.findall(r"^\s*image:\s*['\"]?([^\s'\"]+)", text, re.M)))
    return f"services: {', '.join(services)}\nimages: {', '.join(images)}"


def _summarize_dockerfile(text: str) -> str:
    froms = re.findall(r"^FROM\s+(\S+)", text, re.M | re.I)
    cmd = re.findall(r"^(?:CMD|ENTRYPOINT)\s+(.+)$", text, re.M)
    return f"FROM {', '.join(froms)}" + (f"\nCMD {cmd[-1][:120]}" if cmd else "")


def _summarize_terraform(text: str) -> str:
    providers = sorted(set(re.findall(r'provider\s+"([\w-]+)"', text)))
    resources = sorted(set(re.findall(r'resource\s+"([\w-]+)"', text)))
    return f"providers: {', '.join(providers)}\nresources: {', '.join(resources)}"


def _summarize_toml(text: str) -> str:
    """pyproject.toml / Cargo.toml: keep name + dependency lines only."""
    keep = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("name", "[project", "[tool.poetry.dependencies", "[dependencies")) \
                or re.match(r'^"?[\w.\-]+(\[.*\])?\s*[<>=~"]', s) or s.startswith('"'):
            keep.append(s)
    return "\n".join(keep)[:1500]


def _summarize_go_mod(text: str) -> str:
    mods = re.findall(r"^\s*([\w./\-]+)\s+v[\d.]+", text, re.M)
    return "require: " + ", ".join(m.rsplit("/", 1)[-1] for m in mods)


def _manifest_summarizer(name: str):
    lower = name.lower()
    if lower == "package.json":
        return _dep_names_from_package_json
    if lower.startswith("requirements") and lower.endswith(".txt"):
        return _dep_names_from_requirements
    if lower == "pubspec.yaml":
        return _summarize_pubspec
    if re.match(r"^(docker-)?compose[\w.\-]*\.ya?ml$", lower):
        return _summarize_compose
    if lower == "dockerfile" or lower.startswith("dockerfile."):
        return _summarize_dockerfile
    if lower.endswith(".tf"):
        return _summarize_terraform
    if lower in ("pyproject.toml", "cargo.toml"):
        return _summarize_toml
    if lower == "go.mod":
        return _summarize_go_mod
    return None


def build_digest(root, char_budget: int = DIGEST_CHAR_BUDGET) -> dict:
    """Walk *root* and return {"summary_text", "languages", "manifests", "root", "title"}."""
    root = Path(root).resolve()
    spec = _build_noise_filter(root)
    lang_counts: Counter = Counter()
    tree_lines: list[str] = []
    docs: list[tuple[int, str, str]] = []
    manifests: list[tuple[str, str]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        cur = Path(dirpath)
        rel_dir = cur.relative_to(root)
        depth = 0 if str(rel_dir) == "." else len(rel_dir.parts)
        dirnames[:] = sorted(
            d for d in dirnames
            if not _should_skip_dir(d) and not d.startswith(".")
            and not (spec and spec.match_file(str((rel_dir / d)) + "/"))
        )
        files = [f for f in sorted(filenames) if not _should_skip_file(cur / f, spec, root)]
        for f in files:
            lang = _LANG_BY_EXT.get(Path(f).suffix.lower())
            if lang:
                lang_counts[lang] += 1
        if depth <= TREE_MAX_DEPTH and len(tree_lines) < TREE_MAX_LINES:
            label = "." if depth == 0 else rel_dir.name
            tree_lines.append(f"{'  ' * depth}{label}/ ({len(files)} files)")
        for f in files:
            path = cur / f
            if f in _DOC_FILES and depth <= 1:
                docs.append((depth, str(rel_dir / f), _read_file_safe(path, 20_000)))
            summarizer = _manifest_summarizer(f)
            if summarizer and depth <= MANIFEST_MAX_DEPTH and not _is_binary(path):
                summary = summarizer(_read_file_safe(path, 60_000)).strip()
                if summary:
                    manifests.append((str(rel_dir / f), summary))

    sections = [f"# Project: {root.name}", "## Directory tree", "\n".join(tree_lines)]
    sections.append("## Languages (file counts)")
    sections.append(", ".join(f"{k}: {v}" for k, v in lang_counts.most_common()))
    sections.append("## Dependency & deployment manifests")
    for rel, summary in manifests:
        sections.append(f"### {rel}\n{summary}")
    sections.append("## Documentation excerpts")
    for depth, rel, text in sorted(docs):
        sections.append(f"### {rel}\n{text[:_DOC_CHARS.get(depth, 1500)]}")

    text = _redact_content("\n\n".join(sections))
    if len(text) > char_budget:
        text = text[:char_budget] + "\n…[digest truncated]"
    return {
        "root": str(root),
        "title": root.name,
        "summary_text": text,
        "languages": dict(lang_counts),
        "manifests": [rel for rel, _ in manifests],
        "token_estimate": len(text) // 4,
        "format": "digest",
    }


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(build_digest(target)["summary_text"])
