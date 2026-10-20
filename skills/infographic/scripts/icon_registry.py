"""Icon registry — resolves technology names to inline SVG strings.

Uses the ``simplepycons`` library for brand icons with an emoji fallback
when a matching icon cannot be found.
"""

from __future__ import annotations

import re
from typing import Dict

# ---------------------------------------------------------------------------
# Alias map — maps common human-readable tech names to simplepycons getter
# slugs (the part between ``get_`` and ``_icon``).
# ---------------------------------------------------------------------------

_ALIAS_MAP: Dict[str, str] = {
    # Frontend
    "react": "react",
    "react native": "react",
    "next.js": "nextdotjs",
    "nextjs": "nextdotjs",
    "vue": "vuedotjs",
    "vue.js": "vuedotjs",
    "vuejs": "vuedotjs",
    "angular": "angular",
    "svelte": "svelte",
    "tailwind css": "tailwindcss",
    "tailwindcss": "tailwindcss",
    "typescript": "typescript",
    "javascript": "javascript",
    "html5": "html5",
    "html": "html5",
    "css3": "css3",
    "css": "css3",
    "vite": "vite",
    "webpack": "webpack",
    "expo": "expo",
    # Backend
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "node.js": "nodedotjs",
    "nodejs": "nodedotjs",
    "nestjs": "nestjs",
    "express": "express",
    "spring": "spring",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "ruby on rails": "rubyonrails",
    "rails": "rubyonrails",
    "laravel": "laravel",
    ".net": "dotnet",
    "dotnet": "dotnet",
    # Database
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "redis": "redis",
    "sqlite": "sqlite",
    "supabase": "supabase",
    "firebase": "firebase",
    "cassandra": "apachecassandra",
    "dynamodb": "amazondynamodb",
    "drizzle orm": "drizzle",
    "drizzle": "drizzle",
    # Cloud / Infra
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "aws": "amazonaws",
    "amazon web services": "amazonaws",
    "google cloud": "googlecloud",
    "gcp": "googlecloud",
    "azure": "microsoftazure",
    "terraform": "terraform",
    "github": "github",
    "github actions": "githubactions",
    "gitlab": "gitlab",
    "vercel": "vercel",
    "netlify": "netlify",
    "cloudflare": "cloudflare",
    "nginx": "nginx",
    "railway": "railway",
    # AI / ML
    "openai": "openai",
    "langchain": "langchain",
    "anthropic": "anthropic",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
    "pytorch": "pytorch",
    "tensorflow": "tensorflow",
    # Auth
    "auth0": "auth0",
    "clerk": "clerk",
    # Queue / Messaging
    "kafka": "apachekafka",
    "apache kafka": "apachekafka",
    "rabbitmq": "rabbitmq",
    "celery": "celery",
    # Other
    "python": "python",
    "playwright": "playwright",
    "matplotlib": "matplotlib",  # may not exist — emoji fallback
    "pillow": "python",  # Pillow is a Python library
    "numpy": "numpy",
    "pandas": "pandas",
    "elasticsearch": "elasticsearch",
    "grafana": "grafana",
    "prometheus": "prometheus",
    "sentry": "sentry",
    "jwt": "jsonwebtokens",
    "telegram bot": "telegram",
    "jinja2": "jinja",
    "pgvector": "postgresql",
    "gemini": "googlegemini",
    "lighthouse ci": "lighthouse",
}

# ---------------------------------------------------------------------------
# Emoji fallback — used when simplepycons has no matching icon.
# ---------------------------------------------------------------------------

_EMOJI_FALLBACK: Dict[str, str] = {
    "react": "⚛️",
    "postgresql": "🐘",
    "postgres": "🐘",
    "redis": "🔴",
    "docker": "🐳",
    "fastapi": "⚡",
    "aws": "☁️",
    "kubernetes": "⚙️",
    "k8s": "⚙️",
    "mongodb": "🍃",
    "mongo": "🍃",
    "github": "🐙",
    "python": "🐍",
    "firebase": "🔥",
}

# Default emoji when nothing else matches
_DEFAULT_EMOJI = "🔧"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_slug(name: str) -> str:
    """Normalise a human-readable tech name to a simplepycons getter slug.

    Steps:
      1. Lowercase & strip whitespace.
      2. Look up in ``_ALIAS_MAP`` — if found, return immediately.
      3. Replace ``.`` with ``dot``.
      4. Strip all remaining non-alphanumeric characters.
    """
    key = name.lower().strip()

    # Direct alias hit
    if key in _ALIAS_MAP:
        return _ALIAS_MAP[key]

    # Programmatic normalisation
    slug = key.replace(".", "dot")
    slug = re.sub(r"[^a-z0-9]", "", slug)
    return slug


def _extract_path(raw_svg: str) -> str:
    """Extract the first SVG ``<path d="..."/>`` attribute from *raw_svg*."""
    match = re.search(r'd="([^"]+)"', raw_svg)
    return match.group(1) if match else ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_icon_svg(tech_name: str, size: int = 20, mono: bool = False) -> str:
    """Return an inline SVG string for *tech_name*.

    Parameters
    ----------
    tech_name:
        Human-readable technology name (e.g. ``"React"``, ``"Next.js"``).
    size:
        Icon width/height in pixels.
    mono:
        Draw brand marks in ``currentColor`` instead of the brand color.

    Returns
    -------
    str
        An ``<svg …>`` string on success, or a ``<span>`` with an emoji
        fallback when the icon cannot be resolved.
    """
    try:
        from simplepycons import all_icons  # noqa: WPS433

        for slug in _candidate_slugs(tech_name):
            getter = getattr(all_icons, f"get_{slug}_icon", None)
            if getter is None:
                continue
            icon = getter()
            path_d = _extract_path(icon.raw_svg)
            color = "currentColor" if mono else icon.primary_color  # already includes '#'
            if path_d:
                return (
                    f'<svg width="{size}" height="{size}" '
                    f'viewBox="0 0 24 24" fill="{color}">'
                    f'<path d="{path_d}"/></svg>'
                )
    except ImportError:
        # simplepycons not installed — specific emoji beat a monogram here
        key = tech_name.lower().strip()
        emoji = _EMOJI_FALLBACK.get(key, _DEFAULT_EMOJI)
        return f'<span style="font-size:{size}px;line-height:1;">{emoji}</span>'

    return _monogram_svg(tech_name, size)


def _candidate_slugs(tech_name: str) -> list:
    """Slugs to try in order: full name, first word ("Docker Compose" → docker),
    and the name without a trailing version ("Jinja2" → jinja)."""
    words = tech_name.split()
    candidates = [_normalize_slug(tech_name)]
    if len(words) > 1:
        candidates.append(_normalize_slug(words[0]))
    candidates.append(re.sub(r"\d+$", "", candidates[0]))
    return [c for i, c in enumerate(candidates) if c and c not in candidates[:i]]


# Deterministic accent per name so the same tech keeps its colour across renders
def _monogram_svg(tech_name: str, size: int) -> str:
    """Outlined square with 1-2 initials — used when no brand mark exists.

    An emoji wrench reads as a missing asset; a monogram reads as intentional. It is drawn in
    ``currentColor`` so it takes the surrounding text color instead of adding one to the palette.
    """
    words = re.findall(r"[A-Za-z0-9]+", tech_name) or ["?"]
    letters = (words[0][0] + (words[1][0] if len(words) > 1 else words[0][1:2])).upper()
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
        '<rect x="1" y="1" width="22" height="22" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        '<text x="12" y="16" text-anchor="middle" font-family="inherit" '
        f'font-size="{10 if len(letters) > 1 else 12}" font-weight="700" fill="currentColor">{letters}</text></svg>'
    )
