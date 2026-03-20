---
phase: quick
plan: 260320-g0a
subsystem: infographic-skill
tags: [linkedin, gemini, prompt-quality, cli, skill-docs]
dependency_graph:
  requires: []
  provides: [--learnings CLI param, anti-sketch prompt directives, LinkedIn text post char limit rule]
  affects: [scripts/generate_pretty.py, SKILL.md]
tech_stack:
  added: []
  patterns: [argparse CLI extension, f-string prompt injection, skill documentation]
key_files:
  created: []
  modified:
    - scripts/generate_pretty.py
    - SKILL.md
    - /home/eager-eagle/.claude/skills/infographic-skill/SKILL.md
decisions:
  - "Injected learnings block into both image and HTML prompt builders for full coverage"
  - "Synced local SKILL.md to global copy (local was missing Versioned Output section)"
  - "Added CRITICAL STYLE CONSTRAINTS to both dashboard and architecture image prompt branches"
metrics:
  duration: "12 minutes"
  completed: "2026-03-20T10:46:49Z"
  tasks_completed: 2
  files_modified: 3
---

# Quick 260320-g0a: Improve LinkedIn Infographic and Text Post Workflow Summary

Anti-sketch Gemini prompt directives + `--learnings` CLI parameter + 2,500-char LinkedIn text post rule enforced in both SKILL.md copies.

---

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Enhance Gemini prompts and add --learnings param to generate_pretty.py | d9765b7 | scripts/generate_pretty.py |
| 2 | Add LinkedIn text post char limit and --learnings docs to SKILL.md | 1b23201 | SKILL.md, ~/.claude/skills/infographic-skill/SKILL.md |

---

## What Was Built

### Task 1: generate_pretty.py enhancements

**Anti-sketch directives** added to `_build_image_prompt()` in both the `dashboard` and `architecture` branches. The block reads:

```
CRITICAL STYLE CONSTRAINTS — DO NOT VIOLATE:
• This is NOT a sketch, NOT hand-drawn, NOT a wireframe, NOT a whiteboard drawing
• Render as a PIXEL-PERFECT digital UI design — crisp vector edges, no pencil textures
• Use FLAT or subtle gradient fills — never hatching, crosshatch, or pencil shading
• All text must be sharp, anti-aliased, horizontal, and perfectly legible
• Colors must be SATURATED and VIBRANT (not muted, pastel, or washed-out)
• Backgrounds must be smooth gradients — no paper texture, no grain, no noise
• Think: Figma mockup, Dribbble top shot, Apple keynote slide — NOT napkin sketch
```

**Learnings injection** added to:
- `_build_image_prompt()`: prepends `Key learnings / technologies featured:` block to CONTENT/ARCHITECTURE section when `config.get("learnings")` is non-empty
- `_build_html_prompt()`: appends learnings block to the serialized `data_str` before formatting into the HTML template

**CLI parameter**: `--learnings` added to argparse with descriptive help text. Wired into all three config-building branches (`--config`, `--layers`, `--text`) via `if args.learnings: config["learnings"] = args.learnings`.

### Task 2: SKILL.md updates

**New section** `## LinkedIn Text Post Rules` added after `## Output` (before `## Examples`) in both files:
- Hard 2,500 character limit (count not words)
- Hook line guidance for "see more" fold
- CTA and hashtag rules
- Learnings-driven content requirement

**`--learnings` documentation** added in two places:
- Pretty Mode workflow: new example invocation showing `--config arch.json --learnings "..."`
- LinkedIn Architecture Diagrams section: new "Learnings-focused posts" note with `--layers` + `--learnings` example

**Sync**: Local project SKILL.md was missing the "Versioned Output", "Pretty Mode", and updated dependencies sections compared to the global copy. Both files are now identical (verified with `diff`).

---

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Additional scope (not a deviation, discovered during sync):** The local SKILL.md was significantly out of date compared to the global skill copy (missing Versioned Output, Pretty Mode, and updated deps sections). Since the plan required both files to be identical, the local copy was brought fully up to date. This is the intended behavior per the plan's requirement C ("Ensure both files are identical in content").

---

## Verification Results

All checks passed:
- `python3 scripts/generate_pretty.py --help` shows `--learnings` parameter
- `grep "NOT a sketch" scripts/generate_pretty.py` finds 2 occurrences (one per viz branch)
- `grep "2,500 characters" SKILL.md` confirms char limit rule
- `grep "learnings" SKILL.md` returns 6 matches
- `diff SKILL.md ~/.claude/skills/infographic-skill/SKILL.md` shows no differences

---

## Self-Check: PASSED

Files exist:
- FOUND: /home/eager-eagle/code/infographic-skill/infographic-skill/scripts/generate_pretty.py
- FOUND: /home/eager-eagle/code/infographic-skill/infographic-skill/SKILL.md
- FOUND: /home/eager-eagle/.claude/skills/infographic-skill/SKILL.md

Commits exist:
- d9765b7 — feat(quick-260320-g0a): enhance prompts and add --learnings param
- 1b23201 — feat(quick-260320-g0a): add LinkedIn text post rules and --learnings docs
