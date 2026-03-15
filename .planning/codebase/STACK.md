# Technology Stack

**Analysis Date:** 2026-03-15

## Languages

**Primary:**
- Python 3.8+ - Core generation engine and scripting

**Supporting:**
- JSON - Configuration and data serialization
- Markdown - Documentation and design references
- Shell/Bash - Build and execution scripts

## Runtime

**Environment:**
- Python 3.8 or later (no specific version constraint; compatible with modern Python 3.x)

**Package Manager:**
- pip
- Lockfile: Not present (uses direct requirements specification in SKILL.md)

## Frameworks

**Core:**
- matplotlib 3.7+ - High-DPI canvas rendering, primitive drawing, font rasterization, DPI-aware figure sizing
- Pillow (PIL) 10.0+ - Image manipulation, format conversion, post-processing

**Data/Utilities:**
- numpy 1.24+ - Numerical operations, array manipulation for coordinate transforms

**Visualization:**
- Chart.js 4.4.1+ - Interactive HTML charts (via CDN in generated HTML; see `generate_html.py`)

## Key Dependencies

**Critical:**
- matplotlib - Rendering engine for all PNG/vector outputs; provides DPI awareness, typography system, patch-based drawing primitives
- Pillow - Image I/O and format support
- numpy - Coordinate math and data array operations

**Build/Execution:**
- argparse - CLI argument parsing (stdlib)
- json - Configuration parsing (stdlib)
- pathlib - Cross-platform file operations (stdlib)
- textwrap - Text wrapping for labels (stdlib)

**Browser/Interactive:**
- Chart.js 4.4.1 - Inlined in HTML templates for interactive visualizations

## Configuration

**Environment:**
- Configured via command-line arguments (no .env file needed)
- Design references: `references/design-principles.md` and `references/chart-selection.md` (human-readable guides, not code config)
- Example config: `templates/example-config.json`

**Build:**
- No build configuration files (.eslintrc, tsconfig.json, etc.) — Python scripts run directly
- Entry points: `scripts/generate.py`, `scripts/generate_linkedin_arch.py`, `scripts/generate_html.py`, `scripts/parse_context.py`

## Platform Requirements

**Development:**
- Python 3.8+
- pip
- Access to script execution (no external API keys or secrets needed for basic operation)

**Production:**
- Python 3.8+ runtime
- matplotlib backends support (if running in headless/CI environment, use Agg backend: set `MPLBACKEND=Agg`)
- ~50MB disk space for generated PNG/HTML artifacts

**Output Targets:**
- PNG (high-DPI, 150-300dpi configurable)
- SVG (vector, resolution-independent)
- HTML (self-contained with CDN-inlined Chart.js)

## External Dependencies Matrix

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| matplotlib | ≥3.7 | Vector graphics, text rendering, DPI-aware layouts | BSD-3-Clause |
| Pillow | ≥10.0 | Image I/O, format conversion | HPND |
| numpy | ≥1.24 | Array operations, coordinate math | BSD |
| Chart.js | 4.4.1 | Interactive HTML charts (CDN) | MIT |

## No External Integrations Required

This is a **standalone skill** — no:
- API keys or authentication
- Database connections
- Cloud service dependencies
- Third-party SaaS integrations

All operations are file-based and self-contained.

---

*Stack analysis: 2026-03-15*
