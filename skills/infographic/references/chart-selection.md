# Chart Selection Reference

Use this decision matrix to pick the right chart type for any data.
Wrong chart type = misleading or confusing infographic, regardless of visual quality.

---

## Decision Tree

```
What are you showing?
│
├── PART OF A WHOLE
│   ├── ≤5 categories → Donut chart (with percentages labeled)
│   └── >5 categories → Horizontal bar chart (sorted desc)
│
├── COMPARISON (between items at a point in time)
│   ├── Few items (≤7) → Horizontal bar chart
│   ├── Many items → Dot plot or table
│   └── Multiple attributes → Radar chart (cautiously)
│
├── TREND OVER TIME
│   ├── Continuous data → Line chart
│   ├── Discrete periods → Bar chart (vertical)
│   └── Multiple series (≤4) → Multi-line chart
│
├── DISTRIBUTION
│   ├── Continuous data → Histogram
│   └── Multiple groups → Box plot / violin plot
│
├── RELATIONSHIP / CORRELATION
│   └── Two variables → Scatter plot (add trend line if r > 0.5)
│
├── RANKING
│   └── Any number → Horizontal bar chart, sorted descending
│
├── GEOGRAPHIC
│   ├── Rates / densities → Choropleth map
│   └── Counts / points → Bubble map
│
├── FLOW / PROCESS
│   ├── Sequential steps → Process flow diagram
│   ├── Hierarchical → Tree / org chart
│   └── Material / energy flow → Sankey diagram
│
└── SINGLE IMPORTANT NUMBER
    └── Big number + supporting context + optional sparkline
```

---

## Chart Type Reference

### Bar Chart (Horizontal)
**When to use**: Rankings, comparisons, when labels are long
**Max categories**: 12–15 (more → table)
**Key rules**:
- Sort by value (largest first), unless order is inherently meaningful
- Start axis at 0
- Label bars directly if space allows
- Color: single color unless encoding a second variable

### Bar Chart (Vertical)
**When to use**: Time series with discrete periods (months, quarters, years)
**Key rules**:
- Chronological order (oldest left → newest right)
- Limit to ≤20 bars before switching to line chart

### Line Chart
**When to use**: Continuous trend over time; change is the point
**Max series**: 4 (more → confusing; filter or use small multiples)
**Key rules**:
- Don't use if data has meaningful gaps (use bar instead)
- Solid lines > dashed for primary; dashed for reference/forecast
- Label lines directly at end (not legend if possible)

### Donut / Pie Chart
**When to use**: Part of whole, when composition matters more than comparison
**Max slices**: 5 (more → horizontal bar chart)
**Key rules**:
- Order: largest slice starting at 12 o'clock, clockwise
- Always label percentages directly on or near slices
- One color per slice; avoid rainbow
- Donut preferred over pie (center space for key number)

### Scatter Plot
**When to use**: Correlation between two continuous variables
**Key rules**:
- Add trend line when correlation is apparent
- Label outliers only (don't label all points)
- Bubble size = third variable (use sparingly)

### Area Chart
**When to use**: Volume/magnitude of trend over time; stacked for composition
**Key rules**:
- Don't stack more than 5 series
- Use transparency (alpha) for overlapping areas
- 100% stacked area = part-of-whole over time

### Histogram
**When to use**: Distribution of a single continuous variable
**Key rules**:
- Bins should be equal width
- Start y-axis at 0
- Add normal curve overlay if showing normality

### Big Number (KPI)
**When to use**: Single critical metric is the story; everything else is context
**Components**:
- Large bold number (primary)
- Label (secondary, smaller)
- Delta / trend (tertiary, colored)
- Optional: sparkline, progress ring, or icon

### Process Flow
**When to use**: Sequential steps, onboarding flows, how-it-works
**Key rules**:
- Number steps clearly (1, 2, 3...)
- Keep labels to ≤5 words per step
- Arrows or lines must show directionality
- Max 8 steps before it becomes overwhelming

---

## What NOT to Use (Ever)

| Chart | Problem |
|---|---|
| 3D bar/pie charts | Distort visual perception of values |
| Pie with >5 slices | Impossible to compare small slices |
| Dual Y-axis line chart | Almost always misleading |
| Bubble chart as main chart | Hard to read accurately |
| Word cloud | Cannot be read quantitatively |
| Pictogram with distorted icons | Area distortion misleads |
| Truncated Y-axis on bar charts | Makes small differences look large |

---

## Color Encoding for Charts

| Data type | Palette recommendation |
|---|---|
| Sequential (low → high) | `viridis`, `Blues`, `Greens` (single-hue) |
| Diverging (negative → 0 → positive) | `RdBu`, `coolwarm`, Red-White-Blue |
| Categorical (unordered groups) | `tab10`, custom 4–5 color set |
| Highlight one category | Gray for all, primary color for the one |
