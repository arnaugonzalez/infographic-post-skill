"""Image prompt builder — converts structured data into designer-quality image prompts.

Instead of describing CSS properties, these prompts describe the infographic like
a brief to a professional graphic designer / illustrator. The resulting prompts
are sent to AI image models (Gemini image, DALL-E, Flux) to produce publication-
quality LinkedIn infographics.

Supports 5 infographic types:
  - architecture: System components and data flow
  - comparison: Side-by-side before/after or v1/v2
  - feature: How a specific capability works
  - process: Sequential pipeline / workflow
  - cheatsheet: Reference card with key information
"""
from __future__ import annotations


# ── Infographic types ─────────────────────────────────────────────────────────

INFOGRAPHIC_TYPES = {
    "architecture": "Architecture diagram showing system components and data flow",
    "comparison": "Side-by-side comparison (before/after, v1/v2, old/new)",
    "feature": "Feature explanation showing how a specific capability works",
    "process": "Process flow / pipeline showing sequential steps",
    "cheatsheet": "Cheat sheet / reference card with key information",
}

# ── Brand icon visual descriptions (for image model prompts) ──────────────────

_ICON_DESCRIPTIONS: dict[str, str] = {
    "react": "the blue atomic orbital symbol (three ellipses with a central dot)",
    "react native": "the blue atomic orbital symbol (three ellipses with a central dot)",
    "docker": "the blue whale carrying containers on its back",
    "kubernetes": "the blue ship's wheel/helm with 7 spokes",
    "postgresql": "the blue elephant head logo",
    "fastapi": "the teal diamond with a lightning bolt inside",
    "supabase": "the green lightning bolt logo on dark background",
    "redis": "the red stacked diamond/cube logo",
    "python": "the blue and yellow intertwined snakes logo",
    "typescript": "the blue square with white 'TS' letters",
    "javascript": "the yellow square with black 'JS' letters",
    "node.js": "the green hexagonal Node.js logo",
    "next.js": "the black 'N' lettermark in a white circle",
    "vue": "the green layered V-diamond logo",
    "vue.js": "the green layered V-diamond logo",
    "angular": "the red shield with angular 'A' cutout",
    "svelte": "the orange curved bracket/flame mark",
    "aws": "the orange smile/swoosh below 'aws' text",
    "google cloud": "the multicolored four-segment cloud logo",
    "azure": "the blue angular wave logo",
    "openai": "the black spiral/bloom mark",
    "github": "the black octocat silhouette (cat-octopus hybrid)",
    "github actions": "the blue circular workflow arrows logo",
    "vercel": "the black solid triangle/delta logo",
    "firebase": "the orange/yellow campfire flame logo",
    "mongodb": "the green leaf/sprout logo",
    "mysql": "the blue dolphin logo",
    "sqlite": "the blue feather logo",
    "langchain": "the teal chain-link icon with parrot",
    "langgraph": "the teal directed graph icon",
    "expo": "the dark blue/white Expo wordmark",
    "tailwind css": "the cyan stacked wave/fan of arcs",
    "flutter": "the blue diagonal layered F-shape",
    "django": "the dark green Django text logo",
    "flask": "a minimal dark flask/bottle silhouette",
    "spring": "the green coiled leaf spiral",
    "nestjs": "the red cat silhouette in a circle",
    "express": "the minimal 'Express' wordmark",
    "go": "the light blue Go gopher mascot",
    "rust": "the black gear/cog with R logo",
    "kafka": "the black bold geometric K lettermark",
    "rabbitmq": "the orange rabbit silhouette",
    "celery": "the green celery stalk icon",
    "terraform": "the purple stacked crystal/diamond cluster",
    "grafana": "the orange flame-eye logo",
    "prometheus": "the orange flame/fire torch logo",
    "elasticsearch": "the yellow-green angular brackets logo",
    "nginx": "the green 'N' logo",
    "cloudflare": "the orange cloud with rays logo",
    "netlify": "the teal diamond/gem logo",
    "railway": "the white railway track logo on dark",
    "auth0": "the red/orange shield logo",
    "clerk": "the purple rounded 'C' mark",
    "hugging face": "the yellow smiling face/emoji logo",
    "pytorch": "the orange flame/torch logo",
    "tensorflow": "the orange 'TF' geometric logo",
    "anthropic": "the warm beige/brown stylized 'A' lettermark",
    "drizzle orm": "the yellow-green droplets logo",
    "drizzle": "the yellow-green droplets logo",
    "playwright": "the green theatrical masks logo",
    "matplotlib": "the blue sine wave in a square",
    "pandas": "the dark blue/white pandas logo",
    "numpy": "the blue 3D cube/matrix logo",
    "sentry": "the purple angular shield logo",
    "pgvector": "a database cylinder with vector arrows",
    "faster-whisper": "a speech waveform icon",
    "distilroberta": "a neural network brain icon",
    "react query": "the red circular arrows/cycle logo",
    "react navigation": "a blue navigation compass icon",
}


def _describe_brand_icon(tech_name: str) -> str:
    """Return a visual description of a technology's brand icon for image prompts."""
    key = tech_name.lower().strip()
    if key in _ICON_DESCRIPTIONS:
        return _ICON_DESCRIPTIONS[key]
    # Try without common suffixes
    for suffix in (".js", ".ts", " orm", " css"):
        stripped = key.replace(suffix, "").strip()
        if stripped in _ICON_DESCRIPTIONS:
            return _ICON_DESCRIPTIONS[stripped]
    return f"a professional tech icon representing {tech_name}"


# ── Style presets ─────────────────────────────────────────────────────────────

_STYLE_PRESETS: dict[str, dict[str, str]] = {
    "modern-dark": {
        "background": "deep navy-to-indigo gradient (#0A0F1E → #1a1a3e) with subtle floating geometric shapes and soft glowing accent-colored orbs adding depth",
        "cards": "frosted glass panels with subtle white borders, colored top accents, and soft colored glow shadows beneath",
        "typography": "bold modern sans-serif (Inter/SF Pro style), white text on dark, ultra-high contrast, perfectly readable",
        "feel": "premium, Stripe/Vercel/Linear design system quality — like a $10,000 agency design",
        "constraints": "NOT a sketch, NOT hand-drawn, NOT a wireframe — pixel-perfect digital design with crisp edges",
    },
    "modern-light": {
        "background": "clean white-to-light-gray gradient with a subtle dot-grid pattern and soft colored accent blobs at edges",
        "cards": "white cards with soft multi-layered shadows and colored left/top borders",
        "typography": "bold dark text (#1a1a2e), clean sans-serif, professional spacing",
        "feel": "clean Apple-style minimal — like a WWDC keynote slide",
        "constraints": "NOT a sketch, NOT hand-drawn — clean digital design with precise alignment",
    },
    "illustrated": {
        "background": "rich illustrated gradient with subtle cloud/sky imagery, atmospheric depth layers, and volumetric lighting effects",
        "cards": "styled panels with 3D-looking elements, prominent brand logos with shadow/depth effects",
        "typography": "bold chunky headings with subtle glow, clean body text",
        "feel": "Canva premium template quality — magazine-style illustration meets tech diagram",
        "constraints": "High visual richness — illustrated but still professional and sharp, not cartoon-like",
    },
}


# ── Critical style constraints (appended to all prompts) ─────────────────────

_STYLE_CONSTRAINTS = """
CRITICAL STYLE CONSTRAINTS — FOLLOW STRICTLY:
• This is NOT a sketch, NOT hand-drawn, NOT a wireframe, NOT a whiteboard drawing
• Render as a PIXEL-PERFECT digital design — crisp edges, no pencil textures
• Use FLAT or subtle gradient fills — never hatching, crosshatch, or pencil shading
• All text must be sharp, anti-aliased, horizontal, and perfectly legible at 1080px
• Colors must be SATURATED and VIBRANT — not muted, pastel, or washed-out
• Backgrounds must be smooth gradients — no paper texture, no visible grain
• Brand logos must be RECOGNIZABLE — draw them accurately or use the described shapes
• Think: Figma mockup, Dribbble top shot, Apple keynote slide, Vercel marketing page
• MAXIMUM visual impact with MINIMUM clutter — every element earns its space
"""


# ── Prompt builders per type ──────────────────────────────────────────────────

def _format_tech_with_icon(name: str, description: str = "") -> str:
    """Format a technology entry with its brand icon description."""
    icon_desc = _describe_brand_icon(name)
    desc_part = f' — "{description}"' if description else ""
    return f"• {name} (show {icon_desc}){desc_part}"


def _build_architecture_prompt(data: dict, style: dict) -> str:
    title = data.get("title", "System Architecture")
    subtitle = data.get("subtitle", "")
    layers = data.get("layers", [])
    connections = data.get("connections", [])
    footer_cta = data.get("footer_cta", "Follow for more software architecture content")
    footer_summary = data.get("footer_summary", "")

    # Build component descriptions with icon details
    components_text = ""
    layer_names = []
    for i, layer in enumerate(layers):
        label = layer.get("label", f"Layer {i+1}")
        layer_names.append(label)
        color = layer.get("color", "")
        items = layer.get("items", [])
        items_text = "\n".join(
            _format_tech_with_icon(item.get("name", ""), item.get("description", ""))
            for item in items[:5]  # Max 5 per layer for visual clarity
        )
        components_text += f"\n{label}:{' (accent: ' + color + ')' if color else ''}\n{items_text}\n"

    # Build connections text
    connections_text = ""
    if connections:
        conn_lines = []
        for conn in connections:
            from_idx = conn.get("from_layer", 0)
            to_idx = conn.get("to_layer", 1)
            label = conn.get("label", "")
            from_name = layer_names[from_idx] if from_idx < len(layer_names) else f"Layer {from_idx}"
            to_name = layer_names[to_idx] if to_idx < len(layer_names) else f"Layer {to_idx}"
            conn_lines.append(f"• {from_name} → {to_name}" + (f' (label: "{label}")' if label else ""))
        connections_text = "\n".join(conn_lines)
    else:
        connections_text = "• Show natural data flow from user-facing layers down to data/infrastructure layers"

    return f"""Create a professional LinkedIn architecture infographic image at exactly 1080×1080 pixels.

PROJECT: "{title}"{f' — {subtitle}' if subtitle else ''}

VISUAL CONCEPT:
A modern tech architecture poster showing how the system components connect and data flows between them. {style['background']}. The composition tells a story of how data moves from users through the system.

TITLE AREA (top 12-15%):
"{title}" in large bold white text (36-40pt equivalent) with a subtle gradient glow effect.{f' Below it: "{subtitle}" in smaller muted text.' if subtitle else ''}

MAIN ARCHITECTURE DIAGRAM (center 65-70%):
Show these components as visually prominent elements with LARGE recognizable brand logos (48-64px equivalent). Arrange them in a logical flow — user-facing components at top, backend in middle, data/infrastructure at bottom.
{components_text}

DATA FLOW CONNECTIONS:
Draw curved glowing arrows or flowing connection lines between these components:
{connections_text}

The arrows should feel like data flowing through the system — not just static lines. Use dashed or gradient strokes with subtle animation-like appearance.

FOOTER (bottom 12-15%):
"{footer_cta}" in clean muted text.{f' One-line summary: "{footer_summary}"' if footer_summary else ''}

DESIGN STYLE:
• {style['feel']}
• Background: {style['background']}
• Component panels: {style['cards']}
• Typography: {style['typography']}
• Brand logos should be LARGE and RECOGNIZABLE — they're the visual anchors
• Each technology section should use a distinct accent color
• {style['constraints']}
{_STYLE_CONSTRAINTS}"""


def _build_comparison_prompt(data: dict, style: dict) -> str:
    title = data.get("title", "Comparison")
    layers = data.get("layers", [])
    footer_cta = data.get("footer_cta", "Follow for more insights")
    footer_summary = data.get("footer_summary", "")

    # For comparison, we expect 2 layers: "before" and "after" (or v1/v2)
    left = layers[0] if len(layers) > 0 else {"label": "BEFORE", "items": []}
    right = layers[1] if len(layers) > 1 else {"label": "AFTER", "items": []}

    left_items = "\n".join(
        f"  🟥 {item.get('name', '')}" + (f" — {item.get('description', '')}" if item.get('description') else "")
        for item in left.get("items", [])
    )
    right_items = "\n".join(
        f"  🟩 {item.get('name', '')}" + (f" — {item.get('description', '')}" if item.get('description') else "")
        for item in right.get("items", [])
    )

    return f"""Create a professional LinkedIn comparison infographic image at exactly 1080×1080 pixels.

TITLE: "{title}"

VISUAL CONCEPT:
A bold split-screen design comparing two states. Left side tinted with warm amber/red tones (old/before). Right side tinted with cool green/blue tones (new/after). A dramatic arrow or divider element in the center bridges the transformation.

LEFT COLUMN — "{left['label']}":
{left_items}
Show each item with a red/amber status indicator (🟥)

CENTER:
A bold directional arrow (→) or transformation symbol bridging left to right

RIGHT COLUMN — "{right['label']}":
{right_items}
Show each item with a green status indicator (🟩)

BOTTOM:
A bold tagline summarizing the transformation.
"{footer_cta}"

DESIGN STYLE:
• {style['feel']}
• Background: {style['background']}
• Left column has a subtle warm amber/red overlay
• Right column has a subtle cool green/blue overlay
• Status indicators should be COLOR-CODED (red = old, green = new)
• Typography: {style['typography']}
• {style['constraints']}
{_STYLE_CONSTRAINTS}"""


def _build_feature_prompt(data: dict, style: dict) -> str:
    title = data.get("title", "Feature Overview")
    subtitle = data.get("subtitle", "")
    layers = data.get("layers", [])
    connections = data.get("connections", [])
    footer_cta = data.get("footer_cta", "Follow for more")
    footer_summary = data.get("footer_summary", "")

    # For features, layers represent steps/stages of the feature
    steps_text = ""
    for i, layer in enumerate(layers):
        label = layer.get("label", f"Step {i+1}")
        items = layer.get("items", [])
        items_desc = "; ".join(
            f"{item.get('name', '')} ({item.get('description', '')})"
            for item in items[:4]
        )
        steps_text += f"\nSTEP {i+1} — {label}:\n  Components: {items_desc}\n"

    return f"""Create a professional LinkedIn feature explanation infographic at exactly 1080×1080 pixels.

TITLE: "{title}"{f' — {subtitle}' if subtitle else ''}

VISUAL CONCEPT:
A numbered step-by-step visual showing how this feature works internally. Each step is a distinct visual panel connected by flowing arrows. The progression should feel like "zooming in" to how the system processes a request.

FLOW:
{steps_text}

Show each step as a numbered panel (①②③④...) with:
- A clear step label/title
- The key components involved (with brand icons where applicable)
- A brief description of what happens at this stage
- Arrows flowing to the next step

FOOTER:
"{footer_cta}"{f' Summary: "{footer_summary}"' if footer_summary else ''}

DESIGN STYLE:
• {style['feel']}
• Background: {style['background']}
• Numbered panels: {style['cards']}
• Flow arrows should be prominent and clearly show the direction
• Typography: {style['typography']}
• {style['constraints']}
{_STYLE_CONSTRAINTS}"""


def _build_process_prompt(data: dict, style: dict) -> str:
    title = data.get("title", "Process Flow")
    layers = data.get("layers", [])
    footer_cta = data.get("footer_cta", "Follow for more")

    stages = ""
    for i, layer in enumerate(layers):
        label = layer.get("label", f"Stage {i+1}")
        items = layer.get("items", [])
        techs = ", ".join(item.get("name", "") for item in items[:3])
        stages += f"\nSTAGE {i+1}: {label}\n  Technologies: {techs}\n"

    return f"""Create a professional LinkedIn process flow infographic at exactly 1080×1080 pixels.

TITLE: "{title}"

VISUAL CONCEPT:
A clear horizontal or vertical pipeline showing sequential stages. Each stage is a distinct node/station connected by bold directional arrows. The flow should be immediately obvious — reading left-to-right or top-to-bottom.

PIPELINE:
{stages}

Each stage should be visualized as:
- A prominent node with the stage name
- Brand icons for the key technologies used
- A flowing arrow connecting to the next stage

FOOTER:
"{footer_cta}"

DESIGN STYLE:
• {style['feel']}
• Background: {style['background']}
• Stage nodes: {style['cards']}
• Pipeline arrows should be BOLD and clearly directional
• Typography: {style['typography']}
• {style['constraints']}
{_STYLE_CONSTRAINTS}"""


def _build_cheatsheet_prompt(data: dict, style: dict) -> str:
    title = data.get("title", "Cheat Sheet")
    layers = data.get("layers", [])
    footer_cta = data.get("footer_cta", "Save this for later!")

    sections = ""
    for layer in layers:
        label = layer.get("label", "Section")
        items = layer.get("items", [])
        items_text = "\n".join(
            f"  • {item.get('name', '')}: {item.get('description', '')}"
            for item in items[:5]
        )
        sections += f"\n{label}:\n{items_text}\n"

    return f"""Create a professional LinkedIn cheat sheet infographic at exactly 1080×1080 pixels.

TITLE: "{title}"

VISUAL CONCEPT:
A structured reference card that someone would SAVE and come back to. Clean sections with colored headers, key points in organized bullets, and highlight/tip callouts. Dense but scannable.

SECTIONS:
{sections}

Each section should have:
- A bold colored header with a small icon
- Key items as clean bullet points
- A "Pro Tip" or highlight callout for the most important item

FOOTER:
"💾 {footer_cta}" — encourage saving/bookmarking

DESIGN STYLE:
• {style['feel']}
• Background: {style['background']}
• Section cards: {style['cards']}
• Dense but highly organized — this is a REFERENCE card, not a sparse poster
• Typography: {style['typography']}
• {style['constraints']}
{_STYLE_CONSTRAINTS}"""


# ── Public API ────────────────────────────────────────────────────────────────

_BUILDERS = {
    "architecture": _build_architecture_prompt,
    "comparison": _build_comparison_prompt,
    "feature": _build_feature_prompt,
    "process": _build_process_prompt,
    "cheatsheet": _build_cheatsheet_prompt,
}


def build_image_prompt(
    data: dict,
    infographic_type: str = "architecture",
    style: str = "modern-dark",
) -> str:
    """Build a detailed image generation prompt from structured infographic data.

    Parameters
    ----------
    data : dict with keys from content_structurer (title, subtitle, layers, connections, etc.)
    infographic_type : one of INFOGRAPHIC_TYPES keys
    style : visual style preset ("modern-dark", "modern-light", "illustrated")

    Returns a detailed text prompt for image generation models.
    """
    if infographic_type not in _BUILDERS:
        raise ValueError(
            f"Unknown infographic type '{infographic_type}'. "
            f"Valid types: {', '.join(_BUILDERS.keys())}"
        )
    style_preset = _STYLE_PRESETS.get(style, _STYLE_PRESETS["modern-dark"])
    builder = _BUILDERS[infographic_type]
    return builder(data, style_preset)
