# Technology Stack

**Analysis Date:** 2026-03-20

## Languages

**Primary:**
- Python 3.8+ - Core generation engine and scripting (`scripts/generate.py`, `scripts/parse_context.py`, `scripts/generate_html.py`, `scripts/generate_linkedin_arch.py`, `scripts/generate_pretty.py`)

**Supporting:**
- JSON - Configuration and data serialization
- Markdown - Documentation and design references
- HTML/CSS/JavaScript - Interactive chart templates (Chart.js)

## Runtime

**Environment:**
- Python 3.8 or later (tested with Python 3.12.3; no specific version constraint; compatible with modern Python 3.x)

**Package Manager:**
- pip
- Lockfile: Not present (uses direct requirements specification in SKILL.md frontmatter)

## Frameworks

**Core Graphics:**
- matplotlib 3.7+ - High-DPI canvas rendering, primitive drawing, font rasterization, DPI-aware figure sizing
- Pillow (PIL) 10.0+ - Image manipulation, format conversion, post-processing

**Data/Utilities:**
- numpy 1.24+ - Numerical operations, array manipulation for coordinate transforms

**Interactive Visualizations:**
- Chart.js 4.4.1 - Interactive HTML charts (via CDN in generated HTML; see `scripts/generate_html.py`)

**Optional AI Integration:**
- google-genai - Google Gemini API client for "pretty mode" generation (optional; see `scripts/generate_pretty.py`)

## Key Dependencies

**Critical:**
- matplotlib 3.10+ (installed) - Rendering engine for all PNG/vector outputs; provides DPI awareness, typography system, patch-based drawing primitives. Core to `generate.py` and `generate_linkedin_arch.py`.
- Pillow 10.2+ (installed) - Image I/O and format support
- numpy 2.4+ (installed) - Coordinate math and data array operations

**Build/Execution:**
- argparse - CLI argument parsing (stdlib)
- json - Configuration parsing (stdlib)
- pathlib - Cross-platform file operations (stdlib)
- textwrap - Text wrapping for labels (stdlib)
- re - Regular expression parsing (stdlib, used in `parse_context.py`)

**Browser/Interactive:**
- Chart.js 4.4.1 - Inlined in HTML templates for interactive visualizations (via CDN)

**Optional (Pretty Mode):**
- google-genai - Google Gemini API client (optional). Used only by `scripts/generate_pretty.py` for vision-based infographic generation. Install with: `pip install google-genai`. Requires either INFG_API_KEY (Google AI Studio) or GCP credentials for Vertex AI.

## Configuration

**Environment:**
- CLI arguments: All scripts support `--output`, `--width`, `--height`, `--dpi`, `--palette`, etc.
- Config files: JSON (e.g., `arch.json` from `parse_context.py`)
- Design references: `references/design-principles.md` and `references/chart-selection.md` (human-readable guides, not code config)
- Example config: `templates/example-config.json`

**Build:**
- No build configuration files (.eslintrc, tsconfig.json, etc.) — Python scripts run directly via `python scripts/{name}.py`
- Entry points:
  - `scripts/generate.py` — Core infographic rendering
  - `scripts/generate_linkedin_arch.py` — LinkedIn architecture diagram generation
  - `scripts/generate_html.py` — Interactive HTML with Chart.js
  - `scripts/parse_context.py` — Extract architecture from CLAUDE.md and project structure
  - `scripts/generate_pretty.py` — AI-powered generation via Gemini

**Optional Secrets (.env):**
- `.env` file in project root (loaded by `scripts/generate_pretty.py` lines 51-68)
- Variables: INFG_API_KEY, INFG_VERTEX_PROJECT, INFG_VERTEX_LOCATION
- Not required for core matplotlib-based generation

## Platform Requirements

**Development:**
- Python 3.8+
- pip
- (Optional) Google Cloud SDK or Google AI Studio API key for pretty mode testing

**Production:**
- Python 3.8+ runtime
- matplotlib backends support (if running in headless/CI environment, use Agg backend: set `MPLBACKEND=Agg`)
- ~50MB disk space for generated PNG/HTML artifacts
- (Optional) GCP credentials or API key for pretty mode

**Output Targets:**
- PNG (high-DPI, 150-300dpi configurable)
- SVG (vector, resolution-independent)
- HTML (self-contained with Chart.js)

## Dependency Matrix

| Package | Version | Purpose | License | Required |
|---------|---------|---------|---------|----------|
| matplotlib | ≥3.7 | Vector graphics, text rendering, DPI-aware layouts | BSD-3-Clause | Yes |
| Pillow | ≥10.0 | Image I/O, format conversion | HPND | Yes |
| numpy | ≥1.24 | Array operations, coordinate math | BSD | Yes |
| Chart.js | 4.4.1 | Interactive HTML charts (CDN) | MIT | Optional (HTML only) |
| google-genai | latest | Gemini API client for pretty mode | Apache 2.0 | Optional (pretty mode only) |

---

*Stack analysis: 2026-03-20*
