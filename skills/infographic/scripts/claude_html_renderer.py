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


def inject_logos(html: str) -> str:
    """Replace every empty data-icon placeholder with an inline brand SVG / monogram."""
    def repl(m: re.Match) -> str:
        svg = get_icon_svg(m.group(2), size=40)
        svg = svg.replace('width="40" height="40"', 'width="100%" height="100%"', 1)
        return f"<span{m.group(1)}>{svg}</span>"
    return re.sub(r'<span([^>]*data-icon="([^"]+)"[^>]*)>\s*</span>', repl, html)


def screenshot(html_path: Path, png_path: Path, size: tuple[int, int] = design.FORMATS["square"]) -> Path:
    width, height = size
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
        page.wait_for_timeout(800)
        page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": width, "height": height})
        browser.close()
    return png_path


def finish(html_path: Path, png_path: Path, fmt: str | None = None) -> Path:
    """Inject logos into an agent- or API-written page, warn about generic patterns, screenshot it."""
    html = html_path.read_text(encoding="utf-8")
    for warning in lint_html(html):
        print(f"⚠️  generic-design pattern: {warning}", file=sys.stderr)
    html_path.write_text(inject_logos(html), encoding="utf-8")
    return screenshot(html_path, png_path, design.canvas_size(fmt))


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
) -> tuple[Path, dict]:
    """Ask the chosen backend (or Anthropic API) for the page, then finish it."""
    if backend and backend != "api":
        prompt = backends.build_prompt("render", backend, model, spec, style=style, kind=kind,
                                       fmt=fmt, style_dir=style_dir)
        raw = backends.run(backend, model, prompt)
        html = backends.extract_html(raw)
        out = Path(output).with_suffix(".png")
        out.parent.mkdir(parents=True, exist_ok=True)
        html_path = out.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
        effective_model = model or backends.BACKENDS[backend]["default_model"] or backend
        usage = {"backend": backend, "model": effective_model, "input_tokens": 0, "output_tokens": 0, "total_cost": 0.0}
        return finish(html_path, out, fmt), usage

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
    ap.add_argument("--style-dir", default=None,
                    help="folder of your own .html graphics used as reference (default: the skill's style/)")
    ap.add_argument("--kind", default="architecture")
    ap.add_argument("--backend", default=None, help="Backend: auto|session|claude|agy|codex|copilot|opencode|api")
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    args = ap.parse_args()

    if args.finish:
        print(f"✅  PNG → {finish(args.finish, Path(args.output).with_suffix('.png'), args.fmt).resolve()}")
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
