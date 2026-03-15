---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/generate_linkedin_arch.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Each category group title bar shows a small recognizable icon to the left of the label text"
    - "Icons are drawn purely with matplotlib patches — no emoji, no unicode, no image files"
    - "All 13 GROUP_STYLES categories have a distinct icon"
    - "The rendered PNG looks correct at 1080x1080px with no clipping or overlap"
  artifacts:
    - path: "scripts/generate_linkedin_arch.py"
      provides: "draw_group_icon() function + integration in draw_title_bar()"
  key_links:
    - from: "draw_title_bar()"
      to: "draw_group_icon()"
      via: "called after the title text, passing ax, icon_cx, icon_cy, icon_size, label"
---

<objective>
Add professional patch-based icons to each category group title bar in the LinkedIn architecture diagram renderer.

Purpose: Every group title bar (Frontend, Backend, Database, Auth, etc.) currently shows only bold text on a colored bar. Adding a recognizable icon to the left of the text makes the diagram more visually distinctive and immediately communicates each layer's purpose at a glance — the way professional Kubernetes-style architecture diagrams do.

Output: Modified `scripts/generate_linkedin_arch.py` where every group title bar draws a small patch-based icon to the left of its label text.
</objective>

<execution_context>
</execution_context>

<context>
@scripts/generate_linkedin_arch.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement draw_group_icon() with patch-based icons for all 13 categories</name>
  <files>scripts/generate_linkedin_arch.py</files>
  <action>
Add a new function `draw_group_icon(ax, cx, cy, size, category, color)` after the existing drawing primitives (after `draw_dashed_arrow`, before the main renderer). This function draws a small icon centered at `(cx, cy)` using only matplotlib patches. `size` is the icon diameter in data coordinates (use ~0.018 for the title bar height of 0.035). `color` is the title_fg (white).

Icon designs — all using patches from `matplotlib.patches` and `matplotlib.path.Path`:

- **frontend** — browser window: outer Rectangle, inner Rectangle for address bar strip, two small circles for browser dots
- **mobile** — phone outline: tall thin Rectangle (rounded), tiny Rectangle at bottom for home button
- **backend** / **backend_api** — gear: use `matplotlib.patches.Wedge` repeated 6–8 times to form gear teeth around a central Circle, OR use a `matplotlib.path.Path` with a pre-computed gear polygon; simpler alternative: two overlapping rectangles rotated 45deg (a "cog" asterisk) + central Circle
- **database** — cylinder: two Ellipses (top and bottom of cylinder) + a Rectangle for the cylinder body connecting them; use zorder carefully so top ellipse renders above the body
- **auth** — padlock: Rectangle for body + Arc or Ellipse-segment for the shackle (the U-shaped loop above the lock body); use a `Arc` patch for the shackle
- **queue** / **events** — three horizontal lines (three thin Rectangles), representing a message queue
- **storage** — stack of disks: three thin Rectangle slices stacked vertically with slight gaps
- **cloud** — cloud shape: three overlapping Circles of varying sizes arranged to form a cloud silhouette, clipped together; use a `PathPatch` with a hand-coded bezier cloud outline OR three `Circle` patches that overlap (simpler, works well at small size)
- **infrastructure** — server rack: two or three stacked rectangles with a small circle on each (server LEDs)
- **monitoring** — line chart: three connected line segments using `ax.plot` restricted to the icon bounding box, with a small dot at the peak; OR a Polygon forming an upward spike
- **ci_cd** — circular arrow / refresh: use `Arc` patch with an arrowhead at one end (draw Arc then a tiny Polygon arrowhead)
- **ai_ml** — neural node: three Circles connected by lines (ax.plot), forming a simple 3-node network
- **other** / default — question mark alternative: a simple star or diamond Polygon

Implementation notes:
- All patch coordinates are in data units (0–1 axis scale). `size` ≈ 0.018 gives an icon that fits inside the 0.035-tall title bar with padding.
- Use `zorder=10` on icon patches so they render above the title bar background.
- Set `clip_on=False` on all patches.
- For icons using `ax.plot` (monitoring, ai_ml lines), pass `transform=ax.transData`, `zorder=10`, `clip_on=False`.
- Use `color` (white, `"#FFFFFF"`) for all patch facecolors and edgecolors so icons are visible on the colored title bar background.
- Build a dispatch dict `_ICON_DRAW_FNS = { "frontend": _draw_frontend, ... }` and have `draw_group_icon` look up and call the right function, falling back to the default.

After implementing the function, modify `draw_title_bar()` to:
1. Accept an additional keyword argument `category: str = ""`.
2. After adding the text, call `draw_group_icon(ax, cx=x + 0.022, cy=y + h - 0.018, size=0.013, category=category, color=fg)` — this places the icon at the left side of the title bar, horizontally offset from the left edge.
3. Shift the label text 0.022 units to the right to make room: change `x + w / 2` to `x + 0.022 + (w - 0.022) / 2` in the `ax.text` call.

Finally, update the call site in `render_architecture()` (around line 295–297) to pass `category=category` to `draw_title_bar()`.
  </action>
  <verify>
    <automated>cd /home/eager-eagle/code/infographic-skill/infographic-skill && python scripts/generate_linkedin_arch.py --layers "Frontend:React,Next.js|Backend:FastAPI,Celery|Database:PostgreSQL,Redis|Cloud Services:AWS S3,CloudFront|Auth:JWT,OAuth2|Queue / Events:RabbitMQ,Celery|Storage:S3,GCS|Monitoring:Datadog,Grafana|CI/CD:GitHub Actions,Docker|AI / ML:OpenAI,LangChain|Infrastructure:Kubernetes,Terraform" --title "Test Architecture" --output /tmp/test_icons_arch.png && python -c "from PIL import Image; img = Image.open('/tmp/test_icons_arch.png'); assert img.size == (1080, 1080), f'Wrong size: {img.size}'; print('OK:', img.size)"</automated>
  </verify>
  <done>
    - `draw_group_icon()` exists and handles all 13 categories plus a default fallback
    - `draw_title_bar()` accepts `category` and calls `draw_group_icon()`
    - Text in title bar is shifted right to avoid overlapping the icon
    - Running the test command above produces a 1080x1080 PNG with no Python errors
    - Visually: each group title bar shows a small white icon to the left of the label
  </done>
</task>

</tasks>

<verification>
Run the automated verify command. Then open `/tmp/test_icons_arch.png` and confirm:
- Every title bar has a small icon to the left of the text
- Text and icon do not overlap
- No icon bleeds outside its title bar
- All 11 test groups show distinct icons
</verification>

<success_criteria>
All 13 GROUP_STYLES categories render a recognizable patch-based icon in their title bar. The diagram dimensions remain 1080x1080px. No regressions to existing layout, chips, or arrow routing.
</success_criteria>

<output>
After completion, update `.planning/STATE.md` quick tasks table:

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Add professional patch-based icons to architecture diagram group title bars | 2026-03-15 | (commit hash) | .planning/quick/1-add-professional-icons-symbols-to-archit |
</output>
