# Contributing

Thanks for your interest in contributing! Here's how to get started.

## Setup for development

```bash
# 1. Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/infographic-skill.git
cd infographic-skill

# 2. Install all dependencies (including optional ones for testing)
pip install -r requirements.txt
pip install -r requirements-audit.txt  # coverage, flake8
pip install google-genai playwright    # optional, for AI mode testing
playwright install chromium            # for HTML→PNG screenshots

# 3. Copy the env template
cp .env.example .env
# Add your API keys if you want to test AI image generation

# 4. Run the tests
python -m pytest
# Should see 303+ tests passing
```

## Running tests

```bash
# All tests
python -m pytest

# Specific module
python -m pytest tests/test_icon_registry.py

# With verbose output
python -m pytest -v --tb=short
```

## Code style

- Python 3.9+ with `from __future__ import annotations`
- No linter enforced yet — just keep it clean and consistent
- Use type hints where practical
- Docstrings for public functions

## How the pipeline works

```
Codebase → read_codebase.py → CodebaseReport (JSON)
  ↓
content_structurer.py → Structured JSON (layers, connections, title)
  ↓
Two rendering paths:
  Path A: image_prompt_builder.py → Gemini image model → PNG (best quality)
  Path B: template_renderer.py → Jinja2 HTML → Playwright screenshot → PNG (free)
```

## Adding a new infographic type

1. Add the type to `INFOGRAPHIC_TYPES` in `scripts/image_prompt_builder.py`
2. Create a `_build_{type}_prompt()` function with the prompt template
3. Register it in `_BUILDERS` dict
4. Add the choice to `--infographic-type` in `generate_pretty.py` argparse
5. Add tests in `tests/test_image_prompt_builder.py`

## Adding a new brand icon

Icons are resolved automatically from [Simple Icons](https://simpleicons.org/) via the `simplepycons` package (3,414 brands).

If a technology name doesn't resolve correctly, add an alias in `_ALIAS_MAP` in `scripts/icon_registry.py`:

```python
_ALIAS_MAP = {
    "your tech name": "simplepycons_slug",
    # e.g. "Next.js" → "nextdotjs"
}
```

## Pull request checklist

- [ ] Tests pass (`python -m pytest`)
- [ ] No secrets or API keys in code
- [ ] New features have tests
- [ ] README updated if user-facing behavior changes
