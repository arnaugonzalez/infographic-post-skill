# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** Modular, single-responsibility Python skill with layered generation pipeline + AI-powered "pretty" mode

**Key Characteristics:**
- Canvas-first design — high-level abstraction for building infographic sections
- Context parsing → JSON serialization → rendering pipeline
- Multiple independent output generators (PNG, HTML, LinkedIn diagrams, AI-generated)
- Reference-driven (design principles, chart selection guide)
- CLI-driven execution with optional JSON config files
- Optional Gemini backend for AI-powered generation

## Layers

**Reference & Knowledge Layer:**
- Purpose: Codified design rules and decision matrices
- Location: `references/design-principles.md`, `references/chart-selection.md`
- Contains: Design constraints, typography rules, chart type guidance, color palettes
- Depends on: Nothing
- Used by: Human operators (Claude instances) for design decisions

**Context Parsing Layer:**
- Purpose: Extract architecture components and relationships from project context
- Location: `scripts/parse_context.py`
- Contains: Component detection heuristics, category mapping, layer grouping, connection inference
- Depends on: File I/O (CLAUDE.md, project directories, README)
- Used by: JSON generation for LinkedIn diagrams, AI generation

**Generation Engine Layer:**
- Purpose: High-level canvas abstractions and AI-powered rendering
- Location: `scripts/generate.py` (PNG/matplotlib), `scripts/generate_html.py` (HTML/Chart.js), `scripts/generate_linkedin_arch.py` (LinkedIn diagrams), `scripts/generate_pretty.py` (AI-generated infographics)
- Contains: InfographicCanvas class with section builders (headers, KPIs, charts, callouts, process flows), color palettes, typography utilities, Gemini SDK integration
- Depends on: matplotlib (PNG), Chart.js via CDN (HTML), matplotlib (LinkedIn diagrams), google-genai SDK (AI generation)
- Used by: CLI entry points

**Configuration & Templates:**
- Purpose: Example configs and reusable JSON structures
- Location: `templates/example-config.json`
- Contains: KPI cards, chart definitions, callout text, process steps
- Depends on: JSON schema
- Used by: generate_html.py for templating, generate_pretty.py for AI prompts

**Documentation Layer:**
- Purpose: Skill definition and roadmap
- Location: `SKILL.md`, `ROADMAP.md`
- Contains: Invocation patterns, usage examples, design rules, LinkedIn trigger conditions
- Depends on: Nothing
- Used by: Orchestrator to understand when/how to invoke

## Data Flow

**PNG Infographic Generation:**

1. User provides data/request → Claude interprets request
2. Claude imports InfographicCanvas, defines layout (header, KPIs, bars, donuts, callout, process flow)
3. Canvas accumulates sections (chained method calls)
4. Canvas.save() → matplotlib renders to PNG at specified DPI
5. Output: High-DPI PNG file (150–300 DPI configurable)

**HTML Interactive Infographic:**

1. User provides data + config structure
2. Python reads JSON config → generate_html.py
3. Template fills placeholders (colors, metadata, chart definitions)
4. Chart.js renders interactively in browser (loaded from CDN)
5. Output: Self-contained HTML file with embedded config

**LinkedIn Architecture Diagram:**

1. Context source: CLAUDE.md, directory scan, or free-form text
2. parse_context.py extracts components → groups by category → infers connections
3. Outputs: arch.json (serialized architecture)
4. generate_linkedin_arch.py renders: title bar, layer grid, group icons, component chips, dashed arrows, footer
5. Output: 1080×1080px PNG optimized for LinkedIn

**AI-Generated Infographic (Gemini Pretty Mode):**

1. User provides: config JSON (arch.json, dashboard data) OR inline text + type
2. generate_pretty.py detects backend: AI Studio (gemini-3.1-flash-image-preview) or Vertex AI (gemini-2.5-pro, gemini-2.5-flash-image)
3. Builds prompt from config or text → sends to Gemini SDK
4. Gemini generates: native PNG (image models) OR HTML (text models, converted to PNG via Playwright)
5. Tracks costs (input/output tokens) → prints breakdown
6. Output: PNG or HTML file with generated infographic

**State Management:**

- Stateless: Each generation is independent
- No persistence between runs (configs are ephemeral)
- Caches are implicit (matplotlib figure objects live for the duration of canvas operations)
- Backend state: Gemini API keys loaded from .env at startup

## Key Abstractions

**InfographicCanvas (generate.py):**
- Purpose: High-level builder for matplotlib-based infographics
- Examples: `scripts/generate.py` lines 75–383
- Pattern: Method chaining (add_header → add_kpi_row → add_bar_chart → save)
- Encapsulates: Figure setup, DPI conversion, color palettes, typography utilities

**Component Detection System (parse_context.py):**
- Purpose: Infer technology categories from text and directory names
- Examples: CATEGORY_HINTS (lines 84–125), detect_category() (lines 128–135)
- Pattern: Fuzzy string matching on hints + regex patterns
- Encapsulates: Architecture knowledge (what's backend vs. frontend vs. infrastructure)

**Group Icons (generate_linkedin_arch.py):**
- Purpose: Draw semantic icons for each architecture category
- Examples: _draw_frontend(), _draw_database(), _draw_cloud() (lines 230–393)
- Pattern: Low-level matplotlib primitives (circles, rectangles, arcs)
- Encapsulates: Visual library for architecture diagrams

**Gemini Integration (generate_pretty.py):**
- Purpose: Route requests to Google Gemini and handle AI-powered generation
- Examples: _build_genai_client(), _gen_image_direct(), _gen_via_html_to_png() (lines 96–500+)
- Pattern: Backend detection (AI Studio vs. Vertex AI) + model-specific rendering
- Encapsulates: Cost tracking, error recovery, API integration

**Color Palettes:**
- Purpose: Consistency across outputs
- Examples: PALETTES in generate.py, GROUP_STYLES in generate_linkedin_arch.py
- Pattern: Dict lookup by name or category
- Encapsulates: WCAG AA compliant color sets for different themes

## Entry Points

**generate.py (PNG generation):**
- Location: `scripts/generate.py` lines 430–448
- Triggers: User calls with --demo flag OR Claude imports InfographicCanvas
- Responsibilities: CLI argument parsing, canvas setup, demo/custom rendering, file output

**generate_html.py (HTML generation):**
- Location: `scripts/generate_html.py` lines 380–389
- Triggers: User calls with --config path
- Responsibilities: Load JSON config, format HTML template, render Chart.js charts, output HTML

**generate_linkedin_arch.py (LinkedIn diagram):**
- Location: `scripts/generate_linkedin_arch.py` lines 792–826
- Triggers: User calls with --config arch.json OR --layers string
- Responsibilities: Parse layers/connections, compute grid layout, render boxes/icons/arrows, save PNG

**parse_context.py (Context parsing):**
- Location: `scripts/parse_context.py` lines 337–369
- Triggers: User calls with --root / --text / --file
- Responsibilities: Extract components from context, group into layers, infer connections, output JSON

**generate_pretty.py (AI-powered generation):**
- Location: `scripts/generate_pretty.py` lines 600–846 (CLI entry points)
- Triggers: User calls with --config arch.json OR --text / --type parameters
- Responsibilities: Backend routing (AI Studio/Vertex), Gemini API calls, cost tracking, output management

## Error Handling

**Strategy:** Fail-fast with descriptive messages. No silent fallbacks.

**Patterns:**

- **File I/O errors (parse_context.py):** Try-except with default returns (e.g., read_claude_md returns "" if not found)
- **Missing config (generate_linkedin_arch.py):** Check --config XOR --layers; raise SystemExit(1) if neither provided
- **Invalid JSON (generate_html.py):** Let json.load() raise JSONDecodeError; user must provide valid config
- **Matplotlib failures:** Propagate; user will see matplotlib error messages
- **Assertion errors (generate.py):** e.g., assert len(values) <= 5 for donuts (line 260)
- **Gemini API errors (generate_pretty.py):** Catch genai exceptions, print diagnostic, exit with status code (lines 400–450)
- **Missing .env (generate_pretty.py):** Falls back to empty string; errors occur on first API call if keys not set (lines 51–68)

## Cross-Cutting Concerns

**Logging:** Simple print() statements with emoji prefixes (✅, ℹ️, ❌) for status feedback

**Validation:**
- DPI must be positive integer
- Canvas width/height must be positive
- Palette name must exist in PALETTES dict
- Chart labels/values must have same length
- Gemini model name must be known (generate_pretty.py line 760+)
- Backend credentials (.env INFG_API_KEY or INFG_VERTEX_PROJECT) must be set before generation

**Authentication:**
- generate_pretty.py requires: INFG_API_KEY (AI Studio) OR INFG_VERTEX_PROJECT (Vertex AI)
- Loaded from .env file at module initialization (lines 51–68)
- Backend routing is automatic based on available credentials

**Color Safety:**
- WCAG AA compliance built into palettes (generate.py lines 29–66)
- Colorblind-safe recommendations in design-principles.md
- Group icons use categorical colors (generate_linkedin_arch.py GROUP_STYLES)

---

*Architecture analysis: 2026-03-20*
