"""Template-based infographic renderer using Jinja2."""
from __future__ import annotations

import sys
from pathlib import Path

# Import icon_registry
sys.path.insert(0, str(Path(__file__).resolve().parent))
from icon_registry import get_icon_svg

try:
    import jinja2

    _JINJA2_OK = True
except ImportError:
    _JINJA2_OK = False

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "infographic"

# Default layer color palette
_LAYER_PALETTE = [
    "#3B82F6",
    "#F59E0B",
    "#10B981",
    "#8B5CF6",
    "#06B6D4",
    "#EF4444",
    "#EC4899",
    "#F97316",
]


def render_infographic(
    data: dict,
    template_name: str = "arch-dark-glassmorphism",
    output: str | Path = "infographic.html",
    icon_size: int = 20,
) -> Path:
    """Render a structured infographic data dict into HTML using a Jinja2 template.

    Parameters
    ----------
    data : dict
        Must contain keys: ``title``, ``subtitle``, ``layers`` (list),
        ``connections`` (list), ``footer_cta``, ``footer_summary``.
        Each layer has ``label`` and ``items`` (list of dicts with
        ``name``, ``description``, and optionally ``icon_svg``).
    template_name : str
        Template filename without the ``.html`` extension.
    output : str | Path
        Destination HTML file path.
    icon_size : int
        Size for brand SVG icons in pixels.

    Returns
    -------
    Path
        The path to the written HTML file.

    Raises
    ------
    SystemExit
        If jinja2 is not installed.
    jinja2.TemplateNotFound
        If *template_name* does not resolve to an existing template file.
    """
    if not _JINJA2_OK:
        print("❌ jinja2 is not installed. Install with: pip install jinja2")
        sys.exit(1)

    # Assign colors to layers if not already set
    for i, layer in enumerate(data.get("layers", [])):
        if "color" not in layer:
            layer["color"] = _LAYER_PALETTE[i % len(_LAYER_PALETTE)]

    # Enrich items with SVG icons
    for layer in data.get("layers", []):
        for item in layer.get("items", []):
            if "icon_svg" not in item:
                item["icon_svg"] = get_icon_svg(item.get("name", ""), icon_size)

    # Render template
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,  # We control the HTML — no user input
    )
    tmpl = env.get_template(f"{template_name}.html")
    html = tmpl.render(**data)

    out_path = Path(output).with_suffix(".html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
