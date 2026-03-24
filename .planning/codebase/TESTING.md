# Testing Patterns

**Analysis Date:** 2026-03-20

## Test Framework

**Runner:**
- Not detected in codebase
- No `pytest.ini`, `setup.cfg`, `pyproject.toml`, `tox.ini`, or test configuration found
- No `unittest` or `pytest` imports in source files

**Assertion Library:**
- Not applicable — no test framework detected

**Run Commands:**
- No test execution commands defined
- No test-related scripts in `scripts/` directory
- CI/CD pipeline for testing: Not detected (no `.github/workflows`, `.gitlab-ci.yml`, or similar)

## Test File Organization

**Location:**
- No test files detected in codebase
- Pattern would likely be: `tests/` directory (absent) or co-located with source files (none found)

**Naming:**
- No test files found with `test_*.py` or `*_test.py` patterns
- No `__tests__` directories
- No `spec` files

**Structure:**
- Test infrastructure: Not present

## Test Coverage

**Current State:**
- **No automated tests detected** in the codebase
- All validation appears manual or CLI-based
- Output validation: User visually inspects generated infographics or examines generated JSON

**Files with manual testing points:**
- `scripts/generate.py`: Contains `_demo()` function that generates a sample infographic
  - Invoked with `--demo` flag
  - Demonstrates all major features (headers, KPI rows, bar charts, donuts, callouts, process flows)
- `scripts/generate_linkedin_arch.py`: No built-in demo
- `scripts/parse_context.py`: No built-in demo (but supports `--text` and `--file` for inline testing)
- `scripts/generate_html.py`: No built-in demo
- `scripts/generate_pretty.py`: No built-in demo (requires credentials)

## Demo/Manual Testing

**Available Test Data:**
- `templates/example-config.json`: Example configuration for `generate_html.py`
  - Contains sample KPIs: revenue ($2.4M), NPS (72), churn rate (2.1%), new customers (340)
  - Includes multiple chart types: horizontalBar, donut, line
  - Demonstrates process flow steps

**Demo execution:**
```bash
# Generate a demo infographic showcasing all features
python scripts/generate.py --demo
# Output: demo_infographic.png (1080×1350px @ 150dpi)
```

**What the demo covers:**
- Header with title and subtitle
- KPI row with value, label, and delta indicators
- Horizontal bar chart with labels
- Donut chart with legend
- Callout/highlight box
- Process flow (5 numbered steps with arrows)
- Footer with branding

**Inline testing patterns:**
- `generate_linkedin_arch.py` supports `--layers` argument for quick inline testing:
  ```bash
  python scripts/generate_linkedin_arch.py \
    --layers "Frontend:React,Next.js|Backend:FastAPI" \
    --output test.png
  ```
- `parse_context.py` supports `--text` and `--file` arguments:
  ```bash
  python scripts/parse_context.py \
    --text "FastAPI backend, PostgreSQL, Redis" \
    --output arch.json
  ```

## Mocking

**Framework:** Not applicable — no tests exist

**Patterns:**
- No mocking infrastructure detected
- No mock objects, fixtures, or test doubles in source code

## Fixtures and Factories

**Test Data:**
- `templates/example-config.json`: Configuration example for HTML infographics
  ```json
  {
    "title": "Q3 Performance Report",
    "kpis": [
      { "value": "$2.4M", "label": "Revenue", "delta": "+18% YoY" }
    ],
    "charts": [...]
  }
  ```

**Location:**
- `/templates/example-config.json`
- Reference only; not loaded by tests

**Constants used for testing:**
- Color palettes defined in `PALETTES` dict: `"modern-blue"`, `"dark-professional"`, `"warm-report"`, `"accessible"`
- Component categories in `GROUP_STYLES`: Frontend, Mobile, Backend, Database, etc.
- Example dimensions: `LINKEDIN_W = 1080`, `LINKEDIN_H = 1080`
- Model pricing table: `_PRICING` in `generate_pretty.py` with known model costs

## Code Paths to Test (if tests were added)

**High-value test areas (not currently covered):**

### InfographicCanvas class (`scripts/generate.py`)
- Constructor with different DPI/dimensions/palettes
- Method chaining functionality
- Correct axes positioning for layered elements
- Color palette swapping
- Save functionality with path resolution

### Architecture parsing (`scripts/parse_context.py`)
- Component extraction from free-form text using regex patterns
- Category detection heuristics
- Layer grouping logic
- Connection inference between layers
- File scanning (project directories, package.json, etc.)
- Deduplication of components
- Garbage filtering (short words, file paths, pure numeric strings)

### LinkedIn diagram rendering (`scripts/generate_linkedin_arch.py`)
- Layout computation for different layer counts (1, 2, 4, 6, 9+ components)
- Group style lookup (fuzzy matching)
- Icon drawing functions for each category
- Arrow routing between boxes
- Title/footer rendering

### HTML generation (`scripts/generate_html.py`)
- Chart type rendering (bar, horizontalBar, donut, line, pie)
- KPI card formatting with delta indicators
- Process flow HTML generation
- Palette swapping in CSS injection

### AI-powered generation (`scripts/generate_pretty.py`)
- Backend routing logic (AI Studio vs Vertex AI)
- Credential detection and validation
- Model version detection (Gemini 2.5+ feature gates)
- Icon support detection
- Pricing calculation and cost breakdown
- Response parsing from different models (image vs HTML)
- Fallback handling for missing credentials

## Integration Points Worth Testing

**File I/O:**
- `Path.read_text()` with UTF-8 encoding and error handling
- `Path.write_text()` for output files
- Directory scanning with `.iterdir()`
- JSON file parsing and validation

**Data transformation:**
- JSON parsing from config files
- Component extraction from markdown text
- Layout calculation (grid positioning)
- Pricing calculation from model usage data

**External dependencies:**
- Matplotlib figure creation and axes management
- Matplotlib patch drawing (FancyBboxPatch, Circle, Ellipse, etc.)
- Matplotlib transformation and path effects
- Google Genai SDK (conditional, with graceful failure)
- Vertex AI client initialization

**Environment integration:**
- `.env` file parsing
- Environment variable detection (INFG_API_KEY, INFG_VERTEX_PROJECT)
- Google Cloud authentication (ADC — Application Default Credentials)
- Fallback logic when credentials missing

## Testing Notes

**Why no tests are present:**
- Codebase is primarily UI/visualization generation (hard to test without visual inspection)
- Output is graphics files (PNG) and HTML — validation requires image comparison or visual review
- Skills are designed for interactive use via Claude (manual testing appropriate)
- Critical paths (text extraction, category detection) are deterministic and have inline validation

**Recommended testing approach if tests were added:**
1. **Unit tests** for pure functions:
   - `extract_tech_from_text()`: regex pattern extraction
   - `detect_category()`: category heuristics
   - `group_into_layers()`: data grouping logic
   - `infer_connections()`: connection logic
   - `_gemini_version()`: version parsing
   - `_supports_icons()`: feature gate logic

2. **Integration tests** for file-based workflows:
   - Parse project structure → extract components → render layout
   - Load config.json → generate HTML → validate structure
   - Credential detection → backend selection → client initialization

3. **Visual regression tests** for rendering:
   - Generate known diagrams → compare against baseline images
   - Use tools like `pytest-image-compare` or manual diff

4. **CLI acceptance tests:**
   - Execute `generate.py --demo` → verify output file exists and has valid dimensions
   - Execute `parse_context.py --text "..."` → validate JSON schema of output
   - Execute `generate_linkedin_arch.py --layers "..."` → verify PNG output

5. **API/Model integration tests (with mocked Genai):**
   - Test backend routing logic without actual API calls
   - Verify pricing calculation accuracy
   - Test response parsing for different model outputs

## Validation Strategy (Current)

**Manual validation:**
- User runs `python scripts/generate.py --demo` and visually inspects output
- User reads generated JSON from `parse_context.py` and reviews component extraction
- User opens generated HTML in browser and interacts with charts
- User views PNG outputs at expected dimensions
- User tests `generate_pretty.py` with valid credentials and reviews generated infographics

**Automated checks (implicit):**
- File existence checked by shell scripts
- Path resolution uses `Path.resolve()` for debugging output
- JSON schema is validated by Python's `json` module at parse time
- Matplotlib raises exceptions if invalid dimensions/DPI provided
- Regex patterns match or don't match — validated during parsing
- Environment variable fallbacks provide sensible defaults

**Credential validation:**
- `_build_genai_client()` validates API key presence and backend configuration
- `_vertex_policy_warning()` performs inline credential check when Vertex AI configured
- Graceful error messages guide user to fix configuration

## Inline Quality Assurance

**Input validation:**
- Config file schema implicitly validated by `.get()` calls with sensible defaults
- Text input sanitized with `.strip()` and encoding error handling
- File paths resolved with `Path.resolve()` to catch invalid paths early

**Output validation:**
- Matplotlib figure dimensions validated before render
- Color hex values checked during palette lookup
- Category hints exhaustively mapped in `CATEGORY_HINTS` dictionary
- JSON output from `build_arch_json()` has predictable schema

---

*Testing analysis: 2026-03-20*
