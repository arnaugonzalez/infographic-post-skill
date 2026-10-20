You are a world-class information designer. Build a LinkedIn {kind} infographic as ONE
self-contained HTML file rendered at exactly {canvas}×{canvas} CSS px (it will be screenshotted
by headless Chromium at that viewport, device scale 2).

CONTENT (use ALL of it, exact names, no invented technologies):
{spec}

REQUIREMENTS
- Body exactly {canvas}×{canvas}, overflow hidden, nothing may be clipped or overlap.
- Show the layers and the labelled data-flow connections between them (inline SVG for
  arrows/paths so they line up with the boxes).
- Brand logos: wherever a technology appears, emit the placeholder
  <span class="logo" data-icon="EXACT TECH NAME"></span> — a post-processor replaces it
  with the real brand SVG. Do not draw logos yourself.
- Typography: one Google Font family is allowed via <link> (e.g. Inter, Space Grotesk,
  Manrope). Titles 44px+.
- Visual style: {style}. Aim for the polish of a Stripe/Vercel/Linear launch graphic:
  strong hierarchy, generous spacing, deliberate color, subtle depth. No lorem ipsum,
  no emoji, no external images, no JavaScript.
- Keep every item name EXACTLY as in the content — never split, rename or drop one.
- Item descriptions ≥17px, layer labels ≥20px, connector labels ≥16px with a solid pill background.
- Connector strokes ≥3px with clear arrowheads; route them through empty space, never across cards.
- Logos 40-48px inside a light rounded tile so dark brand marks stay visible on dark backgrounds.
- Prefer fewer, larger cards over dense grids; balance column heights.
Return ONLY the HTML document, starting with <!doctype html>.
