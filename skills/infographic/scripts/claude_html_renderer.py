"""Claude HTML renderer — structured JSON → art-directed HTML → PNG (4:5, square or 2:1, at 2x).

An agent or API model writes one self-contained HTML page from a design brief; the page
marks every technology with <span class="logo" data-icon="Name"></span>, which is
replaced with the real brand SVG (or a monogram) before Playwright screenshots it.

Why HTML instead of an image model: text is typeset, not painted, so names are
never misspelled or dropped (benchmark/RESULTS.md: best text accuracy and
completeness of all renderers).

Ways to use it:

  Subscription CLI mode (default auto-detected: claude, agy, codex, copilot, opencode):
      python3 scripts/claude_html_renderer.py --spec spec.json --backend claude --output out.png

  In-session mode (inside Claude Code — no API cost, the agent is the designer):
      python3 scripts/claude_html_renderer.py --spec spec.json --backend session
      # agent writes page.html following the brief, then:
      python3 scripts/claude_html_renderer.py --finish page.html --output out.png

  API mode (needs ANTHROPIC_API_KEY, ~$0.13-0.28 per image with Opus 5.5 at low effort):
      python3 scripts/claude_html_renderer.py --spec spec.json --backend api --output out.png
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backends  # noqa: E402
import design  # noqa: E402
from icon_registry import get_icon_svg  # noqa: E402
from slop_lint import lint_html  # noqa: E402

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "low"   # benchmark: low beat medium on publishability at 40% of the cost


def build_brief(spec: dict, style: str | None = None, kind: str = "architecture",
                fmt: str | None = None, style_dir: str | None = None) -> str:
    return design.render_brief(spec, kind=kind, style=style, fmt=fmt, style_dir=style_dir)


def inject_logos(html: str, brand_colors: bool = False) -> str:
    """Replace every empty data-icon placeholder with an inline brand SVG / monogram.

    Marks are drawn in the surrounding text color unless ``brand_colors`` is set, so logos do
    not add colors to a one-accent palette.
    """
    def repl(m: re.Match) -> str:
        svg = get_icon_svg(m.group(2), size=40, mono=not brand_colors)
        svg = svg.replace('width="40" height="40"', 'width="100%" height="100%"', 1)
        return f"<span{m.group(1)}>{svg}</span>"
    return re.sub(r'<span([^>]*data-icon="([^"]+)"[^>]*)>\s*</span>', repl, html)


# One rect per rendered line of every text node; report lines of different nodes that overlap
# and lines that leave the canvas. Models ignore "nothing may overlap" often enough to check it.
_LAYOUT_CHECK_JS = """([w, h]) => {
  const boxes = [];
  const blocks = new Map();
  const blockOf = (el) => {
    while (el.parentElement && getComputedStyle(el).display.startsWith("inline")) el = el.parentElement;
    if (!blocks.has(el)) blocks.set(el, blocks.size);
    return blocks.get(el);
  };
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let id = 0;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const text = n.textContent.trim();
    if (!text) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    for (const r of range.getClientRects()) {
      if (r.width * r.height > 4) boxes.push({id, block: blockOf(n.parentElement), text: text.slice(0, 40), r});
    }
    id++;
  }
  const issues = [];
  for (const b of boxes) {
    if (b.r.left < -1 || b.r.top < -1 || b.r.right > w + 1 || b.r.bottom > h + 1)
      issues.push(`outside the canvas: "${b.text}"`);
  }
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const a = boxes[i], b = boxes[j];
    if (a.id === b.id || a.block === b.block) continue;  // lines of one paragraph may touch
    const x = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
    const y = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
    if (x > 2 && y > 2 && x * y > 40) issues.push(`text overlaps: "${a.text}" / "${b.text}"`);
  }
  return [...new Set(issues)].slice(0, 10);
}"""


def _capture(html_path: Path, png_path: Path, size: tuple[int, int]) -> list[str]:
    """Screenshot the page and return the layout problems found in the rendered DOM."""
    width, height = size
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
        page.wait_for_timeout(800)
        issues = page.evaluate(_LAYOUT_CHECK_JS, [width, height])
        page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": width, "height": height})
        browser.close()
    return [f"layout: {i}" for i in issues]


def screenshot(html_path: Path, png_path: Path, size: tuple[int, int] = design.FORMATS["square"]) -> Path:
    for issue in _capture(html_path, png_path, size):
        print(f"⚠️  {issue}", file=sys.stderr)
    return png_path


def review(html_path: Path, png_path: Path, fmt: str | None = None, brand_colors: bool = False) -> list[str]:
    """Lint the page, inject logos, screenshot it; print and return every problem found."""
    html = html_path.read_text(encoding="utf-8")
    issues = [f"generic-design pattern: {w}" for w in lint_html(html)]
    html_path.write_text(inject_logos(html, brand_colors), encoding="utf-8")
    issues += _capture(html_path, png_path, design.canvas_size(fmt))
    for issue in issues:
        print(f"⚠️  {issue}", file=sys.stderr)
    return issues


def finish(html_path: Path, png_path: Path, fmt: str | None = None, brand_colors: bool = False) -> Path:
    """Inject logos into an agent- or API-written page, warn about problems, screenshot it."""
    review(html_path, png_path, fmt, brand_colors)
    return png_path


REPAIR = """

YOUR PREVIOUS PAGE:
```html
{html}
```

PROBLEMS FOUND AFTER RENDERING IT IN CHROMIUM:
{issues}

Fix every problem without changing the thesis, archetype or content. Shorten or move text rather
than shrinking it below the minimum sizes. Return ONLY the complete corrected HTML document."""


def render_with_claude(
    spec: dict,
    output: str,
    style: str | None = None,
    kind: str = "architecture",
    model: str | None = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    backend: str | None = None,
    fmt: str | None = None,
    style_dir: str | None = None,
    repair_rounds: int = 1,
) -> tuple[Path, dict]:
    """Ask the chosen backend (or Anthropic API) for the page, then finish it.

    With a subscription backend, problems found after rendering are sent back to the same model
    for up to ``repair_rounds`` corrections.
    """
    if backend and backend != "api":
        prompt = backends.build_prompt("render", backend, model, spec, style=style, kind=kind,
                                       fmt=fmt, style_dir=style_dir)
        out = Path(output).with_suffix(".png")
        out.parent.mkdir(parents=True, exist_ok=True)
        html_path = out.with_suffix(".html")
        html = backends.extract_html(backends.run(backend, model, prompt))
        for attempt in range(repair_rounds + 1):
            html_path.write_text(html, encoding="utf-8")
            issues = review(html_path, out, fmt)
            if not issues or attempt == repair_rounds:
                break
            print(f"🔧  Sending {len(issues)} problem(s) back to {backend} for a fix...")
            fix = prompt + REPAIR.format(html=html, issues="\n".join(f"- {i}" for i in issues))
            html = backends.extract_html(backends.run(backend, model, fix))
        effective_model = model or backends.BACKENDS[backend]["default_model"] or backend
        usage = {"backend": backend, "model": effective_model, "input_tokens": 0, "output_tokens": 0,
                 "total_cost": 0.0, "issues": issues}
        return out, usage

    effective_model = model or DEFAULT_MODEL
    import anthropic
    prices = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.1, 0.5)}
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY") or None)
    with client.messages.stream(
        model=effective_model, max_tokens=48000, output_config={"effort": effort},
        messages=[{"role": "user", "content": build_brief(spec, style, kind, fmt, style_dir)}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"{effective_model} declined the request: {msg.stop_details}")
    text = "".join(b.text for b in msg.content if b.type == "text")
    html = backends.extract_html(text)
    out = Path(output).with_suffix(".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    p_in, p_out = prices.get(effective_model, (4.0, 20.0))
    usage = {"model": effective_model, "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
             "total_cost": (msg.usage.input_tokens * p_in + msg.usage.output_tokens * p_out) / 1e6}
    return finish(html_path, out, fmt), usage


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", type=Path, help="structured JSON (content_structurer output)")
    ap.add_argument("--print-brief", action="store_true", help="print the design brief and exit")
    ap.add_argument("--print-prompt", action="store_true", help="print the full backend/model prompt and exit")
    ap.add_argument("--finish", type=Path, help="inject logos into this HTML and screenshot it")
    ap.add_argument("--output", default="infographic.png")
    ap.add_argument("--style", default=None,
                    help=f"archetype: {', '.join(design.ARCHETYPES)} (default {design.DEFAULT_ARCHETYPE})")
    ap.add_argument("--format", dest="fmt", default=None,
                    help=f"canvas: {', '.join(design.FORMATS)} (default {design.DEFAULT_FORMAT})")
    ap.add_argument("--brand-colors", action="store_true",
                    help="draw logos in their brand colors (default: the surrounding text color)")
    ap.add_argument("--style-dir", default=None,
                    help="folder of your own .html graphics used as reference (default: the skill's style/)")
    ap.add_argument("--kind", default="architecture")
    ap.add_argument("--backend", default=None, help="Backend: auto|session|claude|agy|codex|copilot|opencode|api")
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    args = ap.parse_args()

    if args.finish:
        print(f"✅  PNG → {finish(args.finish, Path(args.output).with_suffix('.png'), args.fmt, args.brand_colors).resolve()}")
        return
    if not args.spec:
        ap.error("--spec is required unless --finish is used")
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if args.print_brief:
        print(build_brief(spec, args.style, args.kind, args.fmt, args.style_dir))
        return
    backend, model = backends.resolve(args.backend, args.model)
    if args.print_prompt:
        print(backends.build_prompt("render", backend, model, spec, style=args.style, kind=args.kind,
                                    fmt=args.fmt, style_dir=args.style_dir))
        return
    if backend == "session":
        print(build_brief(spec, args.style, args.kind, args.fmt, args.style_dir))
        return
    png, usage = render_with_claude(
        spec, args.output, args.style, args.kind, model=model, effort=args.effort, backend=backend,
        fmt=args.fmt, style_dir=args.style_dir,
    )
    print(f"✅  PNG → {png.resolve()}  ({usage['model']}, ${usage['total_cost']:.3f})")


if __name__ == "__main__":
    main()
