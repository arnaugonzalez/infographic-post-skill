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
Renderers: in-session Claude HTML ($0), Claude Opus HTML, Gemini 3 Pro Image, Jinja template, Matplotlib.

---

## Quick Reference — What Command to Run

| User says | Command |
|-----------|---------|
| "Make an infographic of this project" | `python3 scripts/generate_pretty.py --codebase . --output infographic.png` |
| "Architecture infographic for LinkedIn" | `python3 scripts/generate_pretty.py --codebase . --style editorial --output infographic.png` |
| "Compare before vs after" | `python3 scripts/generate_pretty.py --codebase . --infographic-type comparison --output compare.png` |
| "Explain how auth works as infographic" | `python3 scripts/generate_pretty.py --codebase . --infographic-type feature --output feature.png` |
| "Show the deployment pipeline" | `python3 scripts/generate_pretty.py --codebase . --infographic-type process --output process.png` |
| "Cheat sheet of our API" | `python3 scripts/generate_pretty.py --codebase . --infographic-type cheatsheet --output cheatsheet.png` |
| "Make it look less like AI" / "in my style" | Add `--style-dir <folder with the user's own .html graphics>` |
| "Technical / dark / poster look" | Add `--style blueprint`, `terminal`, `swiss` or `brutalist` |
| "Banner for GitHub / X" | Add `--format landscape` (1280×640) |
| "Make it cheap / budget mode" | In Claude Code: in-session mode ($0). Otherwise `--renderer template` |
| "LinkedIn posts from codebase" | `python3 scripts/generate_posts.py . --language en` |
| "Quality audit" | `python3 scripts/oss_audit.py --root .` |
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

## Step 2 — Determine the Art Direction

The goal is a graphic that does not look like every other AI infographic. Pick ONE archetype
(full descriptions in `scripts/prompts/archetypes.md`):

| Archetype | Flag | Look |
|-----------|------|------|
| `editorial` | `--style editorial` | Default. Paper and ink, display serif, numbered rows, one accent. Magazine page. |
| `blueprint` | `--style blueprint` | Engineering drawing: grid, monospace labels, outlined boxes, one signal color. |
| `terminal` | `--style terminal` | One monospace family; command, output and the line that matters. |
| `swiss` | `--style swiss` | Poster: neo-grotesque, strict grid, a huge number, one primary color. |
| `brutalist` | `--style brutalist` | Zine: thick borders, heavy grotesque, one loud flat color block. |

Canvas: `--format portrait` (1080×1350, default, best on LinkedIn), `square` (1080×1080) or
`landscape` (1280×640, GitHub social preview).

The brief makes the model write a `thesis`/`hero`/`archetype`/`cut` comment before drawing, keep
~12 elements, and avoid a banned list (gradients, glow, glassmorphism, card grids, emoji, purple,
Inter as display face, generic subtitles). Reference pages in `style/` (the author's own graphics)
are added to the prompt; point `--style-dir` (or `INFG_STYLE_DIR`) at a folder of the user's own
`.html` graphics to make the output match their style. `--finish` prints a warning for every
banned pattern it finds; if there are warnings, fix the HTML and run `--finish` again.

Old names still work: `modern-light` → editorial, `modern-dark` → blueprint, `illustrated` → swiss.

## Step 3 — Generate

### From a codebase (most common)

```bash
python3 scripts/generate_pretty.py \
  --codebase /path/to/project \
  --title "My App" \
  --infographic-type architecture \
  --style editorial \
  --output infographic.png
```

The pipeline:
1. `project_digest.py` builds an architecture-first digest (tree, manifests, README) — ~1.5–5k tokens
2. `content_structurer.py` sends it to an LLM → structured JSON (Haiku 5.5 ~$0.001 / Gemini 3.8 Flash ~$0.012)
3. The renderer chosen by `--renderer` produces the PNG (see Rendering Modes)
4. Falls back to the HTML template if the image API fails

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

Choose with `--renderer` (default `auto`). Scores: blind benchmark, 3 real codebases × 2 judges,
mean of 6 criteria out of 10 (`benchmark/RESULTS.md`, Oct 2026).

| Renderer | Flag | $/image | Score | Pick it when |
|---|---|---|---|---|
| **In-session Claude HTML** | see below | **$0** | ≈7.0 | You are running inside Claude Code — always prefer this |
| Claude HTML (Opus 5.5, effort low) | `--renderer claude-html` | ~$0.18 | 7.00 | Exact names/completeness matter (technical audience) |
| Gemini image (`gemini-3-pro-image`, 2K) | `--renderer image` | $0.134 | 6.97 | Maximum visual punch, real-looking logos |
| Jinja template | `--renderer template` | $0 | 5.14 | Offline / no keys (small text — weak on phones) |

`auto` = Gemini image if `INFG_API_KEY` is set, else Claude HTML if `ANTHROPIC_API_KEY` is set, else template.
Avoid `gemini-3.1-flash-image` at 1K (scored last: garbled text, missing items) and
`gemini-3.1-flash-lite-image` except for throwaway drafts.

### 🧠 In-session mode (recommended inside Claude Code — no API cost)

You (the agent) are the designer; only structuring needs a cheap API call.

```bash
# 1. Structure the codebase and save the spec (Haiku 5.5, ~$0.001) — template render is free
python3 scripts/generate_pretty.py --codebase /path/to/project --renderer template \
  --save-spec spec.json --output draft.png
# 2. Print the design brief
python3 scripts/claude_html_renderer.py --spec spec.json --style editorial --print-brief
```

3. Write `page.html` that follows the brief exactly. Use `<span class="logo" data-icon="Tech Name"></span>`
   for every technology (real brand SVGs or monograms are injected). Keep every name exactly as in the spec.
4. Finish and screenshot:

```bash
python3 scripts/claude_html_renderer.py --finish page.html --output infographic.png   # 2160×2160 PNG
```

If you can view images, look at the PNG and fix overlaps or text under ~16px before delivering.

### 🎨 API modes

```bash
python3 scripts/generate_pretty.py --codebase . --renderer claude-html --output infographic.png
python3 scripts/generate_pretty.py --codebase . --renderer image --output infographic.png
```

### 📊 Matplotlib (fully offline — free)

```bash
python3 scripts/parse_context.py --root . --output arch.json
python3 scripts/generate_linkedin_arch.py --config arch.json --output arch.png
```

---

## Choosing a backend and model

Check which subscription CLIs and credentials are available on your machine:

```bash
python3 scripts/doctor.py
```

| Backend | Binary / Mode | Default model | Billing |
|---------|---------------|---------------|---------|
| `session` | Host agent (`CLAUDECODE=1`) | Host model | Subscription |
| `claude` | `claude -p` | `claude-opus-5-5` | Subscription |
| `agy` | `agy -p` | `claude-opus-5-5-low` | Subscription |
| `codex` | `codex exec` | CLI default | Subscription |
| `copilot` | `copilot -p` | `auto` | Subscription |
| `opencode` | `opencode run` | CLI default | Subscription |
| `api` | Anthropic / AI Studio SDK | `claude-haiku-5-5` / `gemini-3.8-flash` | Paid API (per use) |

- **Rule: `auto` never picks a paid API.** Resolution order is `--backend` / `--model` > `INFG_BACKEND` / `INFG_MODEL` > `auto` (`session` when `CLAUDECODE` is set, otherwise the first installed CLI in `claude, agy, codex, copilot, opencode`). To use paid API keys (`ANTHROPIC_API_KEY` or `INFG_API_KEY`), pass `--backend api` explicitly (or `--renderer image`).
- Inspect the exact prompt (brief + backend contract + model-family note) without running a model:
  ```bash
  python3 scripts/claude_html_renderer.py --backend agy --model gemini-4-argon-high --spec spec.json --print-prompt
  ```

---

## CLI Reference

```bash
python3 scripts/generate_pretty.py \
  --codebase <dir>                    # Read and analyze a codebase
  --title "Title"                     # Override title
  --infographic-type <type>           # architecture|comparison|feature|process|cheatsheet
  --style <archetype>                 # editorial|blueprint|terminal|swiss|brutalist
  --format <canvas>                   # portrait|square|landscape (HTML renderer)
  --style-dir <dir>                   # your own .html graphics as reference
  --renderer <r>                      # auto|image|claude-html|template (default: auto)
  --save-spec spec.json               # Save structured JSON (for in-session mode)
  --model <gemini-model>              # Image model (default: gemini-3-pro-image, 2K)
  --llm-model <model>                 # claude-* | gemini-* | vendor/model (OpenRouter); default: auto
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
ANTHROPIC_API_KEY=                    # Claude: structuring (Haiku 5.5) + claude-html renderer (Opus 5.5)
INFG_API_KEY=                         # Google AI Studio: gemini-3-pro-image + gemini structuring
INFG_LLM_MODEL=                       # Empty = auto (claude-haiku-5-5, else gemini-3.8-flash)
INFG_IMAGE_SIZE=2K                    # 1K | 2K | 4K for Gemini image models
INFG_OPENROUTER_API_KEY=              # Only for vendor/model ids

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
| `project_digest.py` | Architecture-first codebase digest (tree, manifests, README) |
| `content_structurer.py` | LLM → structured JSON (Anthropic / Gemini / OpenRouter) |
| `claude_html_renderer.py` | Claude/in-session HTML → logo injection → 2160px PNG |
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
