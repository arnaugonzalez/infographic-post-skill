---
name: infographic
description: >
  Create professional, designer-quality infographics from codebases, data, text, or concepts.
  TRIGGERS — invoke this skill when the user mentions ANY of:
    infographics, data visualization, visual summaries, architecture diagrams,
    system design visuals, process diagrams, comparison visuals, cheat sheets,
    "for linkedin", "linkedin infographic", "linkedin diagram", "linkedin post",
    "make data visual", "turn this into a graphic", "pretty", "make pretty",
    "architecture infographic", "tech stack diagram", "explain as infographic"
  MULTILINGUAL TRIGGERS — also activate for:
    "infografía", "infográfico", "diagrama de arquitectura", "para linkedin",
    "infographie", "Infografik", "infografica"
  VERSIONING — when the user says "next version" / "nueva version" / "new version"
    in any language, run scripts/version_output.py before generating.
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
    - simplepycons>=1.0
    - jinja2>=3.1
---

# Infographic Skill

Generate publication-ready infographics from codebases, data, or text.
Three rendering modes: AI Image (★★★★★), HTML Template (★★★★☆), Matplotlib (★★★☆☆).

---

## Quick Reference — What Command to Run

| User says | Command |
|-----------|---------|
| "Make an infographic of this project" | `python3 scripts/generate_pretty.py --codebase . --output infographic.png` |
| "Architecture infographic for LinkedIn" | `python3 scripts/generate_pretty.py --codebase . --style modern-dark --output infographic.png` |
| "Compare before vs after" | `python3 scripts/generate_pretty.py --codebase . --infographic-type comparison --output compare.png` |
| "Explain how auth works as infographic" | `python3 scripts/generate_pretty.py --codebase . --infographic-type feature --output feature.png` |
| "Show the deployment pipeline" | `python3 scripts/generate_pretty.py --codebase . --infographic-type process --output process.png` |
| "Cheat sheet of our API" | `python3 scripts/generate_pretty.py --codebase . --infographic-type cheatsheet --output cheatsheet.png` |
| "Illustrated style" | Add `--style illustrated` to any command above |
| "Light mode / clean style" | Add `--style modern-light` to any command above |
| "Make it cheap / budget mode" | Add `--legacy-html` to use HTML template instead of AI image |
| "LinkedIn posts from codebase" | `python3 scripts/generate_posts.py . --language en` |
| "Quality audit" | `python3 oss_audit.py --root .` |
| "Pretty KPI dashboard" | `python3 scripts/generate_pretty.py --text "Revenue $2.4M, NPS 72" --type dashboard --output kpis.png` |

---

## Step 1 — Determine the Infographic Type

Ask the user or infer from context:

| Type | Flag | When to use |
|------|------|-------------|
| `architecture` | `--infographic-type architecture` | Default. System components + data flow. |
| `comparison` | `--infographic-type comparison` | Before/after, v1 vs v2, old vs new. |
| `feature` | `--infographic-type feature` | How a specific feature works step-by-step. |
| `process` | `--infographic-type process` | Pipeline, workflow, sequential stages. |
| `cheatsheet` | `--infographic-type cheatsheet` | Reference card, API endpoints, config options. |

## Step 2 — Determine the Visual Style

| Style | Flag | Look |
|-------|------|------|
| `modern-dark` | `--style modern-dark` | Default. Deep navy, glowing orbs, Stripe/Vercel feel. Best for LinkedIn. |
| `illustrated` | `--style illustrated` | Rich gradient, clouds/atmosphere, Canva premium feel. Maximum visual impact. |
| `modern-light` | `--style modern-light` | Clean white, soft shadows, Apple WWDC style. Best for print/docs. |

## Step 3 — Generate

### From a codebase (most common)

```bash
python3 scripts/generate_pretty.py \
  --codebase /path/to/project \
  --title "My App" \
  --infographic-type architecture \
  --style modern-dark \
  --output infographic.png
```

The pipeline:
1. `read_codebase.py` scans the project (skips node_modules, .git, binaries)
2. `content_structurer.py` sends report to LLM → gets structured JSON (layers, connections)
3. `image_prompt_builder.py` builds a designer-brief prompt with brand icon descriptions
4. Gemini image model generates a 1080×1080px publication-quality PNG (~$0.04)
5. Falls back to HTML template if Gemini unavailable

### From inline data

```bash
# Quick architecture from text
python3 scripts/generate_pretty.py \
  --layers "Frontend:React,Next.js|Backend:FastAPI|Database:PostgreSQL,Redis" \
  --title "My App" --output infographic.png

# KPI dashboard
python3 scripts/generate_pretty.py \
  --text "Revenue $2.4M (+18%), NPS 72, Churn 2.1%" \
  --type dashboard --title "Q3 KPIs" --output kpis.png
```

### LinkedIn posts from codebase

```bash
python3 scripts/generate_posts.py /path/to/project --language en
```

Generates two posts (technical + business angle) → stdout + `linkedin_posts.md`.

---

## Rendering Modes

### 🎨 AI Image (default — best quality)

**Cost:** ~$0.04/image | **Requires:** `INFG_API_KEY` (Google AI Studio)

Gemini image model generates a publication-quality PNG directly. Illustrated backgrounds, large brand logos, data flow arrows. Looks like a Canva/Figma design.

```bash
# Default command — uses AI Image automatically if INFG_API_KEY is set
python3 scripts/generate_pretty.py --codebase . --output infographic.png
```

### 🖥️ HTML Template (fallback — free rendering)

**Cost:** ~$0.001 (LLM structuring only) | **Requires:** `INFG_OPENROUTER_API_KEY`

Jinja2 template with glassmorphism, SVG brand icons (3,414 brands), connection arrows. Playwright screenshots to PNG.

```bash
# Force HTML template mode
python3 scripts/generate_pretty.py --codebase . --legacy-html --output infographic.html
```

### 📊 Matplotlib (fully offline — free)

**Cost:** Free | **Requires:** Nothing

```bash
python3 scripts/parse_context.py --root . --output arch.json
python3 scripts/generate_linkedin_arch.py --config arch.json --output arch.png
```

---

## CLI Reference

```bash
python3 scripts/generate_pretty.py \
  --codebase <dir>                    # Read and analyze a codebase
  --title "Title"                     # Override title
  --infographic-type <type>           # architecture|comparison|feature|process|cheatsheet
  --style <style>                     # modern-dark|modern-light|illustrated
  --model <gemini-model>              # Image model (default: gemini-3.1-flash-image-preview)
  --llm-model <model>                 # LLM for structuring (default: INFG_LLM_MODEL env)
  --output <path>                     # Output file
  --legacy-html                       # Force HTML template rendering
  --template <name>                   # Jinja2 template name
  --learnings "topic"                 # Focus infographic on specific technologies
  --author "Name"                     # Author attribution
  --cta "Follow text"                 # Footer call-to-action
```

---

## Environment Variables (.env)

```bash
# AI Image mode (recommended)
INFG_API_KEY=                         # Google AI Studio key → enables ★★★★★ AI image

# LLM for codebase structuring
INFG_OPENROUTER_API_KEY=              # OpenRouter key → enables codebase analysis
INFG_LLM_MODEL=google/gemini-2.5-flash  # Tier 2 default — good accuracy, low cost

# Optional
INFG_VERTEX_PROJECT=                  # Vertex AI project ID (alternative to AI Studio)
INFG_IMAGE_MODEL=                     # Override default image model
INFG_LLM_PROVIDER=                    # Force provider: gemini or openrouter
```

---

## Versioned Output

When the user says "next version" / "nueva versión" in any language:

```bash
OUTPUT=$(python3 scripts/version_output.py --root .)
python3 scripts/generate_pretty.py --codebase . --output "$OUTPUT/infographic.png"
```

---

## Project Scripts

| Script | Purpose |
|--------|---------|
| `generate_pretty.py` | Main entry point — routes to AI image / HTML template / legacy |
| `content_structurer.py` | LLM → structured JSON (layers, connections, title) |
| `image_prompt_builder.py` | JSON → designer-quality image prompt (70+ brand icons) |
| `template_renderer.py` | Jinja2 HTML template rendering with icon enrichment |
| `icon_registry.py` | 3,414 brand SVG icons via simplepycons + fuzzy matching |
| `model_quality.py` | LLM tier classification (1/2/3) + CLI warnings |
| `read_codebase.py` | Noise-filtered codebase reader with token budget |
| `generate_posts.py` | LinkedIn dual-angle post generator (tech + business) |
| `generate.py` | Core matplotlib PNG generator |
| `generate_html.py` | Interactive HTML generator (Chart.js) |
| `generate_linkedin_arch.py` | Matplotlib architecture diagrams |
| `parse_context.py` | Project context parser → arch.json |
| `version_output.py` | Versioned output directory manager |
| `oss_audit.py` | OSS quality audit (coverage, docs, complexity) |

---

## Design References

Read before customizing templates:
- `references/design-principles.md` — Visual hierarchy, color, typography rules
- `references/chart-selection.md` — Chart type decision matrix
- `references/competitive-research.md` — Gap analysis vs Napkin AI, Canva, etc.
- `references/visual-quality-patterns.md` — Premium CSS/SVG techniques
- `references/linkedin-visual-analysis.md` — Real LinkedIn post analysis
