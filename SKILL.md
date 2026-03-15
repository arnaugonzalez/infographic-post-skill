---
name: infographic
description: >
  Create professional, visually stunning infographics from data, text, or concepts.
  Use this skill whenever the user mentions infographics, data visualization, visual
  summaries, charts, statistical graphics, process diagrams, comparison visuals,
  timelines, or any request to "make data visual" or "turn this into a graphic."
  CRITICAL: Also invoke immediately when the user adds "for linkedin", "for linkedin post",
  "linkedin infographic", or "linkedin diagram" to ANY request — especially for architecture
  diagrams, system design visuals, or technical overviews from a CLAUDE.md or project context.
  This skill auto-reads the project's CLAUDE.md and directory structure to infer components.
allowed-tools:
  - Bash
  - Write
  - Read
dependencies:
  python: ">=3.8"
  pip:
    - matplotlib>=3.7
    - Pillow>=10.0
    - numpy>=1.24
---

# Infographic Skill

Transform data, text, concepts, and reports into professional, publication-ready
infographics. Output formats: `.png` (default, high-res), `.svg` (vector),
or `.html` (interactive). Always read `references/design-principles.md` and
`references/chart-selection.md` before starting.

---

## Step 1 — Understand & Plan

Before writing a single line of code:

1. **Extract the core message**: What is the single most important thing this
   infographic must communicate? Write it in one sentence.
2. **Identify the data type** — use `references/chart-selection.md` to pick
   the right visual form.
3. **Define the audience**: general public, executives, technical, etc.
4. **Decide the layout** from the options below.
5. **Choose a color palette** — see `references/design-principles.md`.

### Layout Templates

| Layout | Best for |
|---|---|
| `vertical-story` | Narrative flows, step-by-step, timelines |
| `dashboard` | Multiple KPIs, mixed chart types |
| `comparison` | Side-by-side options, pros/cons, before/after |
| `process-flow` | Workflows, pipelines, how-it-works |
| `data-spotlight` | Single striking stat with supporting context |
| `hierarchical` | Org charts, taxonomies, breakdowns |

---

## Step 2 — Generate the Infographic

Always use `scripts/generate.py` as the execution engine. It provides:
- High-DPI canvas setup (300 DPI for print, 150 for screen)
- Typography system (font stack with fallbacks)
- Color palette utilities
- Section layout helpers

### Invocation pattern

```bash
python scripts/generate.py \
  --layout vertical-story \
  --output infographic.png \
  --width 1080 \
  --height 1920 \
  --dpi 150
```

For interactive HTML output (use when data is complex or interactive exploration
is needed):

```bash
# Generate self-contained HTML with embedded Chart.js
python scripts/generate_html.py --output infographic.html
```

---

## Step 3 — Design Rules (NON-NEGOTIABLE)

Read `references/design-principles.md` for full details. The hard rules:

### Visual Hierarchy
- **One hero element**: largest, boldest, most prominent. Everything else supports it.
- Max 3 font sizes per infographic: hero, body, caption.
- Whitespace is not empty space — it is structure.

### Typography
- Headlines: bold weight, ≥24pt
- Body: regular weight, 11–14pt
- Captions/labels: 9–11pt
- Never use more than 2 typefaces.

### Color
- Max 4–5 colors total (primary, secondary, accent, neutral, background).
- Ensure WCAG AA contrast ratio (≥4.5:1 for text, ≥3:1 for UI).
- Use color to encode meaning, not decoration.
- Sequential data → sequential palette. Categorical → qualitative palette.

### Data Integrity
- Always start bar/column chart axes at zero.
- Label data directly on chart elements when possible (avoid legends when you can).
- Show sample size / source attribution in small text at the bottom.
- Never use 3D charts — they distort perception.
- Never use pie charts with more than 5 slices — use a bar chart instead.

### Layout
- Maintain consistent internal margins (≥40px padding from edges).
- Group related elements with proximity, not just lines/borders.
- Use a grid — align everything to it.

---

## Step 4 — Iteration & Polish

After the first render:

1. Check: Does the hero message read in 3 seconds?
2. Check: Is every element earning its space? Remove anything decorative-only.
3. Check: Can a colorblind person read this? (Use matplotlib's `cividis` or
   `viridis` for sequential; `tab10` avoids red-green issues.)
4. Refine spacing, label sizes, and color contrast.
5. Save final to the requested output path.

---

## Output

Always tell the user:
- Where the file was saved
- Dimensions and DPI
- How to open / embed it
- Any data assumptions made

---

## Examples

**"Make an infographic showing our Q3 KPIs: Revenue $2.4M (+18%), NPS 72,
Churn 2.1%, New customers 340"**
→ Use `dashboard` layout, 4-panel grid, each KPI gets a bold number + sparkline,
   brand-neutral color palette.

**"Visualize the steps of our onboarding process (7 steps)"**
→ Use `vertical-story` or `process-flow` layout with numbered circles + icons.

**"Create an infographic comparing React, Vue, and Angular"**
→ Use `comparison` layout with radar chart or side-by-side attribute table.

**"Turn this CSV of survey results into an infographic"**
→ Read the CSV, identify top 3–5 findings, use `data-spotlight` or `dashboard`.

---

## LinkedIn Architecture Diagrams

> Trigger: user appends **"for linkedin"** or **"for linkedin post"** to any request
> about architecture, system design, project overview, or tech stack.

### What this produces

A 1080×1080px PNG (LinkedIn square format) that looks like a professional
architecture diagram — colored group boxes, component chips, dashed arrows,
bold title bar, and a footer with a CTA. Style reference: Kubernetes architecture
diagram format (bold, colorful, publication-ready).

### Step-by-step workflow

**1. Gather context** — Read everything available:
   - `CLAUDE.md` in the project root (most important)
   - Top-level directory names
   - `README.md`, `docs/architecture.md` if present
   - Any architecture description given directly by the user

**2. Run the context parser:**
```bash
# From project root, reads CLAUDE.md + directory structure automatically:
python scripts/parse_context.py \
  --root /path/to/project \
  --title "My App Architecture" \
  --author "Your Name" \
  --cta "Follow for more software architecture content" \
  --output arch.json
```

Or from a specific file / inline text:
```bash
python scripts/parse_context.py \
  --file /path/to/CLAUDE.md \
  --title "My App Architecture" \
  --output arch.json
```

Or from free-form user description:
```bash
python scripts/parse_context.py \
  --text "FastAPI backend, Flutter mobile app, PostgreSQL database, Redis cache, AWS S3, GitHub Actions" \
  --title "SaaS Platform Architecture" \
  --output arch.json
```

**3. Review and optionally edit `arch.json`** — The parser auto-infers layers and
connections. If something is wrong, edit the JSON before rendering. The format is:
```json
{
  "title": "My App Architecture",
  "subtitle": "Technical Stack Overview",
  "author": "Author Name",
  "linkedin_cta": "Follow for more software architecture posts",
  "layers": [
    {
      "label": "Frontend",
      "category": "frontend",
      "items": ["React", "Next.js", "TailwindCSS"],
      "bg": "#DBEAFE",
      "border": "#1D4ED8",
      "label_color": "#FFF"
    }
  ],
  "connections": [
    { "from": "frontend", "to": "backend", "label": "" }
  ]
}
```

**4. Render the diagram:**
```bash
python scripts/generate_linkedin_arch.py \
  --config arch.json \
  --output linkedin_arch.png
```

Or quick one-liner without a JSON file:
```bash
python scripts/generate_linkedin_arch.py \
  --layers "Frontend:React,Next.js|Backend:FastAPI,Celery|Database:PostgreSQL,Redis|Cloud:AWS S3,CloudFront" \
  --title "My SaaS Architecture" \
  --author "Your Name" \
  --output linkedin_arch.png
```

### Design rules for LinkedIn architecture diagrams

- **Title**: Dark navy bar, white bold text, LinkedIn-blue accent line
- **Groups**: Each technology group gets a color-coded rounded box with a solid
  title bar. Individual components are white chips with colored borders inside.
- **Arrows**: Dashed arrows show data/request flow between layers.
- **Format**: Always 1080×1080px @ 150dpi (LinkedIn square).
- **Footer**: Dark bar with CTA text and optional author name.
- **Max groups**: 9 (3×3 grid). If more components exist, merge related ones.
- **Max items per group**: 6. If more, show the 5 most important + "...".

### Layer color + icon reference

Each group title bar automatically renders a small white patch-based icon drawn
with matplotlib primitives — no external image files or emoji required.

| Layer | Background | Border | Icon |
|---|---|---|---|
| Frontend | Light blue | Blue | Browser window |
| Mobile | Lavender | Purple | Phone outline |
| Backend / API | Amber | Orange | Gear |
| Database | Mint | Green | Cylinder |
| Auth | Yellow | Gold | Padlock |
| Queue / Events | Purple | Deep purple | Three bar lines |
| Storage | Indigo light | Indigo | Stacked disks |
| Cloud Services | Cyan | Teal | Three-circle cloud |
| Infrastructure | Rose | Red | Server rack |
| AI / ML | Emerald | Green | Neural network nodes |
| Monitoring | Warm gray | Brown | Line chart spike |
| CI/CD | Slate | Gray | Circular arrow |
| Other | Gray | Dark gray | Diamond |

### Examples

**"Generate a linkedin post for this project"**
→ Run `parse_context.py --root .` → render with author from git config

**"Make our architecture diagram for linkedin, here's our CLAUDE.md: [paste]"**
→ Run `parse_context.py --text [pasted content]` → render

**"For linkedin: FastAPI backend, Flutter app, PostgreSQL, Redis, AWS"**
→ Run `parse_context.py --text "FastAPI backend, Flutter app, PostgreSQL, Redis, AWS"` → render
