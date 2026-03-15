# External Integrations

**Analysis Date:** 2026-03-15

## APIs & External Services

**None.**

This is a standalone infographic generation skill with no external API dependencies. All operations are file-based and local.

## Data Storage

**Databases:**
- None — skill is stateless and file-based

**File Storage:**
- Local filesystem only
  - Reads from: User-provided data files, `references/` design guides, `templates/` config examples
  - Writes to: User-specified output paths (PNG, SVG, HTML)
  - No persistent state or database

**Caching:**
- None — each invocation is independent

## Authentication & Identity

**Auth Provider:**
- None required
- Skill operates in sandbox environment with file I/O only

**Credentials:**
- No credentials, API keys, or authentication tokens needed

## Monitoring & Observability

**Error Tracking:**
- None — errors logged to stdout/stderr only

**Logs:**
- Console output during generation (print statements)
- Exit codes: 0 on success, 1 on error (argparse usage)

## CI/CD & Deployment

**Hosting:**
- Deployed as Claude Code skill (no separate deployment)

**CI Pipeline:**
- None — skill has no build pipeline or release process

## Environment Configuration

**Required env vars:**
- None — all configuration via CLI arguments or config JSON files

**Optional env vars:**
- `MPLBACKEND=Agg` — Recommended when running in headless/CI environments (forces matplotlib to use non-interactive backend)
- `MPLCONFIGDIR` — matplotlib config directory (defaults to `~/.config/matplotlib`)

**Secrets location:**
- No secrets used — skill requires no authentication

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Flow

### Typical Infographic Generation
1. User provides data (text, CSV, JSON) or references existing CLAUDE.md
2. Claude invokes `scripts/generate.py` or `scripts/generate_html.py` with config
3. Script reads matplotlib defaults and palette constants
4. Canvas is drawn in memory (no file I/O until final save)
5. Output written to user-specified path
6. Process exits with status

### LinkedIn Architecture Diagram Flow
1. User provides context (project root, CLAUDE.md, or inline text)
2. `scripts/parse_context.py` analyzes input and outputs `arch.json`
3. `scripts/generate_linkedin_arch.py` reads `arch.json`
4. Diagram rendered with matplotlib
5. PNG written to output path (1080×1080px @ 150dpi)

### HTML Interactive Output
1. User provides data config JSON
2. `scripts/generate_html.py` reads config
3. HTML template is filled with user data
4. Chart.js library linked via CDN (HTTPS)
5. Self-contained HTML written to output path

## Third-Party Dependencies (Build/Runtime)

**matplotlib:**
- Renders all vector graphics
- Uses system font rendering
- No network calls (local operation only)
- Backends: Agg (PNG/SVG default), TkAgg (interactive, if available)

**Chart.js (HTML output only):**
- Loaded from CDN: `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js`
- Inlined at build time to create self-contained HTML
- Browser requirement: ES6-compatible JavaScript engine

## No Network Dependencies

- No API calls during generation
- No license checks or version validation
- No telemetry or analytics
- No cloud service dependencies

## Offline Capability

**Fully offline:**
- PNG and SVG generation: 100% offline
- HTML generation: Offline if Chart.js is pre-downloaded; otherwise requires CDN access at view-time (not generation-time)

---

*Integration audit: 2026-03-15*
