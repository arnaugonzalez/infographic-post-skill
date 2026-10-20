"""Infographic pipeline benchmark (Oct 2026).

Stages (each writes under benchmark/results/):
  structure  — codebase report/digest → structured JSON, across LLMs
  render     — fixed structured JSON → PNG, across image models / Claude HTML / template
  judge      — blind vision scoring of every PNG by two judges (Gemini + Claude)
  report     — aggregate scores + costs into results/summary.md

Every API call is priced from its usage and appended to results/ledger.jsonl.
A call is refused before it is sent if the vendor's spend would exceed its cap.

    .venv/bin/python benchmark/bench.py structure
    .venv/bin/python benchmark/bench.py render --source claude-opus-5-5
    .venv/bin/python benchmark/bench.py judge
    .venv/bin/python benchmark/bench.py report
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parent / "skills" / "infographic"
sys.path.insert(0, str(SKILL / "scripts"))

from content_structurer import _STRUCTURER_PROMPT, _strip_json_fences  # noqa: E402
from image_prompt_builder import build_image_prompt  # noqa: E402

CASES = ROOT / "cases"
RESULTS = ROOT / "results"
LEDGER = RESULTS / "ledger.jsonl"
CAPS = {"anthropic": 2.85, "gemini": 2.85}
CASE_NAMES = ["project-b", "project-a", "infographic"]

# USD per 1M tokens (input, output incl. thinking) — verified Oct 2026
TEXT_PRICES = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}
# image models: (input $/1M, text-out $/1M, {size: $/image})
IMAGE_PRICES = {
    "gemini-3.1-flash-image": (0.50, 3.00, {"1K": 0.067, "2K": 0.101}),
    "gemini-3-pro-image": (2.00, 12.00, {"1K": 0.134, "2K": 0.134}),
    "gemini-3.1-flash-lite-image": (0.25, 1.50, {"1K": 0.0336}),
}

_lock = threading.Lock()


def _load_env() -> None:
    for line in (SKILL / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def spent(vendor: str) -> float:
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l)["cost"] for l in LEDGER.read_text().splitlines()
               if json.loads(l)["vendor"] == vendor)


def charge(vendor: str, stage: str, case: str, model: str, cost: float, usage: dict) -> None:
    with _lock:
        with LEDGER.open("a") as fh:
            fh.write(json.dumps({"vendor": vendor, "stage": stage, "case": case, "model": model,
                                 "cost": round(cost, 5), "usage": usage, "ts": time.time()}) + "\n")


def guard(vendor: str, estimate: float) -> None:
    with _lock:
        total = spent(vendor)
    if total + estimate > CAPS[vendor]:
        raise RuntimeError(f"budget cap: {vendor} spent ${total:.3f} + est ${estimate:.3f} > ${CAPS[vendor]}")


# ── Clients ──────────────────────────────────────────────────────────────────

_GEMINI = None


def gemini_client():
    """Shared client — a temporary genai.Client is closed by GC before the call completes."""
    global _GEMINI
    with _lock:
        if _GEMINI is None:
            from google import genai
            _GEMINI = genai.Client(api_key=os.environ["INFG_API_KEY"])
    return _GEMINI


def claude_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=3)


def call_text(model: str, prompt: str, stage: str, case: str, effort: str | None = None,
              image_png: bytes | None = None, max_tokens: int = 32000) -> tuple[str, float, float]:
    """Return (text, cost_usd, seconds) for a text-output call to Claude or Gemini."""
    t0 = time.time()
    p_in, p_out = TEXT_PRICES[model]
    if model.startswith("claude"):
        guard("anthropic", 0.05 if stage == "judge" else 0.5 if "opus" in model else 0.2)
        content: list = []
        if image_png:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                         "data": base64.standard_b64encode(image_png).decode()}})
        content.append({"type": "text", "text": prompt})
        kwargs = {"output_config": {"effort": effort}} if effort else {}
        with claude_client().messages.stream(model=model, max_tokens=max_tokens,
                                             messages=[{"role": "user", "content": content}],
                                             **kwargs) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError(f"{model} refused: {msg.stop_details}")
        text = "".join(b.text for b in msg.content if b.type == "text")
        u = msg.usage
        cost = (u.input_tokens * p_in + u.output_tokens * p_out) / 1e6
        charge("anthropic", stage, case, model, cost,
               {"in": u.input_tokens, "out": u.output_tokens, "stop": msg.stop_reason})
    else:
        from google.genai import types
        guard("gemini", 0.1)
        parts: list = []
        if image_png:
            parts.append(types.Part.from_bytes(data=image_png, mime_type="image/png"))
        parts.append(prompt)
        resp = gemini_client().models.generate_content(model=model, contents=parts)
        um = resp.usage_metadata
        inp = um.prompt_token_count or 0
        out = (um.candidates_token_count or 0) + (um.thoughts_token_count or 0)
        text = resp.text or ""
        cost = (inp * p_in + out * p_out) / 1e6
        charge("gemini", stage, case, model, cost, {"in": inp, "out": out})
    return text, cost, time.time() - t0


def call_image(model: str, prompt: str, size: str, case: str,
               ref_png: bytes | None = None) -> tuple[bytes | None, float, float]:
    from google.genai import types
    p_in, p_text, per_img = IMAGE_PRICES[model]
    guard("gemini", per_img[size] + 0.02)
    t0 = time.time()
    parts: list = []
    if ref_png:
        parts.append(types.Part.from_bytes(data=ref_png, mime_type="image/png"))
    parts.append(prompt)
    cfg = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspect_ratio="1:1", image_size=size),
    )
    resp = gemini_client().models.generate_content(model=model, contents=parts, config=cfg)
    img = None
    for cand in resp.candidates or []:
        for part in (cand.content.parts if cand.content else []):
            if getattr(part, "inline_data", None) and part.inline_data.data:
                img = part.inline_data.data
    um = resp.usage_metadata
    inp = um.prompt_token_count or 0
    think = um.thoughts_token_count or 0
    cost = (inp * p_in + think * p_text) / 1e6 + (per_img[size] if img else 0)
    charge("gemini", "render", case, f"{model}@{size}", cost, {"in": inp, "think": think, "image": bool(img)})
    return img, cost, time.time() - t0


# ── Stage 1: structuring ─────────────────────────────────────────────────────

STRUCT_RUNS = [
    # (label, model, input kind, effort)
    ("baseline-gemini-2.5-flash-fullreport", "gemini-2.5-flash", "report", None),
    ("gemini-2.5-flash", "gemini-2.5-flash", "digest", None),
    ("gemini-3.8-flash", "gemini-3.8-flash", "digest", None),
    ("gemini-3.1-flash-lite", "gemini-3.1-flash-lite", "digest", None),
    ("claude-haiku-5-5", "claude-haiku-5-5", "digest", "low"),
    ("claude-sonnet-5-5", "claude-sonnet-5-5", "digest", "low"),
    ("claude-opus-5-5", "claude-opus-5-5", "digest", "low"),
]


def stage_structure(_args) -> None:
    out_dir = RESULTS / "structure"
    out_dir.mkdir(parents=True, exist_ok=True)

    def run(case: str, run_def) -> None:
        label, model, kind, effort = run_def
        dest = out_dir / f"{case}__{label}.json"
        if dest.exists():
            return
        src = (CASES / f"{case}_{kind}.txt").read_text()
        prompt = _STRUCTURER_PROMPT.format(codebase_report=src)
        try:
            text, cost, secs = call_text(model, prompt, "structure", case, effort=effort, max_tokens=16000)
            data = json.loads(_strip_json_fences(text))
            ok = True
        except Exception as exc:  # recorded, not swallowed: the error goes into the result file
            data, cost, secs, ok = {"error": str(exc)[:500]}, 0.0, 0.0, False
        dest.write_text(json.dumps({"label": label, "model": model, "input": kind, "ok": ok,
                                    "cost": cost, "seconds": round(secs, 1), "data": data}, indent=2))
        print(f"  {case:12} {label:40} ok={ok} ${cost:.4f} {secs:.0f}s")

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda a: run(*a), [(c, r) for c in CASE_NAMES for r in STRUCT_RUNS]))


# ── Stage 2: rendering ───────────────────────────────────────────────────────

HTML_BRIEF = """You are a world-class information designer. Build a LinkedIn infographic as ONE
self-contained HTML file rendered at exactly 1080×1080 CSS px (it will be screenshotted
by headless Chromium at that viewport, device scale 2).

CONTENT (use ALL of it, exact names, no invented technologies):
{spec}

REQUIREMENTS
- Body exactly 1080×1080, overflow hidden, nothing may be clipped or overlap.
- Architecture story: show the layers and the labelled data-flow connections between them
  (use inline SVG for arrows/paths so they line up with the boxes).
- Brand logos: wherever a technology appears, emit the placeholder
  <span class="logo" data-icon="EXACT TECH NAME"></span> — a post-processor replaces it
  with the real brand SVG (size it with CSS on .logo, e.g. 32-40px). Do not draw logos yourself.
- Typography: one Google Font family is allowed via <link> (e.g. Inter, Space Grotesk,
  Manrope). Text must be readable on a phone: nothing under 15px; titles 44px+.
- Visual style: {style}. Aim for the polish of a Stripe/Vercel/Linear launch graphic:
  strong hierarchy, generous spacing, deliberate color, subtle depth. No lorem ipsum,
  no emoji, no external images, no JavaScript.
Return ONLY the HTML document, starting with <!doctype html>."""

HTML_BRIEF_V2 = HTML_BRIEF.replace("Return ONLY the HTML", """LESSONS FROM REVIEW (apply strictly)
- Keep every item name EXACTLY as in the spec — never split, rename or drop one.
- Item descriptions ≥17px, layer labels ≥20px, connector labels ≥16px with a solid pill background.
- Connector strokes ≥3px with clear arrowheads; route them through empty space, never across cards.
- Logos 40-48px inside a light rounded tile so dark brand marks stay visible on the dark background.
- Prefer fewer, larger cards over dense grids; balance column heights.
Return ONLY the HTML""")

STYLE_TEXT = "modern dark — deep navy/indigo background, glowing accent colors per layer, glassy cards"


def _inject_logos(html: str) -> str:
    from icon_registry import get_icon_svg

    def repl(m: re.Match) -> str:
        svg = get_icon_svg(m.group(2), size=36)
        if svg.startswith("<svg"):
            svg = svg.replace('width="36" height="36"', 'width="100%" height="100%"')
        return f'<span{m.group(1)}>{svg}</span>'
    return re.sub(r'<span([^>]*data-icon="([^"]+)"[^>]*)>\s*</span>', repl, html)


def screenshot(html_path: Path, png_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080}, device_scale_factor=2)
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
        page.wait_for_timeout(800)
        page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        browser.close()


def overflow_report(html_path: Path) -> dict:
    """Deterministic layout check: count text elements clipped outside the 1080 canvas."""
    from playwright.sync_api import sync_playwright
    js = """() => { let out=0, tiny=0; for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect(); if (!r.width || !el.childNodes.length) continue;
        const hasText = [...el.childNodes].some(n => n.nodeType===3 && n.textContent.trim());
        if (!hasText) continue;
        if (r.right>1081 || r.bottom>1081 || r.left<-1 || r.top<-1) out++;
        if (parseFloat(getComputedStyle(el).fontSize) < 13) tiny++; } return {out, tiny}; }"""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
        res = page.evaluate(js)
        browser.close()
    return res


RENDERERS = [
    # (label, kind, model, size/effort)
    ("template-jinja", "template", None, None),
    ("gemini-3.1-flash-image@1K", "image", "gemini-3.1-flash-image", "1K"),
    ("gemini-3.1-flash-image@2K", "image", "gemini-3.1-flash-image", "2K"),
    ("gemini-3-pro-image@2K", "image", "gemini-3-pro-image", "2K"),
    ("gemini-3.1-flash-lite-image@1K", "image", "gemini-3.1-flash-lite-image", "1K"),
    ("claude-opus-5-5-html", "html", "claude-opus-5-5", "medium"),
    ("claude-sonnet-5-5-html", "html", "claude-sonnet-5-5", "medium"),
    ("claude-haiku-5-5-html", "html", "claude-haiku-5-5", "medium"),
    ("claude-opus-5-5-html-v2-low", "html2", "claude-opus-5-5", "low"),
]

HYBRID_PROMPT = """The attached image is a correct, information-complete architecture infographic.
Re-render it as a premium, illustrated 1:1 LinkedIn infographic with richer depth, lighting and
polish. HARD RULES: keep every piece of text EXACTLY as written (same words, same spelling),
keep every component, connection and the overall layout/grouping. Do not add new text."""


def render_one(case: str, spec: dict, label: str, kind: str, model: str | None, opt: str | None) -> None:
    out_dir = RESULTS / "render" / case
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{label}.png"
    meta_path = out_dir / f"{label}.json"
    if png.exists():
        return
    meta = {"label": label, "kind": kind, "model": model, "cost": 0.0, "seconds": 0.0}
    try:
        if kind == "template":
            from template_renderer import render_infographic
            html_path = render_infographic(spec, template_name="arch-dark-glassmorphism",
                                           output=str(out_dir / f"{label}.html"))
            screenshot(Path(html_path), png)
            meta["layout"] = overflow_report(Path(html_path))
        elif kind == "image":
            prompt = build_image_prompt(spec, infographic_type="architecture", style="modern-dark")
            img, cost, secs = call_image(model, prompt, opt, case)
            meta.update(cost=cost, seconds=round(secs, 1))
            if not img:
                raise RuntimeError("no image returned")
            png.write_bytes(img)
        elif kind in ("html", "html2"):
            brief = HTML_BRIEF_V2 if kind == "html2" else HTML_BRIEF
            prompt = brief.format(spec=json.dumps(spec, indent=1), style=STYLE_TEXT)
            text, cost, secs = call_text(model, prompt, "render", case, effort=opt, max_tokens=48000)
            m = re.search(r"<!doctype html.*</html>", text, re.S | re.I)
            html = _inject_logos(m.group(0) if m else text)
            html_path = out_dir / f"{label}.html"
            html_path.write_text(html)
            screenshot(html_path, png)
            meta.update(cost=cost, seconds=round(secs, 1), layout=overflow_report(html_path))
        elif kind == "hybrid":
            ref = (out_dir / "claude-opus-5-5-html.png").read_bytes()
            img, cost, secs = call_image(model, HYBRID_PROMPT, opt, case, ref_png=_downscale(ref, 1024))
            meta.update(cost=cost, seconds=round(secs, 1))
            if not img:
                raise RuntimeError("no image returned")
            png.write_bytes(img)
        meta["ok"] = True
    except Exception as exc:  # recorded per-run so one failure doesn't sink the batch
        meta.update(ok=False, error=str(exc)[:500])
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"  {case:12} {label:34} ok={meta['ok']} ${meta['cost']:.4f} {meta['seconds']}s")


def stage_render(args) -> None:
    jobs = []
    for case in CASE_NAMES:
        src = json.loads((RESULTS / "structure" / f"{case}__{args.source}.json").read_text())
        spec = src["data"]
        (RESULTS / "render" / case).mkdir(parents=True, exist_ok=True)
        (RESULTS / "render" / case / "_spec.json").write_text(json.dumps(spec, indent=2))
        renderers = RENDERERS if not args.only else [r for r in RENDERERS if r[0] in args.only]
        jobs += [(case, spec, *r) for r in renderers]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda j: render_one(*j), jobs))
    if args.hybrid:
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda c: render_one(c, None, "hybrid-opus-html+gemini-3-pro-image@2K",
                                               "hybrid", "gemini-3-pro-image", "2K"), CASE_NAMES))


# ── Stage 3: judging ─────────────────────────────────────────────────────────

JUDGE_PROMPT = """You are a strict senior design director reviewing a LinkedIn architecture
infographic before it is published. The image must faithfully present this specification:

{spec}

Score each criterion 1-10 (10 = flawless, 5 = mediocre, 1 = unusable). Be harsh and specific.
- text_accuracy: all text legible and correctly spelled; no garbled/gibberish glyphs; no invented
  technologies or labels absent from the spec.
- completeness: every layer, item and connection from the spec is present and correctly grouped.
- logo_accuracy: brand logos are the real, recognizable marks (generic or wrong logos score low;
  if no logos are drawn, score 4).
- hierarchy: clear reading order and visual hierarchy; readable on a phone screen.
- aesthetics: polish, color, spacing, depth — would it stop a scroll on LinkedIn?
- publishable: overall, could this be posted as-is by a senior engineer without embarrassment?

Return ONLY JSON: {{"text_accuracy":n,"completeness":n,"logo_accuracy":n,"hierarchy":n,
"aesthetics":n,"publishable":n,"errors":["concrete defects, max 6"]}}"""

JUDGES = ["gemini-3.1-pro-preview", "claude-sonnet-5-5"]


def _downscale(png: bytes, side: int = 1024) -> bytes:
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im.thumbnail((side, side))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def judge_one(case: str, png: Path, judge: str) -> None:
    dest = png.with_name(f"{png.stem}__judge__{judge}.json")
    if dest.exists():
        return
    spec = json.loads((png.parent / "_spec.json").read_text())
    prompt = JUDGE_PROMPT.format(spec=json.dumps(spec, indent=1))
    try:
        text, cost, _ = call_text(judge, prompt, "judge", case, effort="low" if "claude" in judge else None,
                                  image_png=_downscale(png.read_bytes()), max_tokens=8000)
        scores = json.loads(_strip_json_fences(text))
    except Exception as exc:
        scores, cost = {"error": str(exc)[:300]}, 0.0
    dest.write_text(json.dumps({"judge": judge, "cost": cost, **scores}, indent=2))
    print(f"  judged {case}/{png.stem} by {judge}")


def stage_judge(args) -> None:
    jobs = [(case, png, j) for case in CASE_NAMES
            for png in sorted((RESULTS / "render" / case).glob("*.png")) for j in JUDGES]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda a: judge_one(*a), jobs))


# ── Stage 4: report ──────────────────────────────────────────────────────────

CRITERIA = ["text_accuracy", "completeness", "logo_accuracy", "hierarchy", "aesthetics", "publishable"]


def stage_report(_args) -> None:
    rows: dict[str, dict] = {}
    for case in CASE_NAMES:
        for meta_path in (RESULTS / "render" / case).glob("*.json"):
            if "__judge__" in meta_path.name or meta_path.name.startswith("_"):
                continue
            meta = json.loads(meta_path.read_text())
            r = rows.setdefault(meta["label"], {"cost": [], "secs": [], "ok": 0, "n": 0,
                                                **{c: [] for c in CRITERIA}, "by_judge": {}})
            r["n"] += 1
            r["ok"] += bool(meta.get("ok"))
            r["cost"].append(meta.get("cost", 0))
            r["secs"].append(meta.get("seconds", 0))
            for jf in meta_path.parent.glob(f"{meta['label']}__judge__*.json"):
                j = json.loads(jf.read_text())
                if "error" in j:
                    continue
                for c in CRITERIA:
                    r[c].append(float(j[c]))
                r["by_judge"].setdefault(j["judge"], []).append(float(j["publishable"]))

    def avg(xs):
        return sum(xs) / len(xs) if xs else float("nan")

    lines = ["| Renderer | ok | $/img | s/img | " + " | ".join(CRITERIA) + " | mean | pub (gem / claude) |",
             "|" + "---|" * (len(CRITERIA) + 6)]
    ranked = sorted(rows.items(), key=lambda kv: -avg([avg(kv[1][c]) for c in CRITERIA]))
    for label, r in ranked:
        means = [avg(r[c]) for c in CRITERIA]
        bj = r["by_judge"]
        lines.append(f"| {label} | {r['ok']}/{r['n']} | {avg(r['cost']):.3f} | {avg(r['secs']):.0f} | "
                     + " | ".join(f"{m:.1f}" for m in means)
                     + f" | **{avg(means):.2f}** | {avg(bj.get(JUDGES[0], [])):.1f} / {avg(bj.get(JUDGES[1], [])):.1f} |")

    s_lines = ["| Structurer | input | ok | $/call (mean) | s | layers | items |", "|---|---|---|---|---|---|---|"]
    by_label: dict[str, list] = {}
    for f in sorted((RESULTS / "structure").glob("*.json")):
        d = json.loads(f.read_text())
        by_label.setdefault(d["label"], []).append(d)
    for label, ds in by_label.items():
        oks = [d for d in ds if d["ok"]]
        lay = avg([len(d["data"].get("layers", [])) for d in oks])
        items = avg([sum(len(l.get("items", [])) for l in d["data"].get("layers", [])) for d in oks])
        s_lines.append(f"| {label} | {ds[0]['input']} | {len(oks)}/{len(ds)} | {avg([d['cost'] for d in ds]):.4f} | "
                       f"{avg([d['seconds'] for d in ds]):.0f} | {lay:.1f} | {items:.1f} |")

    spend = {v: spent(v) for v in CAPS}
    out = ["# Benchmark summary", "", f"Spend: Anthropic ${spend['anthropic']:.3f} · Gemini ${spend['gemini']:.3f}",
           "", "## Rendering (mean of 3 cases × 2 blind judges)", *lines, "", "## Structuring", *s_lines]
    (RESULTS / "summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


def main() -> None:
    _load_env()
    RESULTS.mkdir(exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["structure", "render", "judge", "report", "spend"])
    ap.add_argument("--source", default="claude-opus-5-5", help="structure label used as render spec")
    ap.add_argument("--only", nargs="*", help="renderer labels to run")
    ap.add_argument("--hybrid", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    if args.stage == "spend":
        print({v: round(spent(v), 4) for v in CAPS})
        return
    {"structure": stage_structure, "render": stage_render,
     "judge": stage_judge, "report": stage_report}[args.stage](args)


if __name__ == "__main__":
    main()
