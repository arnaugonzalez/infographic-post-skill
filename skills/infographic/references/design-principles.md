# Infographic Design Principles

Reference guide for Claude to produce professional, publication-quality infographics.
Read this file when making any design decision.

---

## 1. The Single Message Rule

Every infographic must have **one core message** that can be stated in one sentence.
All design choices serve that message. If an element doesn't reinforce the message,
remove it.

> ❌ "This infographic shows our business metrics."
> ✅ "Enterprise customers drove 78% of our Q3 growth."

---

## 2. Visual Hierarchy

Viewers scan in order: **biggest → boldest → most colorful → top-left**.
Design your hierarchy around this scan path.

| Priority | Element | Treatment |
|---|---|---|
| 1st | Hero number / headline | ≥2x larger than body, primary color, bold |
| 2nd | Section titles | Medium size, secondary color or bold |
| 3rd | Data labels / body | Standard size, neutral color |
| 4th | Source / footnotes | Smallest, muted, bottom-right |

**Rule**: If everything is bold, nothing is bold. Use emphasis sparingly.

---

## 3. Color System

### Palette structure (max 5 colors)
- **Primary** — hero elements, main bars, key callouts
- **Secondary** — supporting data, secondary series
- **Accent** — single use highlight ("this is the most important number")
- **Neutral** — labels, axes, secondary text
- **Background** — canvas; never pure white (#FAFAFA is better than #FFFFFF)

### Contrast minimums (WCAG AA)
- Body text on background: 4.5:1 ratio minimum
- Large text (≥18pt or bold ≥14pt): 3:1 minimum
- Tool: use `plt.rcParams` or check manually

### Colorblind safety
Avoid red-green as the only differentiator (8% of men are colorblind).
Safe combos: blue/orange, blue/yellow, purple/green.
Matplotlib's `tab10` and `viridis` are safe by default.

---

## 4. Typography Rules

### Scale (3 sizes maximum)
| Role | Size | Weight |
|---|---|---|
| Hero / Big Number | 28–48pt | ExtraBold/Black |
| Section Title | 14–18pt | Bold |
| Body / Labels | 9–12pt | Regular |
| Caption / Source | 7–9pt | Regular, italic |

### Font pairing
- **One font family, two weights** is safest. E.g., DejaVu Sans Regular + Bold.
- If using two families: one geometric sans (headers) + one humanist (body).
- Never use more than 2 typefaces.

### Don'ts
- No decorative/script fonts in data labels
- No text smaller than 7pt (illegible in print)
- No ALL CAPS for body text (kills readability)

---

## 5. Chart Selection Guide

See also: `references/chart-selection.md` for a full decision matrix.

| Data type | Best chart |
|---|---|
| Part of whole (≤5 categories) | Donut chart |
| Part of whole (>5 categories) | Horizontal bar chart |
| Ranking / comparison | Horizontal bar chart |
| Trend over time | Line chart |
| Distribution | Histogram or box plot |
| Correlation | Scatter plot |
| Geographic | Map (choropleth) |
| Single number | Big number + sparkline |
| Composition over time | Stacked area or 100% stacked bar |

### Chart don'ts
- ❌ 3D charts (distort perception)
- ❌ Pie charts with >5 slices → use bar
- ❌ Dual-axis line charts (misleading scales)
- ❌ Truncated Y-axis (start at 0 for bars)
- ❌ Pie/donut without percentage labels or a legend

---

## 6. Layout & Grid

### Standard infographic sizes
| Format | Dimensions |
|---|---|
| Pinterest / vertical | 1000 × 1500px |
| Instagram story | 1080 × 1920px |
| Instagram square | 1080 × 1080px |
| LinkedIn landscape | 1200 × 628px |
| Presentation slide | 1920 × 1080px |
| Letter (print, 150dpi) | 1275 × 1650px |

### Spacing rules
- **Outer margin**: ≥40px on all sides (≥0.5in for print)
- **Between sections**: ≥24px vertical gap
- **Between related elements**: 8–12px (proximity = relationship)
- **Unrelated sections**: ≥32px gap

### Alignment
- Align everything to an implicit grid.
- Left-align text blocks (avoid centered blocks longer than 2 lines).
- Numbers in tables/grids: right-align or decimal-align.

---

## 7. Whitespace

Whitespace is not empty space — it is structure, breathing room, and emphasis.

- More whitespace around the hero element = more visual weight.
- Dense, cramped infographics feel overwhelming → people skip them.
- When in doubt, remove an element rather than shrink it.

---

## 8. Data Integrity

- **Always show the source** (bottom-right, small text)
- **Always show sample size** for survey data (n=X)
- **Round numbers** appropriately — "47.3%" is noisier than "47%"
- **Don't cherry-pick axes** — start bar charts at zero
- **Context beats raw numbers** — show % change, comparison, or benchmark

---

## 9. Final Polish Checklist

Before saving:
- [ ] One core message reads in ≤3 seconds
- [ ] Highest-priority element is visually dominant
- [ ] No more than 4–5 colors total
- [ ] No element smaller than 7pt
- [ ] All text passes contrast check
- [ ] Source attribution included
- [ ] Consistent margins and alignment
- [ ] No decorative elements that don't carry information
- [ ] Colorblind-safe palette
- [ ] File saved at ≥150 DPI
