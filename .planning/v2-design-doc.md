# V2 Infographic Quality Overhaul — Design Document

*Created: 2026-03-26*
*Status: DRAFT*

## Problem Statement

The current HTML-path infographic output is a plain card grid because the LLM
is asked to both **design** and **populate** the infographic in one shot. This
produces inconsistent, model-dependent results that look like developer
dashboards, not LinkedIn-worthy visuals.

## Solution: Template-Driven Architecture

Decouple **design** (deterministic, pre-built templates) from **content intelligence**
(LLM decides what goes where and writes taglines).

```
CURRENT (v1):
  codebase → LLM → raw HTML (design + data) → screenshot → PNG
  Problem: LLM is bad at CSS design. Output quality = f(model tier).

V2:
  codebase → LLM → structured JSON (data only) → template engine → HTML → PNG
  Benefit: Design quality is constant. LLM only does what it's good at.
```

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ read_codebase │────→│ LLM call     │────→│ Jinja2       │────→ HTML → Playwright → PNG
│ (existing)   │     │ "Fill slots"  │     │ template     │
└──────────────┘     │              │     │ engine       │
                     │ Returns JSON: │     │              │
                     │ {             │     │ Injects:     │
                     │   title,      │     │ - data       │
                     │   subtitle,   │     │ - SVG icons  │
                     │   layers: [   │     │ - colors     │
                     │     { label,  │     │ - connections │
                     │       items: [│     └──────────────┘
                     │         {name,│
                     │          desc,│
                     │          icon}│
                     │       ]      │
                     │     }        │
                     │   ],         │
                     │   connections │
                     │ }            │
                     └──────────────┘
```

## Components

### 1. Icon Registry (`scripts/icon_registry.py`)

Programmatic access to 3,414 Simple Icons brand SVGs.

```python
from simplepycons import all_icons

def get_icon_svg(tech_name: str, size: int = 20) -> str:
    """Return an inline SVG string for a technology, or emoji fallback."""
    # Normalize: "React Native" → "react", "Next.js" → "nextdotjs"
    slug = _normalize_slug(tech_name)
    getter = getattr(all_icons, f"get_{slug}_icon", None)
    if getter:
        icon = getter()
        path = _extract_path(icon.raw_svg)
        color = icon.primary_color
        return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{color}"><path d="{path}"/></svg>'
    return _emoji_fallback(tech_name)
```

Key features:
- Fuzzy name matching ("React Native" → react, "Node.js" → nodedotjs)
- Pre-built alias map for common names
- Emoji fallback for unrecognized techs
- Zero LLM involvement — deterministic icon resolution

### 2. HTML Templates (`templates/infographic/`)

Pre-designed, self-contained HTML/CSS templates. The LLM never touches the design.

#### Template: `arch-dark-glassmorphism.html` (default)
- **Canvas**: 1080×1080px, dark gradient background (#0a0f1e → #1a1a2e)
- **Blobs**: 2-3 blurred radial gradients for depth (static, not animated)
- **Header**: Title in gradient text (32px 800 weight), subtitle muted
- **Layer groups**: Glassmorphism cards with colored top borders
  - Each card: backdrop-filter:blur(12px), rgba bg, rounded corners
  - Layer label: uppercase, layer accent color
- **Tech chips**: Inside each card
  - Brand SVG icon (20px) + name (bold) + tagline (muted italic)
  - Colored left-border accent matching the layer
- **Connection arrows**: Inline SVG overlay
  - Dashed lines from layer-to-layer (top→bottom data flow)
  - Arrow markers at endpoints
- **Footer**: CTA text + author + project description summary

#### Template: `arch-light-clean.html`
- White/light background, colored section dividers
- Larger cards with more whitespace
- Suitable for printing / light-mode contexts

#### Template: `dashboard-kpi.html`
- Hero numbers (48-64px) with gradient coloring
- Radial progress rings (SVG)
- Trend indicators (↑↓)

### 3. Content Structurer (`scripts/content_structurer.py`)

Replaces the "LLM generates HTML" call with "LLM returns structured JSON."

**New prompt pattern:**
```
You are a senior software architect. Given a codebase analysis report, produce
a JSON structure for an architecture infographic.

RULES:
- Group technologies into 4-6 logical layers
- Each layer has: label, accent_color (from palette), items[]
- Each item has: name (exact tech name), description (≤8 words, specific)
- Add connections[] showing data flow between layers
- Title: derive from project name, not generic

PALETTE: {frontend: "#3B82F6", backend: "#F59E0B", database: "#10B981", ...}

OUTPUT: Valid JSON only. No explanation.

{codebase_report}
```

**Benefits of JSON output:**
- Parseable and validatable (unlike raw HTML)
- Can retry on parse failure
- Same JSON feeds any template
- Model-independent: even tier-3 models produce valid JSON

### 4. Template Renderer (`scripts/template_renderer.py`)

Uses Jinja2 to merge structured JSON + icon SVGs + template.

```python
def render_infographic(
    data: dict,           # From LLM (structured JSON)
    template: str = "arch-dark-glassmorphism",
    output: Path = "infographic.html",
) -> Path:
    env = jinja2.Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    tmpl = env.get_template(f"{template}.html")

    # Enrich data with real SVG icons
    for layer in data["layers"]:
        for item in layer["items"]:
            item["icon_svg"] = get_icon_svg(item["name"])

    # Render
    html = tmpl.render(**data)
    output.write_text(html)
    return output
```

### 5. Connection Arrow System

SVG overlay rendered at template time, not by the LLM.

```html
<!-- Connection arrows between layers -->
<svg class="connections" viewBox="0 0 1080 1080">
  {% for conn in connections %}
  <line x1="{{ conn.x1 }}" y1="{{ conn.y1 }}"
        x2="{{ conn.x2 }}" y2="{{ conn.y2 }}"
        stroke="{{ conn.color }}" stroke-width="1.5"
        stroke-dasharray="6,4" opacity="0.4"
        marker-end="url(#arrow)"/>
  {% endfor %}
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#666"/>
    </marker>
  </defs>
</svg>
```

## Migration Path

### Phase 1: Icon Registry + simplepycons
- Build `icon_registry.py` with fuzzy matching + alias map
- Add `simplepycons` to `requirements.txt`
- Test against 50+ common tech names

### Phase 2: Jinja2 Templates
- Build the `arch-dark-glassmorphism.html` template
- Implement `template_renderer.py`
- Add `jinja2` to `requirements.txt`

### Phase 3: Content Structurer
- New prompt that returns JSON instead of HTML
- JSON schema validation
- Retry on parse failure
- Wire into existing `generate_pretty.py` as a new rendering path

### Phase 4: Connection Arrows
- Position calculation from layer layout
- SVG overlay generation
- Template integration

### Phase 5: Backward Compatibility
- Keep existing HTML-generation path as `--legacy-html` flag
- Default to template-based rendering
- Image-model path (Gemini native PNG) unchanged

## Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `simplepycons` | 3,414 brand SVG icons | Yes |
| `jinja2` | HTML template engine | Yes |
| (existing) `playwright` | HTML → PNG screenshot | Optional |
| (existing) `matplotlib` | Offline fallback path | Already installed |

## Quality Metrics

| Dimension | v1 (current) | v2 (target) |
|-----------|-------------|-------------|
| Brand icons | None / hallucinated | Real SVGs from Simple Icons |
| Layout consistency | Model-dependent | Deterministic (template) |
| Connection arrows | None in HTML path | SVG overlay with markers |
| Visual hierarchy | Flat grid | Header → layers → footer |
| Color system | Sometimes applied | Always correct per layer |
| Works with tier-3 models | Poor | Good (JSON is easier than HTML) |
| Design polish | ★★☆☆☆ | ★★★★☆ |
