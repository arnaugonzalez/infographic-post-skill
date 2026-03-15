# Codebase Concerns

**Analysis Date:** 2026-03-15

## File I/O Error Handling

**Missing exception handling for JSON parsing:**
- Issue: `generate_html.py` and `generate_linkedin_arch.py` use `json.load()` and `open()` with no error handling. If config files are malformed or missing, the entire script crashes without user-friendly errors.
- Files: `scripts/generate_html.py:386-387`, `scripts/generate_linkedin_arch.py:804-805`
- Impact: Users cannot recover from invalid JSON configs or missing files. Silent failures possible.
- Fix approach: Wrap JSON operations in try-except blocks with specific error messages. Validate JSON schema before processing. Add pre-flight checks for file existence.

**Silent failure on file write:**
- Issue: No error handling when writing output files. If disk is full, permissions denied, or path invalid, the process silently fails or partially writes files.
- Files: `scripts/generate.py:375-379`, `scripts/generate_html.py:374-375`, `scripts/generate_linkedin_arch.py:739-744`
- Impact: Corrupted output files, loss of work, confusing error messages from matplotlib.
- Fix approach: Wrap all `savefig()` and `write_text()` calls in try-except. Validate output path writability before rendering. Check available disk space.

**Unsafe file read with silently ignored errors:**
- Issue: `parse_context.py:195` uses `errors="ignore"` on all file reads. This silently discards malformed UTF-8, potentially losing architecture information from source files.
- Files: `scripts/parse_context.py:195, 189, 351`
- Impact: Architecture diagrams may be incomplete or inaccurate if source files contain encoding issues.
- Fix approach: Use `errors="replace"` instead to preserve indication of broken encoding. Warn user about encoding issues. Provide fallback encoding detection.

---

## Input Validation & Bounds

**No validation of canvas dimensions:**
- Issue: Canvas width/height are passed directly from CLI args without bounds checking. Extremely large values could cause memory exhaustion. Negative or zero values cause undefined behavior.
- Files: `scripts/generate.py:430-440`, `scripts/generate_linkedin_arch.py:792-800`
- Impact: Resource exhaustion, crash, or silent failures. No meaningful error message.
- Fix approach: Validate canvas dimensions (e.g., 100px - 10000px range). Set reasonable defaults. Warn if unusual values detected.

**Assertion instead of validation:**
- Issue: `generate.py:260` uses `assert len(values) <= 5` to enforce constraint. Assertions can be disabled with Python `-O` flag, making the constraint optional at runtime.
- Files: `scripts/generate.py:260`
- Impact: Feature silently broken if run with optimization flags. No graceful error message.
- Fix approach: Replace with proper validation raising ValueError with descriptive message.

**No bounds on KPI row and chart data:**
- Issue: `add_kpi_row()`, `add_bar_chart()`, `add_donut()` accept arbitrary list lengths without validation. 100+ items would break layout calculations and produce garbled output.
- Files: `scripts/generate.py:164-200, 206-244, 250-288`
- Impact: Silently produces broken/unreadable infographics when given large datasets.
- Fix approach: Validate input array lengths. Add `max_items` parameter. Document limits clearly.

---

## Regex Complexity & Performance

**Expensive regex patterns on large files:**
- Issue: `parse_context.py:107-122` defines multiple overlapping regex patterns that are applied sequentially to entire file contents (potentially megabytes). No caching or early-exit optimization.
- Files: `scripts/parse_context.py:101-137`
- Impact: Slow architecture parsing on large projects. Potential for cascading regex timeouts on pathological input.
- Fix approach: Compile regexes once at module load. Add timeout to re.finditer. Implement early exit if sufficient components found. Profile on real projects.

**Substring redundancy detection is quadratic:**
- Issue: `parse_context.py:309-313` compares every component name against every other for substring overlap. O(n²) complexity.
- Files: `scripts/parse_context.py:301-317`
- Impact: Scales poorly with >100 detected components (realistic in large projects). CPU spike during parsing.
- Fix approach: Use trie or set-based approach for deduplication. Sort by name length first to reduce comparisons.

---

## Matplotlib Resource Leaks

**Potential figure memory retention:**
- Issue: `generate_linkedin_arch.py:572` and `generate.py:108` create matplotlib figures. `plt.close(fig)` is called in some paths but `subplots()` may not be fully cleaned in error cases.
- Files: `scripts/generate.py:375-379`, `scripts/generate_linkedin_arch.py:560-748`
- Impact: Long-running processes (e.g., generating 100+ images in loop) may accumulate figure memory. Potential OOM on servers.
- Fix approach: Use context managers for figure creation. Always close figures in finally blocks. Use `matplotlib.use('Agg')` explicitly for non-interactive backend.

**No DPI validation:**
- Issue: DPI values from CLI args are not validated. Extremely high DPI values (>1000) combined with large canvas cause enormous memory allocation.
- Files: `scripts/generate.py:430-437`, `scripts/generate_linkedin_arch.py:36-38`
- Impact: Memory exhaustion, OOM crashes, extremely slow rendering.
- Fix approach: Clamp DPI to reasonable range (72-600). Warn if unusual values used.

---

## Layout Edge Cases

**Icon drawing assumes sufficient space:**
- Issue: `generate_linkedin_arch.py:138-202, 525-553` draws icons and text without checking if the container box has minimum size. Very small boxes produce overlapping, garbled output.
- Files: `scripts/generate_linkedin_arch.py:630-680`
- Impact: Unreadable diagrams with many component groups (>9 layers). No graceful degradation.
- Fix approach: Validate minimum box dimensions. Use collapsible sections or paginated layout for >9 groups. Add scaling logic.

**Component chip layout crashes on empty items:**
- Issue: `generate_linkedin_arch.py:671` iterates over items with hardcoded slice `items[:chip_cols * chip_rows]`. If items list is empty, no warning or special handling.
- Files: `scripts/generate_linkedin_arch.py:647-677`
- Impact: Layers with zero components produce empty boxes (confusing visually, breaks expected layout).
- Fix approach: Skip rendering empty layers. Warn user. Validate items list before layout.

**Process flow arrows overlap on single-step:**
- Issue: `generate.py:348-353` unconditionally draws arrows between steps. With 1 step, no arrow should appear but code has `if i < n - 1` check that works but produces nothing.
- Files: `scripts/generate.py:317-354`
- Impact: Minor visual inconsistency with single-step flows. Low severity.
- Fix approach: Already correct in code. Document expected behavior for edge case (1 step = no arrows).

---

## Heuristic Brittleness

**Component detection relies on name matching:**
- Issue: `parse_context.py:28-53, 92-98` categorizes components by substring matching on name. "React" detects Frontend but "React Query" (data library) might be mis-categorized as Frontend when it's backend. Same for "Apollo" (GraphQL client vs server).
- Files: `scripts/parse_context.py:92-98`
- Impact: Incorrect architecture diagrams. Misleading layer groupings. Users see wrong categories without easy recourse.
- Fix approach: Add user-facing correction mechanism (JSON config override). Expand heuristic rules with context (e.g., "React" in backend dir = backend). Document assumption.

**Directory scanning misses non-standard layouts:**
- Issue: `parse_context.py:140-181` scans top-level directories. Projects with flat structure (all in `src/`) or monorepo-style (services/api, services/web) are not detected correctly.
- Files: `scripts/parse_context.py:140-181`
- Impact: Incomplete architecture diagrams. Missing technologies not in top-level dirs.
- Fix approach: Add recursive scanning with depth limit. Allow custom component hints via config. Check `package.json`/`pyproject.toml` for dependency-based detection.

**CLAUDE.md parsing fragile:**
- Issue: `parse_context.py:184-190` scans for CLAUDE.md in multiple locations but with hard-coded file names. User-created variations (claude.MD, .claude.md) not found.
- Files: `scripts/parse_context.py:184-190`
- Impact: Missing critical architecture info if file name doesn't match exactly.
- Fix approach: Use case-insensitive matching. Check `.gitignore` for alternate names. Allow env var override for config file path.

---

## Type Safety & Data Validation

**Untyped configuration dictionaries:**
- Issue: `generate_html.py:342`, `generate_linkedin_arch.py:560` accept `config: dict` with no validation of required keys. Missing keys cause KeyError crashes.
- Files: `scripts/generate_html.py:342-377`, `scripts/generate_linkedin_arch.py:560-748`
- Impact: Poor error messages. Crashes on invalid config instead of helpful validation error.
- Fix approach: Use TypedDict or dataclass for config schema. Validate required keys on entry. Provide detailed schema documentation.

**Color strings not validated:**
- Issue: Hex color strings in config are used directly in matplotlib without validation. Invalid colors (wrong format, non-existent names) cause cryptic matplotlib errors.
- Files: Entire color system in `scripts/generate.py`, `generate_linkedin_arch.py`
- Impact: Confusing errors. Hard to debug color issues in custom palettes.
- Fix approach: Add color validation function. Support multiple formats (hex, rgb, named). Provide helpful error on invalid colors.

---

## Documentation & Specification

**Palette color format undocumented:**
- Issue: SKILL.md and code comments don't document the exact format for custom color palettes. Users trying to create custom palettes have no spec.
- Files: `scripts/generate.py:29-66`, `generate_linkedin_arch.py:49-64`
- Impact: No way to safely extend palettes. Users must reverse-engineer format from code.
- Fix approach: Document palette format in SKILL.md. Provide JSON schema example. Add validation with clear error messages.

**Layer grouping rules not documented:**
- Issue: Architecture diagram layer ordering and grouping rules are implicit in `parse_context.py:204-211, 214-235` but not explained anywhere.
- Files: `scripts/parse_context.py:204-235`
- Impact: Users cannot predict or customize layer ordering. Surprising results from parse_context.py output.
- Fix approach: Document LAYER_ORDER in SKILL.md. Explain grouping strategy. Allow order customization in config.

---

## Missing Boundary Checks

**String wrapping assumes minimum width:**
- Issue: `generate.py:120`, `generate_linkedin_arch.py:81-82` use `textwrap.wrap()` with fixed width. Very narrow text containers wrap to unreadable single characters.
- Files: `scripts/generate.py:116-123`, `scripts/generate_linkedin_arch.py:81-82, 195`
- Impact: Unreadable text in small containers. No fallback.
- Fix approach: Validate minimum text container width. Use dynamic wrapping width based on container size. Fall back to truncation if text too long.

**Axis limits not validated:**
- Issue: `generate.py:221-232` computes axis limits dynamically from data. If all data points are zero or identical, axis calculations produce degenerate ranges (0-0).
- Files: `scripts/generate.py:206-244`
- Impact: Bar chart with all zero values produces broken visualization.
- Fix approach: Add minimum range padding. Detect zero/identical data and provide sensible defaults.

---

## Testing & Quality Assurance

**No test coverage:**
- Issue: Project has no tests. All verification is manual or assumed to work.
- Files: No test directory exists
- Impact: Regressions undetected. Refactoring risky. Edge cases untested.
- Fix approach: Add pytest suite. Create fixtures for common data patterns. Test all CLI entry points. Test error paths.

**No example configs or test data:**
- Issue: Users must write configs from scratch with no reference examples besides inline demo.
- Files: `templates/example-config.json` exists but may be outdated or incomplete
- Impact: High friction for new users. Errors in user configs go undetected.
- Fix approach: Create comprehensive example configs. Add validation against JSON schema. Include test data for all layout types.

---

## Performance Concerns

**No progress indication for slow operations:**
- Issue: Parsing large CLAUDE.md files (10,000+ lines) or rendering high-DPI images gives no feedback. User unsure if process is stuck.
- Files: All scripts lack logging or progress bars
- Impact: Poor user experience. Appear to hang.
- Fix approach: Add verbose logging. Use tqdm for progress. Log processing steps.

**Regex compilation at runtime:**
- Issue: Regexes in `parse_context.py:107-122` are compiled on every call to `extract_components_from_text()`. Should be module-level constants.
- Files: `scripts/parse_context.py:101-137`
- Impact: Unnecessary recompilation. Slower parsing of large files.
- Fix approach: Compile all regexes once at module import. Store in module constants.

---

## Security Considerations

**Path traversal via output path:**
- Issue: Output file paths from CLI args are passed directly to `Path()` without validation. User could specify `../../sensitive.png` to write outside intended directory.
- Files: `scripts/generate.py:375-376`, `generate_html.py:374-375`, `generate_linkedin_arch.py:739`
- Impact: Low risk in local use. Higher risk if exposed as API. Could overwrite arbitrary files.
- Fix approach: Validate output paths. Restrict to safe directory. Use `Path.resolve()` and check against allowed base paths.

**Unescaped text in HTML output:**
- Issue: `generate_html.py:369` directly embeds user-provided config JSON in HTML without escaping. If config contains HTML/JS, could cause injection.
- Files: `scripts/generate_html.py:365-371`
- Impact: XSS risk if HTML shared or embedded in untrusted context.
- Fix approach: Use proper JSON encoding. Escape all user-provided text. Use templating engine with auto-escaping.

**Command injection via CLAUDE.md paths:**
- Issue: While not exploited here, if any future features shell-exec file paths from CLAUDE.md, arbitrary code execution risk exists.
- Files: `scripts/parse_context.py:186`
- Impact: Low current risk. Architectural vulnerability for future.
- Fix approach: Document security assumptions. Never exec file paths. Use pathlib exclusively. Validate all external input.

---

## Dependencies & Configuration

**No explicit Python version requirement:**
- Issue: `SKILL.md` specifies `python: ">=3.8"` but code uses Python 3.10+ features (e.g., `str | None` type union syntax in `generate.py:95`).
- Files: `SKILL.md:17`, `scripts/generate.py:95`
- Impact: Fails on Python 3.8/3.9. No clear error message about version incompatibility.
- Fix approach: Update version requirement to `>=3.10`. Use `from __future__ import annotations` for compatibility. Test on minimum version.

**Missing or implicit dependency versions:**
- Issue: SKILL.md specifies pip dependencies but no version pins. `matplotlib>=3.7`, `Pillow>=10.0` could change behavior between patch versions.
- Files: `SKILL.md:19-21`
- Impact: Non-reproducible renders across runs. Matplotlib API changes break code. Security updates introduce bugs.
- Fix approach: Create `requirements.txt` with pinned versions. Test against minimum versions. Use `pip-tools` for lock file.

---

## Known Bugs & Unexpected Behavior

**Hard-coded DPI mismatch:**
- Issue: `generate_linkedin_arch.py:36-38` hardcodes 1080x1080px @ 150dpi for LinkedIn. But final savefig uses `bbox_inches=None` which may not preserve exact dimensions. Comment at line 740-741 mentions this was fixed but worth re-verifying.
- Files: `scripts/generate_linkedin_arch.py:36-38, 740-743`
- Impact: LinkedIn diagrams may be off-size by a few pixels. Could affect feed display.
- Fix approach: Test actual output dimensions. Document DPI behavior. Consider `bbox_inches="tight"` with size verification.

**Process flow step calculation unclear:**
- Issue: `generate.py:332-333` has redundant calculation: `cx = (i + 0.5) * step_w / step_w * (n / n)` then overwrites with `cx = (i + 0.5) / n`. First line is dead code.
- Files: `scripts/generate.py:332-333`
- Impact: Code quality. Confusing for maintainers. May indicate incomplete refactor.
- Fix approach: Remove dead line. Clarify step positioning logic.

---

## Scalability Limits

**Component deduplication O(n²) complexity:**
- Issue: See "Substring redundancy detection" above. Architecture parsing becomes slow with 100+ components.
- Files: `scripts/parse_context.py:301-317`
- Impact: Slow on large monorepos with many services.
- Fix approach: Implement set-based deduplication. Add performance test.

**Grid layout assumes ≤9 groups:**
- Issue: `generate_linkedin_arch.py:100-110` uses fixed 3x3 grid (max 9 groups). Projects with 10+ component layers break layout.
- Files: `scripts/generate_linkedin_arch.py:85-131`
- Impact: Cannot visualize large architectures. Users must manually merge layers.
- Fix approach: Implement pagination or scrollable layout. Support 4x4+ grids. Add validation with helpful error.

---

## Fragile Areas

**Color palette matching is fuzzy:**
- Issue: `generate_linkedin_arch.py:69-74` uses substring matching to find palette colors. "Backend" matches "Backend / API" but "Backend" alone won't match custom label "Backend Service".
- Files: `scripts/generate_linkedin_arch.py:69-74`
- Impact: Custom layer names fall back to default color. No visual distinction.
- Fix approach: Use exact category key matching. Provide explicit color assignment in config. Document naming conventions.

**Icon drawing function resolution:**
- Issue: `generate_linkedin_arch.py:525-553` attempts fuzzy category-to-icon matching. Can fail to find correct icon if category strings don't match expected format.
- Files: `scripts/generate_linkedin_arch.py:525-553`
- Impact: Wrong icons rendered. Defaults to generic diamond. Confusing diagrams.
- Fix approach: Use explicit category key enum. Pre-compile icon function map. Add logging for icon mismatches.

---

## Missing Features Blocking Use

**No way to customize component order in architecture diagram:**
- Issue: Components are ordered by category (per LAYER_ORDER) but users cannot customize order.
- Files: `scripts/parse_context.py:204-211`
- Impact: Diagram layout may not match user's mental model. No way to show dependencies top-down vs left-right.
- Fix approach: Add `layer_order` parameter to config. Allow user-defined category ordering.

**No legend or label support in basic infographics:**
- Issue: `generate.py` has no way to add a legend explaining color meaning or data unit.
- Files: `scripts/generate.py` throughout
- Impact: Ambiguous infographics. Readers don't understand color encoding.
- Fix approach: Add `add_legend()` method. Support unit/key labels on charts.

---

*Concerns audit: 2026-03-15*
