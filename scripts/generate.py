#!/usr/bin/env python3
"""
Infographic Skill — Core Generation Engine
Provides canvas setup, typography, color palettes, and layout primitives
for building professional infographics with matplotlib.

Usage:
    python generate.py --layout dashboard --output out.png --width 1080 --height 1350 --dpi 150
    python generate.py --layout vertical-story --output timeline.png

For custom data, import this module and use the InfographicCanvas class.
"""

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ---------------------------------------------------------------------------
# COLOR PALETTES
# ---------------------------------------------------------------------------

PALETTES = {
    "modern-blue": {
        "primary":    "#1A73E8",
        "secondary":  "#0D47A1",
        "accent":     "#FF6D00",
        "neutral":    "#5F6368",
        "light":      "#E8F0FE",
        "background": "#FFFFFF",
        "text":       "#202124",
    },
    "dark-professional": {
        "primary":    "#4FC3F7",
        "secondary":  "#81C784",
        "accent":     "#FFD54F",
        "neutral":    "#90A4AE",
        "light":      "#263238",
        "background": "#1A1A2E",
        "text":       "#ECEFF1",
    },
    "warm-report": {
        "primary":    "#E53935",
        "secondary":  "#FB8C00",
        "accent":     "#43A047",
        "neutral":    "#757575",
        "light":      "#FFF8E1",
        "background": "#FAFAFA",
        "text":       "#212121",
    },
    "accessible": {
        "primary":    "#0077BB",
        "secondary":  "#33BBEE",
        "accent":     "#EE7733",
        "neutral":    "#BBBBBB",
        "light":      "#F5F5F5",
        "background": "#FFFFFF",
        "text":       "#111111",
    },
}

DEFAULT_PALETTE = "modern-blue"


# ---------------------------------------------------------------------------
# INFOGRAPHIC CANVAS
# ---------------------------------------------------------------------------

class InfographicCanvas:
    """
    High-level canvas for building infographics.

    Example
    -------
    canvas = InfographicCanvas(1080, 1920, dpi=150, palette="modern-blue")
    canvas.add_header("My Infographic", subtitle="A subtitle line")
    canvas.add_kpi_row(
        kpis=[("$2.4M", "Revenue", "+18%"), ("72", "NPS", ""), ("2.1%", "Churn", "")]
    )
    canvas.save("out.png")
    """

    def __init__(
        self,
        width_px: int = 1080,
        height_px: int = 1920,
        dpi: int = 150,
        palette: str = DEFAULT_PALETTE,
        bg_color: str | None = None,
    ):
        self.width_px = width_px
        self.height_px = height_px
        self.dpi = dpi
        self.colors = PALETTES.get(palette, PALETTES[DEFAULT_PALETTE]).copy()
        if bg_color:
            self.colors["background"] = bg_color

        # Convert px to inches for matplotlib
        w_in = width_px / dpi
        h_in = height_px / dpi

        self.fig = plt.figure(figsize=(w_in, h_in), dpi=dpi, facecolor=self.colors["background"])
        self._cursor_y = 0.98  # normalized (0=bottom, 1=top)
        self._margin = 0.05   # left/right margin fraction

    # ------------------------------------------------------------------
    # Typography helpers
    # ------------------------------------------------------------------

    def _text(self, ax, x, y, text, size=14, color=None, weight="normal",
              ha="left", va="top", wrap_width=None, **kwargs):
        color = color or self.colors["text"]
        if wrap_width:
            text = "\n".join(textwrap.wrap(text, wrap_width))
        return ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
                       ha=ha, va=va, transform=ax.transAxes,
                       fontfamily="DejaVu Sans", **kwargs)

    # ------------------------------------------------------------------
    # Section: Full-width header
    # ------------------------------------------------------------------

    def add_header(
        self,
        title: str,
        subtitle: str = "",
        source: str = "",
        accent_bar: bool = True,
    ) -> "InfographicCanvas":
        """Add a bold hero header section."""
        ax = self.fig.add_axes([self._margin, 0.90, 1 - 2 * self._margin, 0.09])
        ax.set_axis_off()
        ax.set_facecolor(self.colors["background"])

        if accent_bar:
            ax.axhline(y=0.0, xmin=0, xmax=0.15, color=self.colors["primary"],
                       linewidth=4, solid_capstyle="round")

        ax.text(0, 0.9, title, fontsize=28, fontweight="bold",
                color=self.colors["text"], va="top", ha="left",
                transform=ax.transAxes, fontfamily="DejaVu Sans")

        if subtitle:
            ax.text(0, 0.45, subtitle, fontsize=13, color=self.colors["neutral"],
                    va="top", ha="left", transform=ax.transAxes)

        if source:
            ax.text(1, 0.0, f"Source: {source}", fontsize=8,
                    color=self.colors["neutral"], va="bottom", ha="right",
                    transform=ax.transAxes, style="italic")

        return self

    # ------------------------------------------------------------------
    # Section: KPI Row
    # ------------------------------------------------------------------

    def add_kpi_row(
        self,
        kpis: list[tuple[str, str, str]],  # (value, label, delta)
        top: float = 0.80,
        height: float = 0.10,
    ) -> "InfographicCanvas":
        """Add a row of bold KPI boxes. kpis = [(value, label, delta), ...]"""
        n = len(kpis)
        w = (1 - 2 * self._margin - 0.02 * (n - 1)) / n

        for i, (value, label, delta) in enumerate(kpis):
            left = self._margin + i * (w + 0.02)
            ax = self.fig.add_axes([left, top, w, height])
            ax.set_axis_off()

            rect = FancyBboxPatch((0, 0), 1, 1,
                                  boxstyle="round,pad=0.02",
                                  facecolor=self.colors["light"],
                                  edgecolor=self.colors["primary"],
                                  linewidth=1.5,
                                  transform=ax.transAxes,
                                  clip_on=False)
            ax.add_patch(rect)

            ax.text(0.5, 0.75, value, fontsize=26, fontweight="bold",
                    color=self.colors["primary"], ha="center", va="center",
                    transform=ax.transAxes)
            ax.text(0.5, 0.35, label, fontsize=10, color=self.colors["neutral"],
                    ha="center", va="center", transform=ax.transAxes)

            if delta:
                color = "#43A047" if delta.startswith("+") else "#E53935"
                ax.text(0.5, 0.10, delta, fontsize=9, color=color,
                        ha="center", va="bottom", transform=ax.transAxes,
                        fontweight="bold")

        return self

    # ------------------------------------------------------------------
    # Section: Horizontal Bar Chart
    # ------------------------------------------------------------------

    def add_bar_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str = "",
        unit: str = "",
        top: float = 0.60,
        height: float = 0.18,
        color_override: str | None = None,
    ) -> "InfographicCanvas":
        """Horizontal bar chart section."""
        ax = self.fig.add_axes([self._margin, top, 1 - 2 * self._margin, height])

        bar_color = color_override or self.colors["primary"]
        y_pos = range(len(labels))
        bars = ax.barh(list(y_pos), values, color=bar_color, height=0.6,
                       edgecolor="none")

        # Direct labels
        for bar, val in zip(bars, values):
            ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val}{unit}", va="center", ha="left", fontsize=9,
                    color=self.colors["text"])

        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=10, color=self.colors["text"])
        ax.set_xlim(0, max(values) * 1.15)
        ax.invert_yaxis()
        ax.set_facecolor(self.colors["background"])
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="x", colors=self.colors["neutral"], labelsize=8)
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_tick_params(pad=2)

        if title:
            ax.set_title(title, fontsize=12, fontweight="bold",
                         color=self.colors["text"], loc="left", pad=8)

        return self

    # ------------------------------------------------------------------
    # Section: Donut Chart
    # ------------------------------------------------------------------

    def add_donut(
        self,
        values: list[float],
        labels: list[str],
        title: str = "",
        center_text: str = "",
        top: float = 0.38,
        height: float = 0.20,
    ) -> "InfographicCanvas":
        """Donut chart section (max 5 slices)."""
        assert len(values) <= 5, "Use a bar chart for >5 categories"

        colors = [self.colors["primary"], self.colors["secondary"],
                  self.colors["accent"], self.colors["neutral"], "#9E9E9E"]

        ax = self.fig.add_axes([self._margin + 0.1, top, 0.4, height], aspect="equal")
        wedges, _ = ax.pie(values, colors=colors[:len(values)],
                           startangle=90, wedgeprops=dict(width=0.5))
        if center_text:
            ax.text(0, 0, center_text, ha="center", va="center",
                    fontsize=14, fontweight="bold", color=self.colors["text"])

        # Legend on the right
        legend_ax = self.fig.add_axes([self._margin + 0.52, top + 0.04, 0.38, height - 0.08])
        legend_ax.set_axis_off()
        total = sum(values)
        for j, (label, val, color) in enumerate(zip(labels, values, colors)):
            y = 1 - j * (1 / len(labels))
            legend_ax.add_patch(mpatches.Rectangle((0, y - 0.06), 0.08, 0.09,
                                                    color=color, transform=legend_ax.transAxes))
            legend_ax.text(0.12, y - 0.01, f"{label}  {val/total:.0%}",
                           va="center", ha="left", fontsize=9,
                           color=self.colors["text"], transform=legend_ax.transAxes)

        if title:
            ax.set_title(title, fontsize=12, fontweight="bold",
                         color=self.colors["text"], pad=10)

        return self

    # ------------------------------------------------------------------
    # Section: Divider / callout text
    # ------------------------------------------------------------------

    def add_callout(
        self,
        text: str,
        top: float = 0.30,
        height: float = 0.07,
    ) -> "InfographicCanvas":
        """Bold pull-quote / callout box."""
        ax = self.fig.add_axes([self._margin, top, 1 - 2 * self._margin, height])
        ax.set_axis_off()
        rect = FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.03",
                              facecolor=self.colors["primary"],
                              edgecolor="none",
                              transform=ax.transAxes, clip_on=False)
        ax.add_patch(rect)
        ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=13,
                fontweight="bold", color="#FFFFFF", transform=ax.transAxes,
                wrap=True)
        return self

    # ------------------------------------------------------------------
    # Section: Process Flow (horizontal steps)
    # ------------------------------------------------------------------

    def add_process_flow(
        self,
        steps: list[tuple[str, str]],  # (number/icon, description)
        top: float = 0.15,
        height: float = 0.12,
    ) -> "InfographicCanvas":
        """Numbered horizontal step flow."""
        n = len(steps)
        ax = self.fig.add_axes([self._margin, top, 1 - 2 * self._margin, height])
        ax.set_axis_off()
        ax.set_xlim(0, n)
        ax.set_ylim(0, 1)

        step_w = 1 / n
        for i, (num, desc) in enumerate(steps):
            cx = (i + 0.5) * step_w / step_w * (n / n)  # normalize
            cx = (i + 0.5) / n

            # Circle
            circle = plt.Circle((cx, 0.72), 0.06, color=self.colors["primary"],
                                 transform=ax.transData, zorder=3)
            ax.add_patch(circle)
            ax.text(cx, 0.72, str(num), ha="center", va="center", fontsize=11,
                    fontweight="bold", color="#FFFFFF", zorder=4)

            # Label
            wrapped = "\n".join(textwrap.wrap(desc, 12))
            ax.text(cx, 0.30, wrapped, ha="center", va="center", fontsize=8,
                    color=self.colors["text"], multialignment="center")

            # Arrow between steps
            if i < n - 1:
                ax.annotate("", xy=((i + 1) / n - 0.02, 0.72),
                            xytext=((i + 0.5) / n + 0.07, 0.72),
                            arrowprops=dict(arrowstyle="->",
                                           color=self.colors["neutral"],
                                           lw=1.5))
        return self

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    def add_footer(self, text: str = "") -> "InfographicCanvas":
        ax = self.fig.add_axes([0, 0, 1, 0.04])
        ax.set_axis_off()
        ax.set_facecolor(self.colors["primary"])
        rect = plt.Rectangle((0, 0), 1, 1, color=self.colors["primary"],
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=9,
                color="#FFFFFF", transform=ax.transAxes)
        return self

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, path: str) -> Path:
        out = Path(path)
        self.fig.savefig(out, dpi=self.dpi, bbox_inches="tight",
                         facecolor=self.colors["background"])
        plt.close(self.fig)
        print(f"✅ Infographic saved → {out.resolve()}")
        print(f"   Size: {self.width_px}×{self.height_px}px @ {self.dpi}dpi")
        return out


# ---------------------------------------------------------------------------
# CLI demo — run with: python generate.py --demo
# ---------------------------------------------------------------------------

def _demo():
    canvas = InfographicCanvas(1080, 1350, dpi=150, palette="modern-blue")
    canvas.add_header(
        "Q3 Performance Report",
        subtitle="Key metrics for the period July – September 2024",
        source="Internal Analytics"
    )
    canvas.add_kpi_row(
        kpis=[("$2.4M", "Revenue", "+18%"), ("72", "NPS", "+5pts"), ("2.1%", "Churn", "-0.3%")],
        top=0.78, height=0.11
    )
    canvas.add_bar_chart(
        labels=["Product A", "Product B", "Product C", "Product D"],
        values=[840, 620, 540, 400],
        title="Revenue by Product ($K)",
        unit="K",
        top=0.57,
        height=0.18
    )
    canvas.add_donut(
        values=[45, 30, 15, 10],
        labels=["Enterprise", "SMB", "Startup", "Other"],
        title="Customer Segments",
        center_text="340\nNew",
        top=0.33,
        height=0.21
    )
    canvas.add_callout(
        "🎯  Enterprise segment grew 42% YoY — accelerate investment",
        top=0.27, height=0.05
    )
    canvas.add_process_flow(
        steps=[("1", "Lead Gen"), ("2", "Discovery"), ("3", "Demo"),
               ("4", "Proposal"), ("5", "Close")],
        top=0.10,
        height=0.15
    )
    canvas.add_footer("© 2024 Acme Corp  |  Confidential")
    canvas.save("demo_infographic.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Infographic generator")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo")
    parser.add_argument("--layout", default="dashboard")
    parser.add_argument("--output", default="infographic.png")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1350)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--palette", default="modern-blue",
                        choices=list(PALETTES.keys()))
    args = parser.parse_args()

    if args.demo:
        _demo()
    else:
        print("ℹ️  Import InfographicCanvas from this module to build custom infographics.")
        print(f"   Available palettes: {', '.join(PALETTES.keys())}")
        print(f"   Run with --demo to generate a sample output.")
