# Codebase Structure

**Analysis Date:** 2026-03-15

## Directory Layout

```
infographic-skill/
├── scripts/                  # Core generation engines
│   ├── generate.py          # PNG infographic generator (matplotlib)
│   ├── generate_html.py      # Interactive HTML generator (Chart.js)
│   ├── generate_linkedin_arch.py  # LinkedIn diagram generator
│   └── parse_context.py      # Architecture context parser
│
├── references/              # Design knowledge base
│   ├── design-principles.md  # Visual design rules
│   └── chart-selection.md    # Chart type decision matrix
│
├── templates/               # Example configs
│   └── example-config.json   # Template for HTML infographic config
│
├── SKILL.md                 # Skill definition & invocation guide
├── ROADMAP.md               # Project milestones
└── .planning/
    └── codebase/            # Architecture documentation (this folder)
```

## Directory Purposes

**scripts/:**
- Purpose: Executable Python generation engines
- Contains: Four CLI-callable modules + helper functions
- Key files: All four .py files are independently executable

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

**Configuration:**
- `templates/example-config.json`: Template for HTML infographic structure
- `SKILL.md`: Skill metadata (dependencies, allowed-tools, invocation patterns)
- `ROADMAP.md`: Project status

**Core Logic:**
- `scripts/generate.py` lines 75–383: InfographicCanvas class (all section builders)
- `scripts/parse_context.py` lines 28–99: Component detection heuristics
- `scripts/generate_linkedin_arch.py` lines 49–75: Group styling and layout engine

**Design References:**
- `references/design-principles.md`: Visual hierarchy, typography, color, whitespace
- `references/chart-selection.md`: Chart type decision tree with 10+ chart types

## Naming Conventions

**Files:**
- `generate*.py`: Output generators (PNG, HTML, LinkedIn)
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

**Constants:**
- `PALETTES`: Dict of color palettes
- `GROUP_STYLES`: Dict of category styling
- `CATEGORY_HINTS`: List of keywords per category
- `LAYER_ORDER`: List of category ordering for output

**Global settings:**
- `DEFAULT_PALETTE`: Default color palette name
- `LINKEDIN_W`, `LINKEDIN_H`, `LINKEDIN_DPI`: LinkedIn format constants
- `TITLE_BG`, `TITLE_FG`, `FOOTER_BG`, `ACCENT`: Color constants for LinkedIn diagrams

## Where to Add New Code

**New Output Format (PNG/HTML variant):**
- Primary code: `scripts/generate_new_format.py`
- Follow pattern: Import matplotlib/Chart.js, define new renderer function, add CLI argument parsing
- Reuse: PALETTES from generate.py, GROUP_STYLES from generate_linkedin_arch.py

**New Architecture Category (e.g., "blockchain"):**
- Update: `scripts/parse_context.py` CATEGORY_HINTS (line 28) — add keywords
- Update: CATEGORY_COLORS (lines 55–69) — add hex colors
- Update: CATEGORY_LABELS (lines 71–85) — add display name
- Update: LAYER_ORDER (lines 204–211) if appropriate
- Add icon: `scripts/generate_linkedin_arch.py` _draw_blockchain() function, add to _ICON_DRAW_FNS dict (lines 486–503)

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

**New Test or Example:**
- Demo: Update _demo() function in `scripts/generate.py` (lines 389–427)
- Example config: Add variant to `templates/example-config.json`

## Special Directories

**scripts/:**
- Purpose: All four are independently executable scripts
- Generated: No
- Committed: Yes (all source)
- Run directly: `python scripts/generate.py --demo`

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

---

*Structure analysis: 2026-03-15*
