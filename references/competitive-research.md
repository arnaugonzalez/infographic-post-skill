# Infographic Quality Research — Competitive Landscape & Design Gap Analysis

*Research date: 2026-03-26*
*Purpose: Understand what "publication-quality" infographics look like and define the visual bar for v2*

## The Problem

Our current HTML-path output is a **styled data grid** — layer labels, tech chips with descriptions, arranged in columns. While informationally correct, it looks like a developer dashboard, not a LinkedIn-worthy infographic. Users expect:

- Visual hierarchy with focal points
- Branded icons (not just text labels)
- Data flow arrows / connections between layers
- Glassmorphism, gradients, or other modern design patterns
- Composition that tells a story, not just lists facts

## Competitive Tools & Their Visual Quality Bar

### Tier A — "LinkedIn-native" visual tools (what we're competing with)

| Tool | Approach | Visual Quality | Key Design Patterns |
|------|----------|---------------|---------------------|
| **Napkin AI** | Text → structured diagrams | ★★★★☆ | Clean nodes with icons, smart connectors, curated color palettes, light/dark mode, elastic layouts that adapt. 5M+ users. |
| **Venngage** | Templates + AI text-to-infographic | ★★★★★ | Pre-designed templates with visual hierarchy, data viz (charts, maps), brand kits, LinkedIn-specific formats. |
| **Canva** | Templates + drag-and-drop | ★★★★★ | Massive template library, brand kit, export as PDF carousel for LinkedIn. Gold standard for non-designers. |
| **Adobe Express** | Templates + Firefly AI | ★★★★★ | 150+ LinkedIn carousel templates, generative AI, Adobe Fonts/Stock integration. |

### Tier B — Architecture diagram tools (closer to our domain)

| Tool | Approach | Visual Quality | Key Design Patterns |
|------|----------|---------------|---------------------|
| **Eraser.io** | Text/code → diagram-as-code | ★★★★☆ | Clean cloud architecture diagrams with proper icons (AWS, GCP, etc.), diagram-as-code syntax, minimal aesthetic. |
| **Swark** | Codebase → Mermaid diagrams | ★★☆☆☆ | Mermaid.js output — functional but ugly. Box-and-arrow diagrams, no visual polish. |
| **Miro AI** | Canvas + AI generation | ★★★★☆ | Real-time collaboration, auto-generated docs, infrastructure visualization. |
| **Lucidchart** | AI + data-driven diagramming | ★★★★☆ | Polished diagrams, 100+ integrations, auto-generation from prompts. |

### Where Our Infographic Skill Falls

| Dimension | Napkin/Canva/Venngage | Our Current Output |
|-----------|----------------------|-------------------|
| **Visual hierarchy** | Title → hero section → grouped content → CTA | Flat grid, equal weight everywhere |
| **Icons** | Brand SVG icons (React, Docker, etc.) with official colors | Text-only chips (no icons) |
| **Connections** | Arrows, flow lines, dependency graphs | None — layers are isolated boxes |
| **Color coding** | Layer-specific accent colors, gradients, glows | Uniform border colors per column |
| **Composition** | Story flow (top=frontend, middle=backend, bottom=infra) | Just columns |
| **White space** | Intentional breathing room, focal points | Wasted space from sparse content |
| **Brand feel** | Consistent, template-driven, "designed" | Looks AI-generated (because it is) |

## Key Design Patterns to Adopt

### 1. Napkin-style node diagrams
- Each tech is a **node** (rounded rectangle) with:
  - Brand icon (SVG, 24px)
  - Name (bold)
  - One-line description (muted)
- Nodes are **grouped** by layer with a labeled container
- **Connectors** (arrows/lines) show data flow between layers
- **Color-coded borders** per layer (blue=frontend, green=backend, purple=data, orange=infra)

### 2. Eraser-style architecture diagrams
- Diagram-as-code with proper cloud/service icons
- Layered top-to-bottom flow (Client → API → Services → Data)
- Clean lines, minimal decoration
- Professional, not flashy

### 3. Venngage/Canva-style infographics
- Strong **title treatment** (gradient text, decorative elements)
- **Section dividers** between content areas
- **Data callouts** (key metric with large number)
- **CTA footer** with social branding
- **Template-based** — consistent across runs

## Recommended v2 Approach

### Option A: HTML template system (recommended)
Instead of asking the LLM to generate HTML from scratch (unreliable), provide a **curated HTML/CSS template** and ask the LLM to only fill in the data slots. This is how Napkin, Canva, and Venngage work — the design is pre-built, the AI fills in content.

**Template structure:**
```
┌─────────────────────────────────────┐
│           TITLE (gradient)           │
│         subtitle (muted)             │
├─────────────────────────────────────┤
│                                     │
│  ┌─────┐    ┌─────┐    ┌─────┐    │
│  │ 🔵  │───→│ 🟢  │───→│ 🟣  │    │  ← Layer 1 (Frontend)
│  │React │    │FastAPI│   │Postgres│  │
│  └─────┘    └─────┘    └─────┘    │
│       │           │          │      │
│       ▼           ▼          ▼      │
│  ┌─────┐    ┌─────┐    ┌─────┐    │
│  │ 🔴  │    │ 🟡  │    │ 🟤  │    │  ← Layer 2 (Services)
│  │Redis │    │Celery│    │S3   │    │
│  └─────┘    └─────┘    └─────┘    │
│                                     │
├─────────────────────────────────────┤
│  CTA: "Follow for more..."          │
│  Author · © 2026                     │
└─────────────────────────────────────┘
```

**Benefits:**
- Design quality is deterministic (from template, not LLM)
- LLM only decides what content goes where (its strength)
- Template can be iterated by a designer without touching code
- Works with ANY model tier (even tier 3)

### Option B: Use Napkin AI as a rendering backend
- Napkin has an API / supports text import
- Could pipe our codebase report → Napkin text format → Napkin renders
- Downside: external dependency, paid plans for heavy use

### Option C: SVG generation via D3.js or similar
- Generate architecture diagrams as SVG using a JS library
- More programmatic control than HTML/CSS
- Better for complex connection routing
- Downside: heavier dependency chain

## Conclusion

The **gap between our output and the market standard is primarily a design template problem**, not an LLM problem. Asking an LLM to both design AND populate an infographic produces mediocre results (our current approach). The industry standard is: **pre-designed template + AI-driven content population**.

v2 should ship 3-5 curated HTML/CSS templates with fixed visual design and let the LLM only decide what data goes in each slot.

## References

- Napkin AI: https://www.napkin.ai/
- Eraser.io: https://www.eraser.io/
- Swark (code→diagram): https://github.com/swark-io/swark
- Venngage AI: https://venngage.com/ai-tools/infographic-generator
- Postiv AI LinkedIn tools roundup: https://postiv.ai/blog/linkedin-infographic-maker
