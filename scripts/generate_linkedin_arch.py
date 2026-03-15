#!/usr/bin/env python3
"""
Infographic Skill — LinkedIn Architecture Diagram Generator

Produces professional, colorful system architecture diagrams optimized for
LinkedIn posts. Style inspired by the Kubernetes architecture diagram format:
bold titles, color-coded component groups, dashed arrows, clean layout.

Usage:
    # From a pre-built arch.json (output of parse_context.py):
    python generate_linkedin_arch.py --config arch.json --output arch.png

    # Quick inline mode:
    python generate_linkedin_arch.py \
        --title "My SaaS Architecture" \
        --layers "Frontend:React,Next.js|Backend:FastAPI,Celery|Database:PostgreSQL,Redis|Cloud:AWS S3,CloudFront" \
        --output arch.png
"""

import argparse
import json
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ---------------------------------------------------------------------------
# LinkedIn format constants
# ---------------------------------------------------------------------------

LINKEDIN_W = 1080   # px
LINKEDIN_H = 1080   # px  (square — best for feed)
LINKEDIN_DPI = 150

TITLE_BG   = "#0A2540"   # dark navy — high contrast for bold title
TITLE_FG   = "#FFFFFF"
FOOTER_BG  = "#0A2540"
ACCENT     = "#2D9CDB"   # LinkedIn blue

# ---------------------------------------------------------------------------
# Palette for component groups (same as parse_context.py but standalone)
# ---------------------------------------------------------------------------

GROUP_STYLES = {
    "Frontend":       {"bg": "#DBEAFE", "border": "#1D4ED8", "title_bg": "#1D4ED8", "title_fg": "#FFF"},
    "Mobile":         {"bg": "#EDE9FE", "border": "#7C3AED", "title_bg": "#7C3AED", "title_fg": "#FFF"},
    "Backend / API":  {"bg": "#FEF3C7", "border": "#D97706", "title_bg": "#D97706", "title_fg": "#FFF"},
    "Backend":        {"bg": "#FEF3C7", "border": "#D97706", "title_bg": "#D97706", "title_fg": "#FFF"},
    "Database":       {"bg": "#DCFCE7", "border": "#16A34A", "title_bg": "#16A34A", "title_fg": "#FFF"},
    "Auth":           {"bg": "#FEF9C3", "border": "#CA8A04", "title_bg": "#CA8A04", "title_fg": "#FFF"},
    "Queue / Events": {"bg": "#F3E8FF", "border": "#9333EA", "title_bg": "#9333EA", "title_fg": "#FFF"},
    "Storage":        {"bg": "#E0E7FF", "border": "#4338CA", "title_bg": "#4338CA", "title_fg": "#FFF"},
    "Cloud Services": {"bg": "#CFFAFE", "border": "#0891B2", "title_bg": "#0891B2", "title_fg": "#FFF"},
    "Infrastructure": {"bg": "#FFE4E6", "border": "#E11D48", "title_bg": "#E11D48", "title_fg": "#FFF"},
    "Monitoring":     {"bg": "#FFF7ED", "border": "#C2410C", "title_bg": "#C2410C", "title_fg": "#FFF"},
    "CI/CD":          {"bg": "#F1F5F9", "border": "#475569", "title_bg": "#475569", "title_fg": "#FFF"},
    "AI / ML":        {"bg": "#ECFDF5", "border": "#059669", "title_bg": "#059669", "title_fg": "#FFF"},
    "Other":          {"bg": "#F5F5F5", "border": "#6B7280", "title_bg": "#6B7280", "title_fg": "#FFF"},
}

DEFAULT_STYLE = {"bg": "#F5F5F5", "border": "#6B7280", "title_bg": "#6B7280", "title_fg": "#FFF"}


def get_style(label: str) -> dict:
    # Fuzzy match
    for key, val in GROUP_STYLES.items():
        if key.lower() in label.lower() or label.lower() in key.lower():
            return val
    return DEFAULT_STYLE


# ---------------------------------------------------------------------------
# Layout engine
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int = 12) -> str:
    return "\n".join(textwrap.wrap(text, width))


def compute_layout(layers: list[dict], canvas_w: float, canvas_h: float,
                   margin: float, title_h: float, footer_h: float):
    """
    Divide the canvas below the title and above the footer into a grid of
    layer boxes. Last row items are centered if the row is not full.
    Returns a list of (layer, x, y, w, h) in data coordinates.
    """
    n = len(layers)
    if n == 0:
        return []

    usable_h = canvas_h - title_h - footer_h - 2 * margin
    usable_w = canvas_w - 2 * margin
    y_start  = footer_h + margin

    if n <= 2:
        cols, rows = n, 1
    elif n <= 4:
        cols, rows = 2, 2
    elif n <= 6:
        cols, rows = 3, 2
    elif n <= 9:
        cols, rows = 3, 3
    else:
        cols = 4
        rows = (n + cols - 1) // cols

    gap    = margin * 0.6
    cell_w = (usable_w - (cols - 1) * gap) / cols
    cell_h = (usable_h - (rows - 1) * gap) / rows

    positions = []
    for row_idx in range(rows):
        row_start  = row_idx * cols
        row_layers = layers[row_start: row_start + cols]
        n_in_row   = len(row_layers)
        data_row   = rows - 1 - row_idx   # 0=bottom, rows-1=top in data coords
        y = y_start + data_row * (cell_h + gap)

        row_total_w = n_in_row * cell_w + (n_in_row - 1) * gap
        x_offset    = margin + (usable_w - row_total_w) / 2

        for col_idx, layer in enumerate(row_layers):
            x = x_offset + col_idx * (cell_w + gap)
            positions.append((layer, x, y, cell_w, cell_h))

    return positions


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def draw_rounded_box(ax, x, y, w, h, bg, border, lw=2.5, radius=0.012):
    """Draw a rounded rectangle in axis data coordinates."""
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=bg,
        edgecolor=border,
        linewidth=lw,
        zorder=2,
        clip_on=False,
    )
    ax.add_patch(rect)


def draw_title_bar(ax, x, y, w, h, bg, text, fg="#FFF", fontsize=9):
    """Colored title bar at top of a group box."""
    rect = FancyBboxPatch(
        (x, y + h - 0.035), w, 0.035,
        boxstyle="round,pad=0.005",
        facecolor=bg,
        edgecolor=bg,
        linewidth=0,
        zorder=3,
        clip_on=False,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, y + h - 0.018,
        text, ha="center", va="center",
        fontsize=fontsize, fontweight="bold", color=fg,
        zorder=4, clip_on=False,
    )


def draw_component_chip(ax, x, y, w, h, label, border_color, text_color="#212121"):
    """Draw a single component chip inside a group box."""
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.006",
        facecolor="#FFFFFF",
        edgecolor=border_color,
        linewidth=1.5,
        zorder=4,
        clip_on=False,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, y + h / 2,
        _wrap(label, 11),
        ha="center", va="center",
        fontsize=7.5, color=text_color,
        fontweight="bold",
        zorder=5, clip_on=False,
        multialignment="center",
    )


def draw_dashed_arrow(ax, x0, y0, x1, y1, color="#9E9E9E"):
    """Draw a dashed directional arrow between two points."""
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=2.0,
            linestyle=(0, (6, 3)),   # custom dash: 6pt on, 3pt off
            mutation_scale=14,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=1,
    )


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_architecture(config: dict, output_path: str) -> Path:
    layers      = config.get("layers", [])
    title       = config.get("title", "System Architecture")
    subtitle    = config.get("subtitle", "")
    author      = config.get("author", "")
    cta         = config.get("linkedin_cta", "Follow for more software architecture content")
    connections = config.get("connections", [])

    # ── Canvas setup ────────────────────────────────────────────────────────
    dpi    = LINKEDIN_DPI
    w_in   = LINKEDIN_W / dpi
    h_in   = LINKEDIN_H / dpi
    fig, ax = plt.subplots(1, 1, figsize=(w_in, h_in), dpi=dpi)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    margin     = 0.035
    title_h    = 0.14
    footer_h   = 0.075
    canvas_h   = 1.0
    canvas_w   = 1.0

    # ── Title bar ───────────────────────────────────────────────────────────
    title_rect = FancyBboxPatch(
        (0, 1 - title_h), 1, title_h,
        boxstyle="square,pad=0",
        facecolor=TITLE_BG, edgecolor=TITLE_BG, linewidth=0, zorder=5,
    )
    ax.add_patch(title_rect)

    # Accent line under title
    ax.add_patch(plt.Rectangle((0, 1 - title_h), 1, 0.004,
                                color=ACCENT, zorder=6))

    ax.text(0.5, 1 - title_h / 2 + 0.02, title,
            ha="center", va="center", fontsize=17, fontweight="bold",
            color=TITLE_FG, zorder=6,
            path_effects=[pe.withStroke(linewidth=1, foreground=TITLE_BG)])

    if subtitle:
        ax.text(0.5, 1 - title_h + 0.022, subtitle,
                ha="center", va="bottom", fontsize=9, color="#94A3B8", zorder=6)

    # ── Footer bar ──────────────────────────────────────────────────────────
    footer_rect = FancyBboxPatch(
        (0, 0), 1, footer_h,
        boxstyle="square,pad=0",
        facecolor=FOOTER_BG, edgecolor=FOOTER_BG, linewidth=0, zorder=5,
    )
    ax.add_patch(footer_rect)
    ax.add_patch(plt.Rectangle((0, footer_h - 0.004), 1, 0.004,
                                color=ACCENT, zorder=6))

    footer_text = cta
    if author:
        footer_text = f"{author}  |  {cta}"
    ax.text(0.5, footer_h / 2, footer_text,
            ha="center", va="center", fontsize=8.5,
            color="#E2E8F0", zorder=6)

    # ── Compute layer grid ──────────────────────────────────────────────────
    positions = compute_layout(layers, canvas_w, canvas_h, margin, title_h, footer_h)

    # Store box boundaries per category for proper edge-to-edge arrow routing
    boxes = {}       # category → (x, y, w, h)
    centers = {}     # category → (cx, cy)

    for layer, bx, by, bw, bh in positions:
        label    = layer.get("label", "")
        items    = layer.get("items", [])
        style    = get_style(label)
        category = layer.get("category", "other")

        # Outer group box
        draw_rounded_box(ax, bx, by, bw, bh,
                         bg=style["bg"], border=style["border"], lw=2)

        # Title bar
        draw_title_bar(ax, bx, by, bw, bh,
                       bg=style["title_bg"], text=label,
                       fg=style["title_fg"], fontsize=8.5)

        # Component chips inside
        n_items = len(items)
        if n_items > 0:
            inner_pad = 0.012
            top_pad   = 0.042   # space for title bar
            inner_w   = bw - 2 * inner_pad
            inner_h   = bh - top_pad - inner_pad

            if n_items <= 2:
                chip_cols = n_items
            elif n_items <= 4:
                chip_cols = 2
            else:
                chip_cols = 3

            chip_rows  = (n_items + chip_cols - 1) // chip_cols
            chip_gap   = 0.008
            chip_w     = (inner_w - (chip_cols - 1) * chip_gap) / chip_cols
            chip_h     = min(
                (inner_h - (chip_rows - 1) * chip_gap) / chip_rows,
                0.055
            )
            total_chips_h = chip_rows * chip_h + (chip_rows - 1) * chip_gap
            chips_y_start = by + inner_pad + (inner_h - total_chips_h) / 2

            for j, item_name in enumerate(items[:chip_cols * chip_rows]):
                ci = j % chip_cols
                ri = j // chip_cols
                cx = bx + inner_pad + ci * (chip_w + chip_gap)
                cy = chips_y_start + (chip_rows - 1 - ri) * (chip_h + chip_gap)
                draw_component_chip(ax, cx, cy, chip_w, chip_h,
                                    item_name, style["border"])

        boxes[category]   = (bx, by, bw, bh)
        centers[category] = (bx + bw / 2, by + bh / 2)

    # ── Draw connection arrows (edge-to-edge, above boxes) ──────────────────
    cat_to_layer = {l.get("category"): l for l in layers}
    for conn in connections:
        src_cat = conn.get("from")
        dst_cat = conn.get("to")
        if src_cat not in boxes or dst_cat not in boxes:
            continue

        sx_b, sy_b, sw, sh = boxes[src_cat]
        dx_b, dy_b, dw, dh = boxes[dst_cat]
        scx, scy = sx_b + sw / 2, sy_b + sh / 2
        dcx, dcy = dx_b + dw / 2, dy_b + dh / 2

        src_style = get_style(cat_to_layer[src_cat].get("label", ""))
        arrow_color = src_style["border"]

        # Choose which edges to connect based on relative position
        dy_diff = dcy - scy
        dx_diff = dcx - scx

        if abs(dy_diff) >= abs(dx_diff):
            # Vertical connection — use top/bottom edges
            if dy_diff > 0:   # dst is above src
                x0, y0 = scx, sy_b + sh
                x1, y1 = dcx, dy_b
            else:             # dst is below src
                x0, y0 = scx, sy_b
                x1, y1 = dcx, dy_b + dh
        else:
            # Horizontal connection — use left/right edges
            if dx_diff > 0:   # dst is to the right
                x0, y0 = sx_b + sw, scy
                x1, y1 = dx_b,      dcy
            else:             # dst is to the left
                x0, y0 = sx_b,      scy
                x1, y1 = dx_b + dw, dcy

        ax.annotate(
            "", xy=(x1, y1), xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=arrow_color,
                lw=1.8,
                linestyle=(0, (5, 3)),
                mutation_scale=12,
                connectionstyle="arc3,rad=0.0",
            ),
            zorder=6,
        )

    # ── Subtle grid background ───────────────────────────────────────────────
    for xi in np.arange(0, 1.01, 0.05):
        ax.axvline(xi, color="#E2E8F0", lw=0.3, zorder=0, alpha=0.5)
    for yi in np.arange(0, 1.01, 0.05):
        ax.axhline(yi, color="#E2E8F0", lw=0.3, zorder=0, alpha=0.5)

    # ── Save ─────────────────────────────────────────────────────────────────
    out = Path(output_path)
    fig.savefig(out, dpi=dpi, bbox_inches="tight",
                facecolor="#F8FAFC", pad_inches=0)
    plt.close(fig)

    print(f"✅ LinkedIn architecture diagram → {out.resolve()}")
    print(f"   {LINKEDIN_W}×{LINKEDIN_H}px @ {dpi}dpi  |  {len(layers)} component groups")
    return out


# ---------------------------------------------------------------------------
# Quick-build from --layers string
# ---------------------------------------------------------------------------

def layers_from_string(layers_str: str) -> list[dict]:
    """Parse 'Frontend:React,Next.js|Backend:FastAPI,Celery' into layers."""
    GROUP_STYLES_LABELS = {v: k for k, v in {
        "frontend": "Frontend", "backend": "Backend / API",
        "database": "Database", "cloud": "Cloud Services",
        "auth": "Auth", "queue": "Queue / Events",
        "storage": "Storage", "monitoring": "Monitoring",
        "ci_cd": "CI/CD", "ai_ml": "AI / ML",
        "infra": "Infrastructure", "mobile": "Mobile",
    }.items()}

    layers = []
    for part in layers_str.split("|"):
        if ":" in part:
            label, items_str = part.split(":", 1)
            label = label.strip()
            items = [i.strip() for i in items_str.split(",") if i.strip()]

            # guess category
            cat = GROUP_STYLES_LABELS.get(label, "other")
            style = get_style(label)

            layers.append({
                "label": label,
                "category": cat,
                "items": items,
                "bg": style["bg"],
                "border": style["border"],
                "label_color": style.get("title_fg", "#FFF"),
            })
    return layers


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn architecture diagram generator")
    parser.add_argument("--config",   help="Path to arch.json from parse_context.py")
    parser.add_argument("--layers",   help="Quick layers string: 'Frontend:React|Backend:FastAPI'")
    parser.add_argument("--title",    default="System Architecture", help="Diagram title")
    parser.add_argument("--subtitle", default="", help="Subtitle")
    parser.add_argument("--author",   default="", help="Author name for footer")
    parser.add_argument("--cta",      default="Follow for more software architecture content")
    parser.add_argument("--output",   default="linkedin_arch.png")
    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            config = json.load(f)
        if args.title != "System Architecture":
            config["title"] = args.title
        if args.author:
            config["author"] = args.author
        if args.cta:
            config["linkedin_cta"] = args.cta
    elif args.layers:
        layers = layers_from_string(args.layers)
        config = {
            "title":        args.title,
            "subtitle":     args.subtitle,
            "author":       args.author,
            "linkedin_cta": args.cta,
            "layers":       layers,
            "connections":  [],
        }
    else:
        print("❌  Provide either --config arch.json or --layers 'Frontend:React|Backend:FastAPI'")
        raise SystemExit(1)

    render_architecture(config, args.output)
