# Coding Conventions

**Analysis Date:** 2026-03-15

## Naming Patterns

**Files:**
- Lowercase with underscores: `generate.py`, `generate_linkedin_arch.py`, `parse_context.py`
- Descriptive, action-oriented names indicating purpose
- Main execution scripts in `scripts/` directory

**Functions:**
- Lowercase with underscores (snake_case): `extract_components_from_text()`, `compute_layout()`, `group_into_layers()`
- Internal/private functions prefixed with underscore: `_text()`, `_wrap()`, `_demo()`, `_draw_frontend()`, `_draw_database()`
- Descriptive names indicating what the function does: `render_architecture()`, `layers_from_string()`

**Variables:**
- Lowercase with underscores: `canvas_w`, `canvas_h`, `layer_order`, `src_cat`
- Single letter acceptable for loop counters: `i`, `j`, `k` in tight loops
- Meaningful names for configuration dictionaries: `GROUP_STYLES`, `CATEGORY_HINTS`, `PALETTES`

**Types/Constants:**
- UPPERCASE for module-level constants: `LINKEDIN_W`, `LINKEDIN_DPI`, `TITLE_BG`, `DEFAULT_PALETTE`
- Dictionary keys use lowercase with underscores: `"primary"`, `"secondary"`, `"accent"`, `"bg"`, `"border"`
- Type hints used in function signatures: `path: str`, `dpi: int`, `layers: list[dict]`

## Code Style

**Formatting:**
- No enforced linting/formatting tool detected (no `.eslintrc`, `.prettierrc`, `pyproject.toml`, etc.)
- Manual formatting following implicit Python conventions
- Lines often exceed typical 80-char limit (many ~100+ characters)
- Indentation: 4 spaces

**Linting:**
- Not detected in codebase
- Code follows PEP 8 spirit informally

**Module organization:**
- Shebang line: `#!/usr/bin/env python3`
- Module docstring at top describing purpose and usage
- Imports organized: standard library first, then third-party
- Example: `scripts/generate.py` imports `argparse`, `textwrap` (stdlib) then matplotlib, numpy

**Python version:**
- Type hints using Python 3.10+ syntax: `str | None`, `list[dict]`, `list[tuple[str, str]]`
- F-strings for string formatting
- `.format()` also used in template strings (`HTML_TEMPLATE` in `generate_html.py`)

## Import Organization

**Order (observed pattern):**
1. Standard library: `argparse`, `json`, `os`, `re`, `sys`, `textwrap`, `pathlib.Path`
2. Third-party: `matplotlib.*`, `numpy`, `PIL/Pillow` (not directly used in reviewed files)

**Path Aliases:**
- No path aliases detected (no `@` imports, no `jsconfig.json` / `tsconfig.json`)
- Direct relative imports where needed, absolute imports with standard library

**Example from `scripts/generate.py`:**
```python
import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
```

## Error Handling

**Patterns:**
- Try-except blocks for file I/O: `try: ... except PermissionError: pass` in `parse_context.py`
- Error messages printed to stdout with emoji prefixes for user feedback:
  - `✅` for success: `print(f"✅ Infographic saved → {out.resolve()}")`
  - `❌` for errors: `print("❌  Provide either --config arch.json or --layers '...'")` followed by `raise SystemExit(1)`
- Assertions for invariant checking: `assert len(values) <= 5, "Use a bar chart for >5 categories"` in `generate.py`
- Encoding specified in file operations: `.read_text(encoding="utf-8", errors="ignore")`

**No defensive null checks:**
- Code assumes valid input from config files/CLI args
- Missing keys handled with `.get()` with defaults: `config.get("layers", [])`

## Logging

**Framework:** `print()` statements (standard output only)

**Patterns:**
- Status messages with emoji indicators
- Success: `print(f"✅ {filename} saved → {path}")`
- Info: `print(f"ℹ️  Import InfographicCanvas from this module...")`
- Error: `print("❌  Error message")` followed by exit
- Details printed on separate lines:
  ```python
  print(f"✅ Infographic saved → {out.resolve()}")
  print(f"   Size: {self.width_px}×{self.height_px}px @ {self.dpi}dpi")
  ```

**When to log:**
- File I/O completion (success/failure)
- Processing milestones in context parsing
- Configuration detection results
- No debug logging for function entry/exit

## Comments

**When to Comment:**
- Module-level docstrings present in all scripts describing purpose and usage patterns
- Inline comments used to separate logical sections: `# -----------` dividers
- Comments explain non-obvious design choices (e.g., why a specific color mapping)
- Complex mathematical calculations documented: "Compute layer grid coordinates"

**JSDoc/TSDoc:**
- Not applicable (Python codebase, not TypeScript)
- Function docstrings present in class methods:
  ```python
  def add_header(
      self,
      title: str,
      subtitle: str = "",
      source: str = "",
      accent_bar: bool = True,
  ) -> "InfographicCanvas":
      """Add a bold hero header section."""
  ```

**Section Headers:**
- Visual separators using comment lines: `# -----------` repeated 75 times
- Descriptive category labels:
  ```python
  # ---------------------------------------------------------------------------
  # Typography helpers
  # ---------------------------------------------------------------------------
  ```

## Function Design

**Size:** Functions typically 5-50 lines; drawing functions (`_draw_*`) 10-30 lines

**Parameters:**
- Positional args for core functionality
- Keyword args for optional styling: `color_override: str | None = None`
- Sensible defaults in class constructors: `dpi: int = 150`, `palette: str = DEFAULT_PALETTE`
- Multiple parameters use type hints and often exceed single line

**Return Values:**
- Matplotlib Axes objects returned from drawing operations
- Method chaining supported: `add_header().add_kpi_row().add_footer().save()`
- Dictionaries returned for structured data: `build_arch_json()` returns architecture config
- Path objects returned from save operations: `def save(self, path: str) -> Path:`

**Parameter validation:**
- Asserts for constraints: `assert len(values) <= 5`
- `.get()` with defaults for optional config values
- File existence checked with `.exists()`

## Module Design

**Exports:**
- Classes: `InfographicCanvas` in `generate.py`
- Functions for public use: `render_architecture()`, `generate_html()`, `build_arch_json()`
- Configuration constants exported: `PALETTES`, `GROUP_STYLES`, `CATEGORY_HINTS`
- Helper functions prefixed with `_` treated as private

**Barrel Files:**
- Not used (single-file modules)
- Each script is standalone with self-contained logic

**Organization pattern:**
1. Module docstring + usage examples
2. Constants and configuration
3. Helper functions (often prefixed with `_`)
4. Main classes or core logic functions
5. CLI argument parsing
6. `if __name__ == "__main__":` block for CLI execution

## Code Examples

**Type hints with unions:**
```python
def __init__(
    self,
    width_px: int = 1080,
    height_px: int = 1920,
    dpi: int = 150,
    palette: str = DEFAULT_PALETTE,
    bg_color: str | None = None,
):
```

**Dictionary configuration pattern:**
```python
PALETTES = {
    "modern-blue": {
        "primary":    "#1A73E8",
        "secondary":  "#0D47A1",
        "accent":     "#FF6D00",
        "neutral":    "#5F6368",
        "light":      "#E8F0FE",
        "background": "#FFFFFF",
        "text":       "#202124",
    },
}
```

**Method chaining:**
```python
canvas = InfographicCanvas(1080, 1920, dpi=150, palette="modern-blue")
canvas.add_header("Title", subtitle="Subtitle")
       .add_kpi_row(kpis=[...])
       .add_bar_chart(labels=[...], values=[...])
       .save("out.png")
```

**Private helper function pattern:**
```python
def _wrap(text: str, width: int = 12) -> str:
    return "\n".join(textwrap.wrap(text, width))
```

---

*Convention analysis: 2026-03-15*
