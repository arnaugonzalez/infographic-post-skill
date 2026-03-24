# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```
infographic-skill/
├── scripts/                      # Core generation engines
│   ├── generate.py              # PNG infographic generator (matplotlib)
│   ├── generate_html.py          # Interactive HTML generator (Chart.js)
│   ├── generate_linkedin_arch.py # LinkedIn diagram generator
│   ├── generate_pretty.py        # AI-powered Gemini infographic generator
│   └── parse_context.py          # Architecture context parser
│
├── references/                   # Design knowledge base
│   ├── design-principles.md      # Visual design rules
│   └── chart-selection.md        # Chart type decision matrix
│
├── templates/                    # Example configs
│   └── example-config.json       # Template for HTML infographic config
│
├── SKILL.md                      # Skill definition & invocation guide
├── ROADMAP.md                    # Project milestones
├── .gitignore                    # Git ignore file
└── .planning/
    └── codebase/                 # Architecture documentation (this folder)
```

## Directory Purposes

**scripts/:**
- Purpose: Executable Python generation engines
- Contains: Five CLI-callable modules + helper functions
- Key files: All .py files are independently executable (except parse_context.py can be imported)

**references/:**
- Purpose: Codified design knowledge and decision matrices
- Contains: Markdown guides for design decisions
- Key files: `design-principles.md` (typography, color, layout rules), `chart-selection.md` (chart type decision tree)

**templates/:**
- Purpose: Example configurations for users to copy/adapt
- Contains: JSON template with all available fields
- Key files: `example-config.json` with KPIs, charts, callout, process steps

**.planning/codebase/:**
- Purpose: Architecture documentation (you are here)
- Contains: ARCHITECTURE.md, STRUCTURE.md (and other GSD docs)
- Key files: Analysis documents for Claude orchestrator

## Key File Locations

**Entry Points:**
- `scripts/generate.py`: PNG infographic generation (CLI or library import)
- `scripts/generate_html.py`: Interactive HTML generation (CLI only)
- `scripts/generate_linkedin_arch.py`: LinkedIn architecture diagrams (CLI only)
- `scripts/parse_context.py`: Extract architecture from context (CLI only)
- `scripts/generate_pretty.py`: AI-powered Gemini infographic generation (CLI only)

**Configuration:**
- `templates/example-config.json`: Template for HTML infographic structure
- `.env`: Environment variables (INFG_API_KEY, INFG_VERTEX_PROJECT, INFG_VERTEX_LOCATION) - not committed
- `SKILL.md`: Skill metadata (dependencies, allowed-tools, invocation patterns)
- `ROADMAP.md`: Project status

**Core Logic:**
- `scripts/generate.py` lines 75–383: InfographicCanvas class (all section builders)
- `scripts/parse_context.py` lines 84–135: Component detection heuristics
- `scripts/generate_linkedin_arch.py` lines 49–75: Group styling and layout engine
- `scripts/generate_pretty.py` lines 96–600: Gemini backend routing and generation

**Design References:**
- `references/design-principles.md`: Visual hierarchy, typography, color, whitespace
- `references/chart-selection.md`: Chart type decision tree with 10+ chart types

## Naming Conventions

**Files:**
- `generate*.py`: Output generators (PNG, HTML, LinkedIn, AI)
- `parse*.py`: Input/context parsers
- `*-principles.md`: Design guidance
- `*-selection.md`: Decision matrices
- `example-*.json`: Copyable configuration templates

**Directories:**
- `scripts/`: Lowercase, dash-separated for non-Python files in output
- `references/`: Lowercase, plural for collections of guidance
- `templates/`: Lowercase, stores reusable JSON/config templates

**Python classes:**
- `InfographicCanvas`: Noun-based, represents a drawable canvas object

**Python functions:**
- `add_*()`: Canvas section builders (add_header, add_kpi_row, add_bar_chart)
- `draw_*()`: Low-level shape drawing (draw_rounded_box, draw_component_chip)
- `_draw_*()`: Icon drawing (internal, prefixed with underscore)
- `get_*()`: Accessors (get_style)
- `extract_*()`: Extraction from text (extract_components_from_text)
- `detect_*()`: Heuristic detection (detect_category)
- `read_*()`: File I/O (read_claude_md, read_file)
- `_build_*()`: Internal builders (e.g., _build_genai_client)
- `_gen_*()`: Internal generation methods (e.g., _gen_image_direct)

**Constants:**
- `PALETTES`: Dict of color palettes
- `GROUP_STYLES`: Dict of category styling
- `CATEGORY_HINTS`: List of keywords per category
- `LAYER_ORDER`: List of category ordering for output
- `LINKEDIN_W`, `LINKEDIN_H`, `LINKEDIN_DPI`: LinkedIn format constants

**Global settings:**
- `DEFAULT_PALETTE`: Default color palette name
- `TITLE_BG`, `TITLE_FG`, `FOOTER_BG`, `ACCENT`: Color constants for LinkedIn diagrams
- `_VERTEX_PROJECT`, `_VERTEX_LOCATION`, `_USE_VERTEX`: Gemini backend configuration from .env

## Where to Add New Code

**New Output Format (PNG/HTML variant):**
- Primary code: `scripts/generate_new_format.py`
- Follow pattern: Import matplotlib/Chart.js, define new renderer function, add CLI argument parsing
- Reuse: PALETTES from generate.py, GROUP_STYLES from generate_linkedin_arch.py

**New Architecture Category (e.g., "blockchain"):**
- Update: `scripts/parse_context.py` CATEGORY_HINTS (line 84) — add keywords
- Update: CATEGORY_COLORS (lines 38–52) — add hex colors
- Update: CATEGORY_LABELS (lines 54–68) — add display name
- Update: LAYER_ORDER (lines 70–77) if appropriate
- Add icon: `scripts/generate_linkedin_arch.py` _draw_blockchain() function, add to _ICON_DRAW_FNS dict

**New Design Principle or Chart Rule:**
- Add section: `references/design-principles.md` or `references/chart-selection.md`
- Format: Markdown with heading, explanation, examples
- Reference in: SKILL.md Step 1 guidance or ARCHITECTURE.md if it affects code

**New Canvas Section (e.g., add_timeline):**
- Location: `scripts/generate.py` add method to InfographicCanvas class
- Pattern: Follow add_process_flow() (lines 317–354) as template
  - Accept: data (list of dicts or tuples)
  - Accept: positioning (top, height)
  - Use: self.fig.add_axes(), ax.text(), matplotlib patches
  - Return: self (for chaining)

**New AI Generation Mode (Gemini variant):**
- Location: `scripts/generate_pretty.py` — add new model handler
- Pattern: Follow _gen_image_direct() or _gen_via_html_to_png() as template (lines 300–500)
  - Accept: genai Client, model name, prompt
  - Handle: model-specific response format
  - Return: PIL Image or HTML string
  - Add: model name to MODEL_METADATA dict (line 760+)

**New Test or Example:**
- Demo: Update _demo() function in `scripts/generate.py` (lines 389–427)
- Example config: Add variant to `templates/example-config.json`

## Special Directories

**scripts/:**
- Purpose: All five are independently executable scripts
- Generated: No
- Committed: Yes (all source)
- Run directly: `python scripts/generate.py --demo`
- Environment: generate_pretty.py reads .env for Gemini credentials

**references/:**
- Purpose: Static guidance; never generated
- Generated: No
- Committed: Yes (hand-written markdown)
- Read by: Claude instances before making design decisions

**templates/:**
- Purpose: User copies these as starting points
- Generated: No (but users may generate new .json files here)
- Committed: Yes (examples only)
- Updated: When new config fields are added to generators

**.planning/:**
- Purpose: GSD orchestrator documentation
- Generated: Yes (by GSD agents)
- Committed: Yes (part of codebase analysis)
- Structure: .planning/codebase/ for architecture docs, .planning/quick/ for task status

**.env (not committed):**
- Purpose: Runtime secrets for Gemini backends
- Contains: INFG_API_KEY, INFG_VERTEX_PROJECT, INFG_VERTEX_LOCATION
- Used by: generate_pretty.py (lines 51–68)
- Pattern: Key=value format, loaded at startup via _load_dotenv()

## Invocation Patterns

**PNG Infographic (standalone demo):**
```bash
python scripts/generate.py --demo
# Output: demo_infographic.png (1080×1350px @ 150dpi)
```

**PNG Infographic (custom, via library import):**
```python
from scripts.generate import InfographicCanvas
canvas = InfographicCanvas(1080, 1920, dpi=150, palette="modern-blue")
canvas.add_header("Title", subtitle="Subtitle")
canvas.add_kpi_row(kpis=[("$2.4M", "Revenue", "+18%")])
canvas.save("output.png")
```

**HTML Interactive Infographic:**
```bash
python scripts/generate_html.py --config templates/example-config.json --output infographic.html
# Reads JSON, renders HTML with Chart.js
```

**LinkedIn Architecture Diagram (from config):**
```bash
python scripts/parse_context.py --root /path/to/project --output arch.json
python scripts/generate_linkedin_arch.py --config arch.json --output arch.png
# Output: 1080×1080px @ 150dpi
```

**LinkedIn Architecture Diagram (quick inline):**
```bash
python scripts/generate_linkedin_arch.py \
  --layers "Frontend:React,Next.js|Backend:FastAPI|Database:PostgreSQL" \
  --title "My App" --output arch.png
```

**AI-Generated Infographic (Gemini Pretty Mode):**
```bash
# From architecture config
python scripts/generate_pretty.py --config arch.json --output pretty.png

# Quick inline (automatic backend detection)
python scripts/generate_pretty.py \
  --layers "Frontend:React|Backend:FastAPI|Database:PostgreSQL" \
  --title "My App" --author "Your Name" --output pretty.png

# Dashboard/KPI type
python scripts/generate_pretty.py \
  --text "Revenue $2.4M (+18%), NPS 72, Churn 2.1%" \
  --type dashboard --title "Q3 Performance" --output pretty.png

# With specific Gemini model
python scripts/generate_pretty.py \
  --config arch.json --model gemini-2.5-pro --output pretty.html
```

**Gemini Backend Selection (automatic):**
- If `--model` starts with "gemini-3.1-flash-image-preview" → AI Studio (INFG_API_KEY)
- If `--model` is other image model → Vertex AI (INFG_VERTEX_PROJECT)
- If `--model` is text model → Vertex AI
- If only one backend configured → route to that backend

---

*Structure analysis: 2026-03-20*
