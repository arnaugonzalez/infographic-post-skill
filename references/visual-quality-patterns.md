# ★★★★★ Visual Quality Patterns for HTML/CSS Tech Infographics

> Research compiled March 2026 — Practical, paste-ready code patterns

---

## 1. ANIMATED GRADIENT GLOW BORDERS (Cards)

### Technique A: Pure CSS with `@property` + `conic-gradient` (BEST — no JS)

Source: [codetv.dev](https://codetv.dev/blog/animated-css-gradient-border)

```css
/* Register the custom property so CSS can interpolate angles */
@property --bg-angle {
  inherits: false;
  initial-value: 0deg;
  syntax: "<angle>";
}

@keyframes spin {
  to { --bg-angle: 360deg; }
}

.glow-card {
  /* Two backgrounds: solid interior + gradient border */
  background:
    linear-gradient(to bottom, oklch(0.1 0.2 240 / 0.95), oklch(0.1 0.2 240 / 0.95)) padding-box,
    conic-gradient(from var(--bg-angle) in oklch longer hue, oklch(1 0.37 0) 0 0) border-box;
  border: 2px solid transparent;
  border-radius: 1rem;
  animation: spin 3s linear infinite;
}
```

**Why it works:** `background-origin: padding-box` keeps the solid bg inside, `border-box` lets the gradient bleed into the transparent border. `longer hue` gives full rainbow from a single color.

### Technique B: Pseudo-element glow (simpler, wider support)

Source: [CodePen by mike-schultz](https://codepen.io/mike-schultz/pen/NgQvGO)

```css
.gradient-border {
  --borderWidth: 3px;
  background: #1D1F20;
  position: relative;
  border-radius: var(--borderWidth);
}

.gradient-border::after {
  content: '';
  position: absolute;
  top: calc(-1 * var(--borderWidth));
  left: calc(-1 * var(--borderWidth));
  height: calc(100% + var(--borderWidth) * 2);
  width: calc(100% + var(--borderWidth) * 2);
  background: linear-gradient(60deg, #f79533, #f37055, #ef4e7b, #a166ab, #5073b8, #1098ad, #07b39b, #6fba82);
  border-radius: calc(2 * var(--borderWidth));
  z-index: -1;
  animation: animatedgradient 3s ease alternate infinite;
  background-size: 300% 300%;
}

@keyframes animatedgradient {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

### Technique C: Soft outer glow (behind card, diffused)

Source: [CodePen by SimonEvans](https://codepen.io/SimonEvans/pen/bgVxMO)

```css
.soft-glow-card {
  position: relative;
  background-color: rgba(21, 24, 35, 0.7);
  box-shadow: inset 2px 2px 10px rgba(0, 0, 0, 0.3);
}

.soft-glow-card::after {
  position: absolute;
  content: '';
  top: 0; left: 0; right: 0;
  z-index: -1;
  height: 100%; width: 100%;
  margin: 0 auto;
  filter: blur(40px);
  transform: scale(1.3);
  background: linear-gradient(90deg, #0fffc1, #7e0fff);
  background-size: 200% 200%;
  animation: animateGlow 10s ease infinite;
}

@keyframes animateGlow {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

### Technique D: Static premium glow (no animation — best for infographics/print)

```css
.premium-card {
  background: #0f1729;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  box-shadow:
    0 0 0 1px rgba(99, 102, 241, 0.1),
    0 4px 6px -1px rgba(0, 0, 0, 0.3),
    0 0 20px -5px rgba(99, 102, 241, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
```

---

## 2. SVG CIRCUIT BOARD / TECH PATTERN BACKGROUNDS

### Technique A: Pure SVG inline pattern (self-contained, no external deps)

```html
<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="position:absolute;top:0;left:0;opacity:0.05;">
  <defs>
    <pattern id="circuit" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
      <!-- Horizontal traces -->
      <line x1="0" y1="20" x2="40" y2="20" stroke="currentColor" stroke-width="1"/>
      <line x1="60" y1="20" x2="100" y2="20" stroke="currentColor" stroke-width="1"/>
      <!-- Vertical traces -->
      <line x1="40" y1="20" x2="40" y2="50" stroke="currentColor" stroke-width="1"/>
      <line x1="60" y1="50" x2="60" y2="80" stroke="currentColor" stroke-width="1"/>
      <!-- Corner turn -->
      <line x1="40" y1="50" x2="60" y2="50" stroke="currentColor" stroke-width="1"/>
      <!-- Nodes / solder points -->
      <circle cx="40" cy="20" r="3" fill="currentColor"/>
      <circle cx="60" cy="20" r="2" fill="none" stroke="currentColor" stroke-width="1"/>
      <circle cx="40" cy="50" r="2" fill="currentColor"/>
      <circle cx="60" cy="50" r="3" fill="none" stroke="currentColor" stroke-width="1"/>
      <circle cx="60" cy="80" r="2" fill="currentColor"/>
      <!-- IC chip rectangle -->
      <rect x="70" y="60" width="16" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1"/>
      <!-- IC pins -->
      <line x1="73" y1="60" x2="73" y2="55" stroke="currentColor" stroke-width="0.5"/>
      <line x1="78" y1="60" x2="78" y2="55" stroke="currentColor" stroke-width="0.5"/>
      <line x1="83" y1="60" x2="83" y2="55" stroke="currentColor" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#circuit)"/>
</svg>
```

### Technique B: CSS-only dot grid (simpler tech feel)

```css
.tech-grid-bg {
  background-image:
    radial-gradient(circle, rgba(99, 102, 241, 0.15) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

### Technique C: Animated circuit trace (SVG stroke animation)

Source: Dribbble/Udacity approach — animate `stroke-dashoffset` on polylines.

```css
.circuit-trace {
  stroke-dasharray: 200;
  stroke-dashoffset: 200;
  animation: trace 3s ease-in-out infinite;
}

@keyframes trace {
  0%   { stroke-dashoffset: 200; }
  50%  { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -200; }
}
```

### Key Resources:
- **heropatterns.com** — Free repeatable SVG patterns including circuit board (by Steve Schoger)
- **pattern.monster** — SVG pattern generator with customizable colors
- **bgjar.com** — Free SVG background generator

---

## 3. MESH GRADIENT / AURORA BACKGROUNDS

### Technique A: Stacked radial gradients (mesh simulation)

Source: [littleblueinsight.com](https://littleblueinsight.com/tool/technology/css-gradient-mesh-generator/)

```css
.mesh-gradient {
  background-color: #0a0a1a;
  background-image:
    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.4) 0%, transparent 50%),
    radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.3) 0%, transparent 50%),
    radial-gradient(at 50% 100%, rgba(6, 182, 212, 0.3) 0%, transparent 50%),
    radial-gradient(at 80% 50%, rgba(236, 72, 153, 0.2) 0%, transparent 40%);
}
```

**Pro tip from sources:** "Used by brands like Stripe and Apple, these ethereal backgrounds feel modern and premium." Apply `filter: blur(100px)` to a child container for smoother blending.

### Technique B: Aurora animated background (pure CSS)

Source: [daltonwalsh.com](https://daltonwalsh.com/blog/aurora-css-background-effect/)

```css
.aurora-bg {
  position: relative;
  background: #0a0a1a;
  overflow: hidden;
}

.aurora-bg .colour-1,
.aurora-bg .colour-2,
.aurora-bg .colour-3 {
  position: absolute;
  width: 60%; height: 60%;
  border-radius: 50%;
  opacity: 0.4;
  filter: blur(80px);
}

.aurora-bg .colour-1 {
  background: #6366f1;
  top: -20%; left: -10%;
  animation: drift1 15s ease-in-out infinite alternate;
}
.aurora-bg .colour-2 {
  background: #06b6d4;
  bottom: -20%; right: -10%;
  animation: drift2 18s ease-in-out infinite alternate;
}
.aurora-bg .colour-3 {
  background: #a855f7;
  top: 40%; left: 30%;
  animation: drift3 20s ease-in-out infinite alternate;
}

@keyframes drift1 { to { transform: translate(30%, 20%); } }
@keyframes drift2 { to { transform: translate(-25%, -15%); } }
@keyframes drift3 { to { transform: translate(-20%, 30%); } }
```

### Technique C: Animated gradient (simplest, one-element)

Source: [CodePen aurora](https://codepen.io/shottsn/pen/QOqpqP)

```css
.simple-aurora {
  background: linear-gradient(45deg, #32a6ff 0%, #3f6fff 49%, #8d54ff 82%);
  background-size: 200%;
  animation: aurora 10s infinite;
}

@keyframes aurora {
  0%   { background-position: left top; }
  25%  { background-position: right top; }
  50%  { background-position: right bottom; }
  75%  { background-position: left bottom; }
  100% { background-position: left top; }
}
```

### Generators:
- **csshero.org/mesher/** — CSS mesh gradient generator
- **auroragradient.com** — Aurora gradient generator with grain/noise

---

## 4. SVG ARROWS & CONNECTORS FOR INFOGRAPHICS

### Technique A: SVG `<marker>` for arrowheads (the correct way)

Source: [W3Schools SVG Marker](https://www.w3schools.com/graphics/svg_marker.asp) + [shalvah.me](https://blog.shalvah.me/posts/learn-svg-by-drawing-an-arrow)

```html
<svg width="100%" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Arrowhead marker -->
    <marker id="arrowhead" markerWidth="10" markerHeight="10"
            refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1"/>
    </marker>
    <!-- Circle dot marker -->
    <marker id="dot" markerWidth="8" markerHeight="8" refX="4" refY="4">
      <circle cx="4" cy="4" r="3" fill="#6366f1"/>
    </marker>
  </defs>

  <!-- Straight arrow -->
  <line x1="50" y1="50" x2="250" y2="50"
        stroke="#6366f1" stroke-width="2" marker-end="url(#arrowhead)"/>

  <!-- Curved connector with dot start and arrow end -->
  <path d="M 50,120 C 100,80 200,160 300,120"
        stroke="#6366f1" stroke-width="2" fill="none"
        marker-start="url(#dot)" marker-end="url(#arrowhead)"/>

  <!-- Right-angle connector (L-shape) -->
  <polyline points="50,170 150,170 150,190 300,190"
            stroke="#6366f1" stroke-width="2" fill="none"
            marker-end="url(#arrowhead)"/>
</svg>
```

### Technique B: Dashed/animated flow arrows

```html
<svg width="400" height="60" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow-flow" markerWidth="8" markerHeight="8"
            refX="7" refY="4" orient="auto">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="#06b6d4"/>
    </marker>
  </defs>

  <path d="M 20,30 C 80,10 160,50 220,30 S 340,10 380,30"
        stroke="#06b6d4" stroke-width="2" fill="none"
        stroke-dasharray="8 4"
        marker-end="url(#arrow-flow)">
    <animate attributeName="stroke-dashoffset"
             from="24" to="0" dur="1s" repeatCount="indefinite"/>
  </path>
</svg>
```

### Technique C: Vertical flow connector between cards

```html
<svg width="40" height="60" viewBox="0 0 40 60" style="display:block;margin:0 auto;">
  <defs>
    <marker id="arr-down" markerWidth="8" markerHeight="6" refX="4" refY="6" orient="auto">
      <path d="M0,0 L4,6 L8,0" fill="none" stroke="#6366f1" stroke-width="1.5"/>
    </marker>
  </defs>
  <line x1="20" y1="0" x2="20" y2="54"
        stroke="#6366f1" stroke-width="2" stroke-dasharray="4 3"
        marker-end="url(#arr-down)"/>
</svg>
```

---

## 5. LUCIDE ICONS — INLINE SVG USAGE

### How Lucide works:
- All icons are **stroke-based SVGs** on a **24×24 viewBox**
- They use `stroke="currentColor"` so they inherit text color via CSS
- Licensed under ISC (free for commercial use)
- 1000+ icons available at [lucide.dev/icons](https://lucide.dev/icons)

### Getting SVG paths — just copy from lucide.dev:

Visit any icon page, click "Copy SVG" and paste inline. Example common tech icons:

```html
<!-- Server icon -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <rect width="20" height="8" x="2" y="2" rx="2" ry="2"/>
  <rect width="20" height="8" x="2" y="14" rx="2" ry="2"/>
  <line x1="6" x2="6.01" y1="6" y2="6"/>
  <line x1="6" x2="6.01" y1="18" y2="18"/>
</svg>

<!-- Database icon -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <ellipse cx="12" cy="5" rx="9" ry="3"/>
  <path d="M3 5V19A9 3 0 0 0 21 19V5"/>
  <path d="M3 12A9 3 0 0 0 21 12"/>
</svg>

<!-- Cloud icon -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
</svg>

<!-- Shield/Security icon -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
</svg>

<!-- Zap (performance/speed) icon -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
</svg>

<!-- Globe (network/internet) icon -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
  <path d="M2 12h20"/>
</svg>
```

### Styling Lucide icons in your CSS:

```css
.icon {
  display: inline-flex;
  width: 24px; height: 24px;
  color: currentColor;  /* inherits from parent */
}

/* Override size */
.icon-lg svg { width: 32px; height: 32px; }
.icon-xl svg { width: 48px; height: 48px; }

/* Colored icon inside a badge */
.icon-badge {
  display: inline-flex;
  align-items: center; justify-content: center;
  width: 48px; height: 48px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}
```

---

## 6. CSS TEXT GRADIENT + GLOW EFFECTS

### Technique A: Gradient text (the standard approach)

```css
.gradient-text {
  background: linear-gradient(135deg, #6366f1, #06b6d4, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### Technique B: Gradient text + glow halo

```css
.glow-title {
  background: linear-gradient(135deg, #818cf8, #22d3ee, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.4))
          drop-shadow(0 0 40px rgba(6, 182, 212, 0.2));
}
```

### Technique C: Animated gradient text

```css
@property --text-angle {
  inherits: false;
  initial-value: 0deg;
  syntax: "<angle>";
}

@keyframes text-shimmer {
  to { --text-angle: 360deg; }
}

.shimmer-title {
  background: linear-gradient(
    var(--text-angle),
    #6366f1, #06b6d4, #a855f7, #6366f1
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: text-shimmer 4s linear infinite;
}
```

### Technique D: Text with subtle emboss (premium feel without glow)

```css
.emboss-title {
  color: #e2e8f0;
  text-shadow:
    0 1px 0 rgba(255, 255, 255, 0.1),
    0 -1px 0 rgba(0, 0, 0, 0.5);
}
```

---

## 7. LINKEDIN CAROUSEL INFOGRAPHIC DESIGN PATTERNS

Based on research into what makes infographics go viral on LinkedIn:

### Visual Framework:

```css
/* LinkedIn optimal: 1080x1080 or 1080x1350 */
.linkedin-slide {
  width: 1080px;
  height: 1350px;
  padding: 80px;
  font-family: 'Inter', -apple-system, sans-serif;
  background: #0a0a1a;
  color: #e2e8f0;
}

/* Consistent top branding bar */
.brand-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 40px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 48px;
}

/* Slide number indicator */
.slide-number {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
}

/* Big bold statement per slide */
.slide-headline {
  font-size: 56px;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin-bottom: 32px;
}

/* Supporting text */
.slide-body {
  font-size: 24px;
  line-height: 1.6;
  color: rgba(255,255,255,0.7);
  max-width: 85%;
}
```

### What makes LinkedIn infographics viral:
1. **One big idea per slide** — not dense walls of text
2. **Consistent visual system** — same colors, fonts, spacing across all slides
3. **Slide numbers** — creates progression/curiosity
4. **Bold headlines** — scannable in 2 seconds
5. **High contrast** — dark bg + bright accents
6. **Brand consistency** — logo/handle on every slide
7. **Call to action on last slide** — "Follow for more", "Save this"

---

## 8. ★★★★ vs ★★★★★ — WHAT SEPARATES GREAT FROM ELITE

### 8.1 Depth & Layering

```css
/* Multi-layer depth system */
.layer-background { z-index: 0; }  /* patterns, grids */
.layer-ambient    { z-index: 1; }  /* glows, gradients */
.layer-content    { z-index: 2; }  /* cards, text */
.layer-accent     { z-index: 3; }  /* highlights, badges */
.layer-overlay    { z-index: 4; }  /* tooltips, popovers */

/* Cards that "float" above the background */
.elevated-card {
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.3),
    0 4px 8px rgba(0, 0, 0, 0.2),
    0 12px 24px rgba(0, 0, 0, 0.15);
}
```

### 8.2 Subtle Textures (Noise/Grain)

```css
/* SVG noise texture overlay — paste-ready */
.noise-overlay::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.03;
  z-index: 10;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
}

/* Alternative: CSS filter for grain */
.grain-filter {
  filter: contrast(1.02) brightness(1.01);
  /* Pair with the noise overlay above */
}
```

### 8.3 Color Theory — Systematic, Not Random

```css
:root {
  /* Primary palette (analogous: blue-violet family) */
  --color-primary-50: #eef2ff;
  --color-primary-400: #818cf8;
  --color-primary-500: #6366f1;  /* Main accent */
  --color-primary-600: #4f46e5;
  --color-primary-900: #312e81;

  /* Complementary accent (cyan — opposite on wheel) */
  --color-accent: #06b6d4;
  --color-accent-muted: rgba(6, 182, 212, 0.15);

  /* Semantic colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;

  /* Neutral scale */
  --color-bg-deep: #020617;
  --color-bg-card: #0f172a;
  --color-bg-elevated: #1e293b;
  --color-text-primary: #f1f5f9;
  --color-text-secondary: rgba(241, 245, 249, 0.6);
  --color-text-muted: rgba(241, 245, 249, 0.35);
  --color-border: rgba(255, 255, 255, 0.06);
  --color-border-accent: rgba(99, 102, 241, 0.3);
}
```

**Rules for 5-star color:**
- Max 2 accent colors + 1 complementary pop
- Use opacity variants (0.1, 0.2, 0.4) not different hues for subtlety
- Dark backgrounds: never pure black (#000) — use #020617 or #0a0a1a
- Text: never pure white (#fff) — use #f1f5f9 or #e2e8f0

### 8.4 Typography Hierarchy (more than size)

```css
/* 5-star typography system */
.text-display {
  font-size: 64px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.05;
  color: var(--color-text-primary);
}

.text-h1 {
  font-size: 42px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  color: var(--color-text-primary);
}

.text-h2 {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1.25;
  color: var(--color-text-primary);
}

.text-h3 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: 1.35;
  color: var(--color-text-secondary);
}

.text-body {
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0.01em;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.text-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.text-mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 14px;
  letter-spacing: -0.01em;
}
```

**Key differentiators (what amateurs miss):**
- **Negative letter-spacing** on large text (-0.02em to -0.03em)
- **Positive letter-spacing** on small caps/labels (+0.1em)
- **Line-height decreases** as text gets larger (1.6 body → 1.05 display)
- **Weight + opacity** used together for hierarchy, not just size
- **Font smoothing** for dark backgrounds:
  ```css
  body { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
  ```

### 8.5 Negative Space

```css
/* Generous padding system */
.section-spacing { padding: 80px 0; }
.card-padding    { padding: 32px; }
.content-gap     { gap: 24px; }

/* Rule of thumb for 5-star infographics: */
/* Content should fill ~60-70% of available space */
/* 30-40% should be breathing room */
```

### 8.6 Visual Rhythm & Repetition

```css
/* Consistent spacing scale (multiples of 8) */
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
}

/* Consistent border-radius scale */
:root {
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
}

/* ALL cards use the same radius */
.card { border-radius: var(--radius-lg); }
.badge { border-radius: var(--radius-full); }
.icon-box { border-radius: var(--radius-md); }
```

### 8.7 Micro-Details Checklist

```css
/* Shadow quality — layered, not single */
.shadow-premium {
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.06),
    0 2px 4px rgba(0, 0, 0, 0.06),
    0 4px 8px rgba(0, 0, 0, 0.06),
    0 8px 16px rgba(0, 0, 0, 0.06),
    0 16px 32px rgba(0, 0, 0, 0.06);
}

/* Inner highlight on cards (simulates top light source) */
.card-inner-glow {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Border that's visible but not distracting */
.subtle-border {
  border: 1px solid rgba(255, 255, 255, 0.06);
}

/* Dividers */
.divider {
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    rgba(255, 255, 255, 0.08) 20%,
    rgba(255, 255, 255, 0.08) 80%,
    transparent
  );
}

/* Consistent icon containers */
.icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px; height: 48px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.15);
  color: #818cf8;
}

/* Status dots */
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}

/* Tags/badges */
.tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-radius: 9999px;
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.2);
}
```

---

## COMPLETE EXAMPLE: Premium Tech Architecture Card

```html
<style>
  @property --bg-angle {
    inherits: false;
    initial-value: 0deg;
    syntax: "<angle>";
  }

  .arch-card {
    position: relative;
    background:
      linear-gradient(to bottom, rgba(15,23,42,0.95), rgba(15,23,42,0.95)) padding-box,
      conic-gradient(from var(--bg-angle) in oklch longer hue, oklch(0.7 0.15 270) 0 0) border-box;
    border: 1px solid transparent;
    border-radius: 16px;
    padding: 32px;
    box-shadow:
      0 0 0 1px rgba(99,102,241,0.05),
      0 4px 24px rgba(0,0,0,0.3),
      inset 0 1px 0 rgba(255,255,255,0.05);
    animation: spin 8s linear infinite;
  }

  @keyframes spin { to { --bg-angle: 360deg; } }

  .arch-card-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
  }

  .arch-card-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px; height: 48px;
    border-radius: 12px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.2);
    color: #818cf8;
  }

  .arch-card-title {
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #f1f5f9;
  }

  .arch-card-subtitle {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: rgba(241,245,249,0.4);
  }

  .arch-card-body {
    font-size: 15px;
    line-height: 1.6;
    color: rgba(241,245,249,0.65);
  }

  .arch-card-tags {
    display: flex;
    gap: 8px;
    margin-top: 20px;
    flex-wrap: wrap;
  }

  .arch-tag {
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    border-radius: 9999px;
    background: rgba(6,182,212,0.1);
    color: #22d3ee;
    border: 1px solid rgba(6,182,212,0.15);
  }
</style>

<div class="arch-card">
  <div class="arch-card-header">
    <div class="arch-card-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="8" x="2" y="2" rx="2" ry="2"/>
        <rect width="20" height="8" x="2" y="14" rx="2" ry="2"/>
        <line x1="6" x2="6.01" y1="6" y2="6"/>
        <line x1="6" x2="6.01" y1="18" y2="18"/>
      </svg>
    </div>
    <div>
      <div class="arch-card-title">API Gateway</div>
      <div class="arch-card-subtitle">Edge Layer</div>
    </div>
  </div>
  <div class="arch-card-body">
    Rate limiting, auth, and request routing. Handles 50k req/s with &lt;10ms P99 latency.
  </div>
  <div class="arch-card-tags">
    <span class="arch-tag">Kong</span>
    <span class="arch-tag">gRPC</span>
    <span class="arch-tag">mTLS</span>
  </div>
</div>
```

---

## SOURCES

1. codetv.dev — Animated CSS gradient borders (Jason Lengstorf)
2. CodePen mike-schultz — Animated gradient border pseudo-element
3. CodePen SimonEvans — Animated gradient glow
4. heropatterns.com — Free repeatable SVG background patterns (Steve Schoger)
5. pattern.monster — SVG pattern generator
6. bgjar.com — Free SVG background generator
7. csshero.org/mesher — CSS mesh gradient generator
8. daltonwalsh.com — Aurora CSS background tutorial
9. littleblueinsight.com — CSS gradient mesh generator
10. W3Schools — SVG Marker reference
11. shalvah.me — Learn SVG by drawing an arrow
12. lucide.dev — Lucide icons official documentation
13. dev.to/oobleck — CSS Aurora effect experiments
14. Dribbble/jennie-yip — Circuit animation SVG+CSS technique
15. freefrontend.com — 57 CSS border animations collection
16. github.com/lucide-icons/lucide — Lucide icon format specification
