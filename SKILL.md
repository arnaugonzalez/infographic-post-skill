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
  VERSIONING: When the user adds any version-iteration phrase — "next version", "nueva version",
  "siguiente version", "new version", "next design", "nouvelle version", "nächste version",
  "próxima versión", "nuova versione", or any equivalent in any language — ALWAYS run
  scripts/version_output.py to manage versioned output before generating.
allowed-tools:
  - Bash
  - Write
  - Read
dependencies:
  python: ">=3.9"
  pip:
    - matplotlib>=3.7
    - Pillow>=10.0
    - numpy>=1.24
    - requests>=2.28
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

## LinkedIn Text Post Rules

When generating the accompanying LinkedIn text post for any infographic:

- **HARD LIMIT: 2,500 characters maximum** (LinkedIn truncates at ~3,000 but
  best engagement is under 2,500). Count characters, not words.
- Open with a hook line (question or bold statement) in the first 2 lines
  (these show before "...see more")
- Use line breaks liberally for readability on mobile
- End with a clear CTA (question to audience, or "Follow for more")
- Include 3-5 relevant hashtags at the end (do NOT count toward the 2,500 limit)
- If the user provided --learnings or a topic, the text post MUST focus on those
  specific technologies/insights, not generic content

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

---

## "Pretty" Mode — Gemini-Powered Generative Designs

> **Trigger**: user includes **"pretty"** or **"make pretty"** anywhere in their
> request — e.g. *"make this architecture diagram pretty for linkedin"* or
> *"pretty infographic of our Q3 KPIs"*.

This mode replaces the matplotlib renderer with a **Google Gemini Pro** call that
produces a visually stunning, self-contained HTML infographic (dark glassmorphism,
CSS animations, SVG arrows) at 1080×1080 px. If Playwright is installed the HTML
is automatically screenshotted to a PNG ready for LinkedIn.

### Setup (one-time)

Hay dos backends disponibles. **Vertex AI es el recomendado** si tienes crédito GCP.

#### Opción A — Vertex AI (recomendado con crédito GCP $300)

```bash
# Configura IAM, service account y descarga la clave en un solo paso:
bash scripts/setup_vertex_iam.sh mi-proyecto-gcp-id

# Verifica que la policy está activa:
python scripts/check_vertex_policy.py
```

Esto añade automáticamente al `.env`:
```
INFG_VERTEX_PROJECT=mi-proyecto-gcp-id
INFG_VERTEX_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/vertex_credentials.json
```

El script crea el service account `infographic-skill-sa` con el rol `roles/aiplatform.user`.

#### Opción B — AI Studio API key (fallback)

```
INFG_API_KEY=<your-google-ai-studio-key>
```

#### Dependencias comunes

```bash
pip install google-genai google-auth google-auth-httplib2
# Opcional — export PNG desde HTML:
pip install playwright && playwright install chromium
```

#### Aviso de policy revocada

`generate_pretty.py` verifica automáticamente las credenciales Vertex AI al arrancar.
Si la policy fue revocada (rol eliminado, clave borrada, etc.) muestra un aviso
**antes** de intentar generar la imagen:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  AVISO: las credenciales de Vertex AI no son válidas
   Error: ...
   Diagnóstico completo:
     python scripts/check_vertex_policy.py
   Re-configurar:
     bash scripts/setup_vertex_iam.sh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Para diagnóstico completo (4 checks: key file, credenciales, IAM, API):
```bash
python scripts/check_vertex_policy.py
```

### Optional setup: OpenRouter

Use OpenRouter to route text generation through any model (Claude, GPT-4o, Llama, etc.).

1. Get an API key at https://openrouter.ai/keys
2. Set in `.env`:

```text
INFG_LLM_PROVIDER=openrouter
INFG_LLM_MODEL=anthropic/claude-opus-4
INFG_OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

3. Run:

```bash
python3 scripts/generate_pretty.py \
  --text "Your data here" \
  --output pretty.html
```

Note: OpenRouter only supports the HTML-output path. Image generation always uses Gemini.

### Workflow

**Step 1 — Parse context** (same as the standard LinkedIn flow):
```bash
python scripts/parse_context.py \
  --root /path/to/project \
  --title "My App Architecture" \
  --output arch.json
```

**Step 2 — Generate pretty HTML (+ optional PNG)**:
```bash
python scripts/generate_pretty.py \
  --config arch.json \
  --output pretty_arch.html
```

Quick inline mode (no JSON file needed):
```bash
python scripts/generate_pretty.py \
  --layers "Frontend:React,Next.js|Backend:FastAPI,Celery|Database:PostgreSQL,Redis|Cloud:AWS S3,CloudFront" \
  --title "My SaaS Architecture" \
  --author "Your Name" \
  --output pretty_arch.html
```

With learnings focus (drives infographic content to emphasize specific technologies):
```bash
python scripts/generate_pretty.py \
  --config arch.json \
  --learnings "FastAPI async patterns, PostgreSQL JSONB for flexible schemas" \
  --output pretty.png
```

Dashboard / KPI mode (use `--type dashboard`):
```bash
python scripts/generate_pretty.py \
  --text "Revenue $2.4M (+18%), NPS 72, Churn 2.1%, New customers 340" \
  --type dashboard \
  --title "Q3 Performance" \
  --output pretty_kpis.html
```

Change the Gemini model (default `gemini-3.1-flash-image-preview`):
```bash
# Best quality HTML output (works on Vertex AI)
python scripts/generate_pretty.py --config arch.json --model gemini-2.5-pro --output pretty.html

# Fast + cheap (works on Vertex AI)
python scripts/generate_pretty.py --config arch.json --model gemini-2.0-flash --output pretty.html

# Native image generation — no Playwright needed (works on Vertex AI)
python scripts/generate_pretty.py --config arch.json --model gemini-2.5-flash-image --output pretty.png
```

Available models (Feb 2026):
| Model ID | Output | Backend | Notes |
|---|---|---|---|
| `gemini-3.1-flash-image-preview` | **PNG directly** | AI Studio | **Default** — newest image gen; auto-routed to AI Studio (INFG_API_KEY) |
| `gemini-2.5-flash-image` | **PNG directly** | Vertex AI | Stable image gen fallback, no Playwright needed |
| `gemini-2.5-pro` | HTML → PNG | Vertex AI | Best quality HTML output |
| `gemini-2.0-flash` | HTML → PNG | Vertex AI | Fast, lowest cost |
| `gemini-2.0-flash-lite` | HTML → PNG | Vertex AI | Cheapest option |
| `gemini-3-pro-preview` | HTML → PNG | AI Studio | Auto-routed to AI Studio (INFG_API_KEY) |
| `gemini-3.1-pro-preview` | HTML → PNG | AI Studio | Auto-routed to AI Studio (INFG_API_KEY) |

**Backend routing is automatic** — you never need to configure the backend manually.
The script reads both `INFG_API_KEY` and `INFG_VERTEX_PROJECT` from `.env` and routes
each model to the cheapest available endpoint that supports it.

### Cost report

Every invocation prints a cost breakdown immediately after generation:

```
┌──────────────────────────────────────────────┐
│            ⚡ Gemini Generation Cost          │
├──────────────────────────────────────────────┤
│  Model   gemini-3.1-flash-image-preview      │
├──────────────────────────────────────────────┤
│    Input      4,231 tok              $0.000317│
│    Image(s)       1 img              $0.039000│
├──────────────────────────────────────────────┤
│    TOTAL                             $0.039317│
└──────────────────────────────────────────────┘
  ⚠ Estimates — verify at: https://ai.google.dev/pricing
```

Fields shown when non-zero: input tokens, output tokens, thinking tokens, images generated.

### Icon enhancement (automatic for Gemini 2.5+)

When the selected model is **Gemini 2.5 or higher**, icon mode is activated
automatically — no extra flags needed.

| Model | What changes |
|---|---|
| Image models (`*-image`) | Gemini draws recognizable brand logos inside each chip — React atom, Docker whale, PostgreSQL elephant, Kubernetes helm, etc. in official brand colors. |
| HTML/text models | Each chip gets an inline SVG brand icon (16×16 px) or emoji fallback prepended to the text. Chip layout switches to `flex` row. |

The script prints `🎨  Icon mode: enabled` when active.

### What pretty mode produces

| Feature | Standard renderer | Pretty mode (Gemini < 2.5) | Pretty mode (Gemini 2.5+) |
|---|---|---|---|
| Output | `.png` via matplotlib | `.html` + auto `.png` via Playwright | same |
| Background | Light `#F8FAFC` | Rich dark gradient | same |
| Cards | Flat colored boxes | Glassmorphism (blur + rgba) | same |
| Animations | None | Float, blob, SVG draw-on | same |
| Arrows | Dashed matplotlib lines | Animated SVG stroke-dashoffset | same |
| Typography | System matplotlib fonts | CSS gradient clip text, 800 weight | same |
| **Icons** | **None** | **None** | **Brand logos per chip** |

### Decision rule

| User says | Action |
|---|---|
| "for linkedin" | Standard `generate_linkedin_arch.py` |
| "pretty" or "make pretty" | `generate_pretty.py` (Gemini mode) |
| "pretty for linkedin" | `generate_pretty.py` → PNG (Gemini mode) |

### Examples

**"Make our architecture diagram pretty for linkedin"**
→ Run `parse_context.py --root .` → `generate_pretty.py --config arch.json --output pretty.html`

**"Pretty infographic of Q3 KPIs: Revenue $2.4M, NPS 72, Churn 2.1%"**
→ `generate_pretty.py --text "..." --type dashboard --title "Q3 KPIs" --output q3.html`

**"Make this pretty: FastAPI backend, Flutter app, PostgreSQL, Redis, AWS"**
→ `generate_pretty.py --layers "Backend:FastAPI|Mobile:Flutter|Database:PostgreSQL,Redis|Cloud:AWS" --output pretty.html`

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

### Layer color reference

| Layer | Background | Border |
|---|---|---|
| Frontend | Light blue | Blue |
| Mobile | Lavender | Purple |
| Backend / API | Amber | Orange |
| Database | Mint | Green |
| Auth | Yellow | Gold |
| Queue / Events | Purple | Deep purple |
| Storage | Indigo light | Indigo |
| Cloud Services | Cyan | Teal |
| Infrastructure | Rose | Red |
| AI / ML | Emerald | Green |
| Monitoring | Warm gray | Brown |
| CI/CD | Slate | Gray |

**Learnings-focused posts:** When the user specifies technologies or learnings,
pass them via `--learnings` to generate_pretty.py so the infographic design
emphasizes those specific topics:
```bash
python scripts/generate_pretty.py \
  --learnings "Event-driven architecture with Kafka, CQRS pattern" \
  --layers "Backend:FastAPI|Queue:Kafka|Database:PostgreSQL" \
  --title "What I Learned Building Event-Driven Systems" \
  --output pretty.png
```

### Examples

**"Generate a linkedin post for this project"**
→ Run `parse_context.py --root .` → render with author from git config

**"Make our architecture diagram for linkedin, here's our CLAUDE.md: [paste]"**
→ Run `parse_context.py --text [pasted content]` → render

**"For linkedin: FastAPI backend, Flutter app, PostgreSQL, Redis, AWS"**
→ Run `parse_context.py --text "FastAPI backend, Flutter app, PostgreSQL, Redis, AWS"` → render

---

## Versioned Output — "Next Version" / "Nueva Version"

> **Trigger**: user includes any version-iteration phrase in any language — "next version",
> "nueva version", "siguiente version", "new version", "next design", "nouvelle version",
> "nächste version", "próxima versión", "nuova versione", or equivalent.

When this trigger is detected, run `scripts/version_output.py` **before** generating the
infographic to manage versioned output directories automatically.

### Directory structure (auto-created)

```
infographics/        ← or designs/, generated/, output/ if already exists
├── v1/              ← archived versions (read-only history)
├── v2/
├── v3/
└── v4_last/         ← always the current / latest version
```

### Step-by-step workflow

**Step 1 — Prepare the next version directory:**
```bash
OUTPUT=$(python scripts/version_output.py --root /path/to/project)
```
This prints the new version path to stdout (e.g. `/project/infographics/v2_last`) and
archives the previous `v{n}_last` → `v{n}` on stderr so you can see the history.

**Step 2 — Generate into that directory:**
```bash
# Standard mode
python scripts/generate.py --output "$OUTPUT/infographic.png" ...

# Pretty / Gemini mode
python scripts/generate_pretty.py --layers "..." --output "$OUTPUT/infographic.png"

# LinkedIn arch
python scripts/generate_linkedin_arch.py --config arch.json --output "$OUTPUT/linkedin_arch.png"
```

**Step 3 — Tell the user:**
- Which version was just created (e.g. "Saved as **v3_last**")
- Where the file is (full path)
- That previous versions are preserved in `v1/`, `v2/`, etc.

### List existing versions

```bash
python scripts/version_output.py --root /path/to/project --list
```

Output example:
```
  Versions in: /project/infographics
  ──────────────────────────────────────────
  v1              2 file(s)  [.html, .png]
  v2              1 file(s)  [.png]
  v3_last         1 file(s)  [.png]  ← current
```

### First call (no existing versions)

If no versioned directory exists yet, `version_output.py` creates `infographics/v1_last/`
automatically. No action needed from you — just capture the output and use it.

### Examples

**"Next version of the dashboard infographic"**
→ `OUTPUT=$(python scripts/version_output.py --root .)` → generate into `$OUTPUT/`

**"Nueva version, same style"**
→ Same as above — language doesn't matter, trigger is the same.

**"Show me the versions"**
→ `python scripts/version_output.py --root . --list`
