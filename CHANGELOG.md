# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] — 2026-03-27

### Added
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

### Changed
- Default rendering path changed from LLM-generated HTML to AI image generation
- Model tier lists updated to March 2026 (claude-sonnet-4.6, gpt-5.2, deepseek-v3.2, mimo-v2-pro)
- README completely rewritten with modes comparison, cost tables, and junior-friendly setup guide

### Fixed
- `_strip_fences()` now strips LLM preamble text before code fences
- Image model routing when `INFG_IMAGE_MODEL` is a non-Gemini model (e.g. Flux)
- Gemini 500 errors now fall back gracefully to HTML template instead of crashing

## [1.1.0] — 2026-03-26

### Added
- **Codebase reader** (`read_codebase.py`) — noise-filtered directory walk with token budget
- **LinkedIn post generator** (`generate_posts.py`) — dual-angle posts (technical + business)
- **Model-aware prompt registry** — per-family prompt strategies with staleness warnings
- **OSS quality audit** (`oss_audit.py`) — test coverage, docstrings, code quality report
- Codebase-to-infographic pipeline via `--codebase` flag

## [1.0.0] — 2026-03-25

### Added
- Configurable LLM provider (OpenRouter + any model)
- OpenRouter HTTP adapter via `requests.post()`
- API key redaction for Google and OpenRouter keys
- `gemini-3.1-flash-image-preview` as default image model
- Matplotlib offline fallback (zero API keys)
- LinkedIn architecture diagram generator
- Interactive HTML chart generator (Chart.js)
- Version output manager
