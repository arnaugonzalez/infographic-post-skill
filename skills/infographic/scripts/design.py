"""Art direction for the HTML renderer: archetypes, canvas formats, reference pages, brief."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent.parent
_PROMPTS_DIR = _SKILL_DIR / "scripts" / "prompts"
DEFAULT_STYLE_DIR = _SKILL_DIR / "style"

FORMATS = {"portrait": (1080, 1350), "square": (1080, 1080), "landscape": (1280, 640)}
DEFAULT_FORMAT = "portrait"
DEFAULT_ARCHETYPE = "editorial"
# Pre-0.2 style names keep working.
LEGACY_STYLES = {"modern-dark": "blueprint", "modern-light": "editorial", "illustrated": "swiss"}
MAX_EXAMPLES = 2
MAX_EXAMPLE_CHARS = 6000


def _load_archetypes() -> dict[str, str]:
    text = (_PROMPTS_DIR / "archetypes.md").read_text(encoding="utf-8")
    parts = re.split(r"^# (\w+)\s*$", text, flags=re.M)
    return {name: body.strip() for name, body in zip(parts[1::2], parts[2::2])}


ARCHETYPES = _load_archetypes()


def resolve_archetype(style: str | None) -> str:
    name = LEGACY_STYLES.get(style or "", style or DEFAULT_ARCHETYPE)
    if name not in ARCHETYPES:
        raise ValueError(f"unknown style {style!r}; choose one of: {', '.join(ARCHETYPES)}")
    return name


def canvas_size(fmt: str | None) -> tuple[int, int]:
    try:
        return FORMATS[fmt or DEFAULT_FORMAT]
    except KeyError:
        raise ValueError(f"unknown format {fmt!r}; choose one of: {', '.join(FORMATS)}") from None


def load_examples(style_dir: str | Path | None = None) -> list[str]:
    """Reference pages the model should match in restraint and voice (not content)."""
    root = Path(style_dir or os.environ.get("INFG_STYLE_DIR") or DEFAULT_STYLE_DIR)
    if not root.is_dir():
        return []
    pages = sorted(root.glob("*.html"))[:MAX_EXAMPLES]
    return [p.read_text(encoding="utf-8")[:MAX_EXAMPLE_CHARS] for p in pages]


def _examples_block(examples: list[str]) -> str:
    if not examples:
        return ""
    pages = "\n\n".join(f"```html\n{e}\n```" for e in examples)
    return ("REFERENCE PAGES — the author's own graphics. Match their restraint, hierarchy and "
            "typographic voice; do not copy their content, wording or colors unless the archetype "
            f"asks for them.\n\n{pages}")


def render_brief(spec: dict, *, kind: str = "architecture", style: str | None = None,
                 fmt: str | None = None, style_dir: str | Path | None = None) -> str:
    archetype = resolve_archetype(style)
    width, height = canvas_size(fmt)
    template = (_PROMPTS_DIR / "brief.md").read_text(encoding="utf-8").strip()
    return template.format(
        kind=kind, width=width, height=height,
        spec=json.dumps(spec, indent=1, ensure_ascii=False),
        archetype=archetype, archetype_brief=ARCHETYPES[archetype],
        examples=_examples_block(load_examples(style_dir)),
    )
