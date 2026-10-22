# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-10-22

First tagged release, packaged as a Claude Code plugin. The version restarts at 0.1.0: the
entries below it were internal milestones and were never tagged or published.

### Added
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`: install with
  `/plugin marketplace add arnaugonzalez/infographic-post-skill`, then
  `/plugin install infographic-post-skill@infographic-post-skill`, or with
  `npx skills add arnaugonzalez/infographic-post-skill`.
- README sections "Install" and "What it runs and sends": which API receives what, in each mode.
- The skill's Setup section checks the Python dependencies and asks before installing them.

### Changed
- The skill lives in `skills/infographic/` (`SKILL.md`, `scripts/`, `templates/`, `references/`,
  `requirements.txt`, `.env.example`), so it works when installed outside this repository.
  `SKILL.md` calls every script through `${CLAUDE_SKILL_DIR}` instead of a path relative to the
  current directory. `oss_audit.py` moved to `skills/infographic/scripts/`.
- `SKILL.md` no longer pre-approves tools (`allowed-tools`): Claude asks before running the
  scripts, as with any other command. Unused `dependencies` front matter removed.
- Example images moved to `docs/images/`.
- Tests run from any directory; they no longer depend on a local checkout path.

### Added (renderer and backends)
- User-selectable backend and model (`scripts/backends.py`, `scripts/doctor.py`, `scripts/prompts/`) supporting subscription CLIs (`claude`, `agy`, `codex`, `copilot`, `opencode`), in-session agent mode (`session`), and explicit API mode (`api`) via `--backend` / `--model` and `INFG_BACKEND` / `INFG_MODEL`.
- `scripts/claude_html_renderer.py` (`--backend`, `--model`, `--print-prompt`, `--finish`), `scripts/project_digest.py` (architecture-first codebase digest), and `benchmark/` (`bench.py`, `RESULTS.md`).

- Art direction for the HTML renderer (`scripts/design.py`, `scripts/prompts/archetypes.md`): five
  archetypes (`editorial`, `blueprint`, `terminal`, `swiss`, `brutalist`) chosen with `--style`, canvas
  formats with `--format` (`portrait` 1080×1350 by default, `square`, `landscape` 1280×640), and
  reference pages from `style/` or `--style-dir` / `INFG_STYLE_DIR` added to the prompt.
- `scripts/slop_lint.py`: `--finish` warns about generic AI-design patterns (gradients, glow,
  glassmorphism, card grids, emoji, purple palettes, generic fonts and subtitles), and after
  rendering it reports text that overlaps another block or leaves the canvas.
- Logos and monograms are drawn in the surrounding text color by default; `--brand-colors` restores
  brand colors.

### Changed (renderer and backends)
- The design brief (`scripts/prompts/brief.md`) is rewritten: the model writes its thesis, hero
  element, archetype and what it cut before drawing, keeps about twelve elements and avoids a banned
  list. It no longer asks for a "Stripe/Vercel/Linear" look or suggests Inter/Manrope.
- `--style modern-light|modern-dark|illustrated` map to `editorial|blueprint|swiss` in the HTML renderer.
- `auto` backend resolution prefers `session` (inside Claude Code) or the first installed subscription CLI and never selects a paid API or OpenRouter automatically.
- `--renderer auto` routes to `claude-html` via the resolved backend; `--renderer image` is used only when requested explicitly.
- Subscription CLIs run in an empty scratch directory, so they cannot edit the user's project. `agy`
  runs in `--print --output-format json` mode and the HTML is read from its `response` field.

### Removed
- Generated files from the repository root: `linkedin_posts.md`, `QUALITY_AUDIT.md`, a test
  image and an example about another project. They are now in `.gitignore`.

## Pre-release history

### 2.0.0 (internal) — 2026-03-27

#### Added
- **AI Image Generation** — Designer-quality infographics via Gemini image models (~$0.04/image)
- **5 infographic types**: architecture, comparison, feature, process, cheatsheet
- **3 visual styles**: modern-dark, modern-light, illustrated
- **Image prompt builder** (`image_prompt_builder.py`) — 70+ brand icon descriptions for designer-brief prompts
- **Content structurer** (`content_structurer.py`) — LLM returns structured JSON instead of HTML
- **Template renderer** (`template_renderer.py`) — Jinja2 HTML template with glassmorphism design
- **Icon registry** (`icon_registry.py`) — 3,414 brand SVG icons via simplepycons with fuzzy matching
- **Model quality tiers** (`model_quality.py`) — Classifies LLMs into tier 1/2/3 with CLI warnings
- **Graceful fallback**: AI image → HTML template → legacy HTML when APIs are unavailable
- New CLI flags: `--infographic-type`, `--style`, `--template`, `--legacy-html`
- New dependencies: `simplepycons>=1.0`, `jinja2>=3.1`

#### Changed
- Default rendering path changed from LLM-generated HTML to AI image generation
- Model tier lists updated to March 2026 (claude-sonnet-4.6, gpt-5.2, deepseek-v3.2, mimo-v2-pro)
- README completely rewritten with modes comparison, cost tables, and junior-friendly setup guide

#### Fixed
- `_strip_fences()` now strips LLM preamble text before code fences
- Image model routing when `INFG_IMAGE_MODEL` is a non-Gemini model (e.g. Flux)
- Gemini 500 errors now fall back gracefully to HTML template instead of crashing

### 1.1.0 (internal) — 2026-03-26

#### Added
- **Codebase reader** (`read_codebase.py`) — noise-filtered directory walk with token budget
- **LinkedIn post generator** (`generate_posts.py`) — dual-angle posts (technical + business)
- **Model-aware prompt registry** — per-family prompt strategies with staleness warnings
- **OSS quality audit** (`oss_audit.py`) — test coverage, docstrings, code quality report
- Codebase-to-infographic pipeline via `--codebase` flag

### 1.0.0 (internal) — 2026-03-25

#### Added
- Configurable LLM provider (OpenRouter + any model)
- OpenRouter HTTP adapter via `requests.post()`
- API key redaction for Google and OpenRouter keys
- `gemini-3.1-flash-image-preview` as default image model
- Matplotlib offline fallback (zero API keys)
- LinkedIn architecture diagram generator
- Interactive HTML chart generator (Chart.js)
- Version output manager
