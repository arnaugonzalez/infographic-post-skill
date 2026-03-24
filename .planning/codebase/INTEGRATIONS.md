# External Integrations

**Analysis Date:** 2026-03-20

## APIs & External Services

**Google Gemini (Optional - Pretty Mode):**
- Service: Multimodal AI for enhanced/AI-generated infographic creation
- SDK/Client: `google-genai` package (pip install google-genai)
- Auth methods:
  - AI Studio: INFG_API_KEY environment variable (fallback)
  - Vertex AI: Application Default Credentials (ADC) via GCP + INFG_VERTEX_PROJECT + INFG_VERTEX_LOCATION
- Usage: `scripts/generate_pretty.py` (lines 87-123 for client routing, 135-150 for credential detection)
- Models supported (Feb 2026):
  - `gemini-3.1-flash-image-preview` (default, AI Studio only)
  - `gemini-2.5-flash-image` (Vertex AI, native PNG)
  - `gemini-2.5-pro` (Vertex AI, best quality)
  - `gemini-2.0-flash` (Vertex AI, fast/cheap)
  - `gemini-2.0-flash-lite` (Vertex AI, cheapest)
- Cost: Usage-based; cost breakdown printed to stdout after generation

**Google Cloud Vertex AI (Optional - AI Routing):**
- Service: GCP-hosted Gemini models for cost optimization
- Project ID: INFG_VERTEX_PROJECT environment variable
- Location: INFG_VERTEX_LOCATION (defaults to us-central1)
- Auth: Application Default Credentials (ADC) via `google-auth` package
- Usage: Auto-routing in `scripts/generate_pretty.py` lines 96-132 (`_build_genai_client()`)
- Fallback: Automatically routes to AI Studio if Vertex AI not configured

## Data Storage

**Databases:**
- None — skill is stateless generation engine

**File Storage:**
- Local filesystem only
  - Reads from: User-provided data files, `references/` design guides, `templates/` config examples, project `CLAUDE.md`
  - Writes to: User-specified output paths (PNG, SVG, HTML, JSON)
  - No persistent state or database

**Caching:**
- None — each invocation is independent

## Authentication & Identity

**Auth Provider:**
- Optional: Google OAuth 2.0 (for Vertex AI via ADC)
- Optional: API Keys (for Google AI Studio)

**When Not Required:**
- All core generation functions (matplotlib-based PNG/SVG, Chart.js HTML) work offline with no auth
- Auth only needed for `scripts/generate_pretty.py` when using Gemini models

**Credentials Flow (generate_pretty.py):**
1. Check INFG_API_KEY for AI Studio-only models → use AI Studio
2. Check INFG_VERTEX_PROJECT → use Vertex AI with ADC
3. Fallback to INFG_API_KEY → use AI Studio
4. Exit with helpful error if none configured

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- Console output via print statements
- Cost breakdown printed by `generate_pretty.py` after generation
- Credential warnings via `_vertex_policy_warning()` (lines 135-150)

## CI/CD & Deployment

**Hosting:**
- Deployed as Claude Code skill (no separate hosting)

**CI Pipeline:**
- None — skill has no build pipeline or release process

## Environment Configuration

**Required env vars:**
- None — all configuration via CLI arguments or config JSON files

**Optional env vars (for pretty mode only):**
- `INFG_API_KEY` - Google AI Studio API key (string)
- `INFG_VERTEX_PROJECT` - GCP project ID for Vertex AI (string)
- `INFG_VERTEX_LOCATION` - GCP region (string, defaults to us-central1)
- `MPLBACKEND=Agg` - Recommended for headless/CI environments (matplotlib non-interactive backend)
- `MPLCONFIGDIR` - matplotlib config directory (defaults to ~/.config/matplotlib)

**Secrets location:**
- `.env` file in project root: `_SKILL_DIR / ".env"` (see `scripts/generate_pretty.py` line 54)
- Loaded via custom `_load_dotenv()` (lines 57-68)
- Environment variables override .env file values
- Format: `KEY=value` (quotes stripped by parser)

## Webhooks & Callbacks

**Incoming:**
- None — skill is invoked synchronously via Claude

**Outgoing:**
- None — all outputs written to local filesystem or printed to stdout

## Data Flow

### Core Infographic Generation (No API calls)
1. User invokes `scripts/generate.py` with layout, data, output path
2. InfographicCanvas class reads palette and typography
3. Matplotlib renders directly to memory (PNG/SVG)
4. Output written to local filesystem
5. Exit status returned to caller

### LinkedIn Architecture Diagram Flow
1. `scripts/parse_context.py` analyzes CLAUDE.md or project structure (local files)
2. Outputs `arch.json` with layer/component metadata (local file)
3. `scripts/generate_linkedin_arch.py` reads `arch.json`
4. Matplotlib renders diagram (no API calls)
5. PNG written to output path (1080×1080px @ 150dpi)

### HTML Interactive Output (Local generation, CDN at view-time)
1. User provides data config JSON
2. `scripts/generate_html.py` reads config (local file)
3. HTML template filled with user data
4. Chart.js linked via CDN URL: `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js`
5. Self-contained HTML written to output path
6. **Note:** Chart.js library is fetched by browser at view-time, not generation-time

### AI-Generated Infographic (Pretty Mode - API calls)
1. User provides config or data
2. `scripts/generate_pretty.py` reads input (local files)
3. Routes to Vertex AI or AI Studio based on env vars
4. Sends generation request to Gemini API
5. Receives PNG or HTML from API
6. Writes output to local filesystem
7. Prints cost breakdown and API usage

## Third-Party Runtime Dependencies

**matplotlib:**
- Renders all vector graphics
- Uses system font rendering
- No network calls during PNG/SVG generation (local operation only)
- Backends: Agg (PNG/SVG default), TkAgg (interactive, if available)

**Chart.js (HTML mode only):**
- Loaded from CDN during HTML view, not generation
- CDN URL: `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js`
- Browser requirement: ES6-compatible JavaScript engine
- Fallback: Works offline if Chart.js is cached

**google-genai (optional, pretty mode only):**
- Makes HTTPS requests to Google Gemini API
- Requires internet connectivity when using pretty mode
- Handles image upload and generation polling
- See: `scripts/generate_pretty.py` lines 150+ for model inference

## Offline Capability

**Fully offline (core generation):**
- PNG and SVG generation: 100% offline
- Architecture diagram generation: 100% offline
- Context parsing: 100% offline

**Partially offline (HTML generation):**
- HTML file generation: 100% offline
- Chart.js library: Offline if cached in browser, otherwise CDN fetch at view-time

**Online required:**
- Pretty mode (Gemini): Requires active internet and valid API credentials
- CDN resources: Only required if viewing generated HTML in browser

---

*Integration audit: 2026-03-20*
