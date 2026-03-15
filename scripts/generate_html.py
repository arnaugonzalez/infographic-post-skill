#!/usr/bin/env python3
"""
Infographic Skill — Interactive HTML Generator
Produces self-contained HTML files with Chart.js visualizations.
No external dependencies at runtime — all libraries are CDN-inlined at build time.

Usage:
    # Called by Claude with a JSON config file
    python generate_html.py --config config.json --output infographic.html
"""

import argparse
import json
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  /* ─── Reset & Base ─────────────────────────────────────── */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: {bg};
    color: {text};
    min-height: 100vh;
    padding: 0;
  }}

  /* ─── Infographic Container ─────────────────────────────── */
  .infographic {{
    max-width: 1080px;
    margin: 0 auto;
    background: {bg};
    padding: 48px 40px 32px;
  }}

  /* ─── Header ────────────────────────────────────────────── */
  .header {{
    border-left: 6px solid {primary};
    padding-left: 16px;
    margin-bottom: 40px;
  }}
  .header h1 {{
    font-size: 2.2rem;
    font-weight: 800;
    color: {text};
    line-height: 1.15;
  }}
  .header .subtitle {{
    font-size: 1rem;
    color: {neutral};
    margin-top: 6px;
  }}

  /* ─── KPI Grid ──────────────────────────────────────────── */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin-bottom: 40px;
  }}
  .kpi-card {{
    background: {light};
    border: 1.5px solid {primary};
    border-radius: 12px;
    padding: 20px 16px 16px;
    text-align: center;
  }}
  .kpi-card .value {{
    font-size: 2.2rem;
    font-weight: 800;
    color: {primary};
    line-height: 1;
  }}
  .kpi-card .label {{
    font-size: 0.8rem;
    color: {neutral};
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .kpi-card .delta {{
    font-size: 0.85rem;
    font-weight: 700;
    margin-top: 6px;
  }}
  .kpi-card .delta.positive {{ color: #43A047; }}
  .kpi-card .delta.negative {{ color: #E53935; }}

  /* ─── Charts ────────────────────────────────────────────── */
  .chart-section {{
    margin-bottom: 40px;
  }}
  .chart-section h2 {{
    font-size: 1.1rem;
    font-weight: 700;
    color: {text};
    margin-bottom: 16px;
  }}
  .chart-container {{
    background: {bg};
    border-radius: 12px;
    padding: 16px;
    border: 1px solid {light};
  }}

  /* ─── Two-column layout ─────────────────────────────────── */
  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 40px;
  }}
  @media (max-width: 640px) {{
    .two-col {{ grid-template-columns: 1fr; }}
  }}

  /* ─── Callout ───────────────────────────────────────────── */
  .callout {{
    background: {primary};
    color: #fff;
    border-radius: 12px;
    padding: 20px 24px;
    font-size: 1.05rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 40px;
  }}

  /* ─── Process Flow ──────────────────────────────────────── */
  .process-flow {{
    display: flex;
    align-items: flex-start;
    gap: 0;
    margin-bottom: 40px;
    overflow-x: auto;
    padding-bottom: 8px;
  }}
  .process-step {{
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    min-width: 80px;
    position: relative;
    text-align: center;
  }}
  .process-step:not(:last-child)::after {{
    content: '';
    position: absolute;
    top: 20px;
    left: 60%;
    right: -40%;
    height: 2px;
    background: {neutral};
    z-index: 0;
  }}
  .step-circle {{
    width: 40px;
    height: 40px;
    background: {primary};
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.95rem;
    position: relative;
    z-index: 1;
    margin-bottom: 8px;
  }}
  .step-label {{
    font-size: 0.75rem;
    color: {neutral};
    max-width: 80px;
    line-height: 1.3;
  }}

  /* ─── Footer ────────────────────────────────────────────── */
  .footer {{
    background: {primary};
    margin: 0 -40px -32px;
    padding: 12px 40px;
    text-align: center;
    color: rgba(255,255,255,0.85);
    font-size: 0.8rem;
  }}
</style>
</head>
<body>
<div class="infographic">

  <!-- HEADER -->
  <div class="header">
    <h1>{title}</h1>
    <p class="subtitle">{subtitle}</p>
  </div>

  <!-- KPI CARDS — inject from config.kpis -->
  <div class="kpi-grid" id="kpi-grid"></div>

  <!-- CHARTS — inject from config.charts -->
  <div id="charts-container"></div>

  <!-- CALLOUT — inject from config.callout -->
  <div id="callout-container"></div>

  <!-- PROCESS FLOW — inject from config.steps -->
  <div id="flow-container"></div>

  <div class="footer">{footer}</div>
</div>

<script>
// ─── Config (injected) ────────────────────────────────────────────────────
const CONFIG = {config_json};

// ─── Colors ───────────────────────────────────────────────────────────────
const C = {{
  primary:   "{primary}",
  secondary: "{secondary}",
  accent:    "{accent}",
  neutral:   "{neutral}",
  light:     "{light}",
  text:      "{text}",
}};

// ─── KPI Cards ────────────────────────────────────────────────────────────
const kpiGrid = document.getElementById("kpi-grid");
(CONFIG.kpis || []).forEach((kpi) => {{
  const card = document.createElement("div");
  card.className = "kpi-card";
  const deltaClass = kpi.delta?.startsWith("+") ? "positive" : "negative";
  card.innerHTML = `
    <div class="value">${{kpi.value}}</div>
    <div class="label">${{kpi.label}}</div>
    ${{kpi.delta ? `<div class="delta ${{deltaClass}}">${{kpi.delta}}</div>` : ""}}
  `;
  kpiGrid.appendChild(card);
}});

// ─── Charts ───────────────────────────────────────────────────────────────
const chartsContainer = document.getElementById("charts-container");
(CONFIG.charts || []).forEach((chart, i) => {{
  const section = document.createElement("div");
  section.className = "chart-section";
  section.innerHTML = `<h2>${{chart.title}}</h2><div class="chart-container"><canvas id="chart-${{i}}"></canvas></div>`;
  chartsContainer.appendChild(section);

  const ctx = document.getElementById(`chart-${{i}}`).getContext("2d");
  const colors = [C.primary, C.secondary, C.accent, "#9E9E9E", "#78909C"];

  if (chart.type === "bar" || chart.type === "horizontalBar") {{
    new Chart(ctx, {{
      type: "bar",
      data: {{
        labels: chart.labels,
        datasets: [{{
          label: chart.dataset_label || "",
          data: chart.values,
          backgroundColor: C.primary,
          borderRadius: 6,
          borderSkipped: false,
        }}]
      }},
      options: {{
        indexAxis: chart.type === "horizontalBar" ? "y" : "x",
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, beginAtZero: true }},
          y: {{ grid: {{ display: chart.type !== "horizontalBar" }} }}
        }}
      }}
    }});
  }} else if (chart.type === "donut" || chart.type === "pie") {{
    new Chart(ctx, {{
      type: "doughnut",
      data: {{
        labels: chart.labels,
        datasets: [{{ data: chart.values, backgroundColor: colors.slice(0, chart.values.length), borderWidth: 0 }}]
      }},
      options: {{
        responsive: true,
        cutout: chart.type === "donut" ? "60%" : 0,
        plugins: {{ legend: {{ position: "right" }} }}
      }}
    }});
  }} else if (chart.type === "line") {{
    new Chart(ctx, {{
      type: "line",
      data: {{
        labels: chart.labels,
        datasets: [{{
          data: chart.values,
          borderColor: C.primary,
          backgroundColor: C.primary + "22",
          fill: true,
          tension: 0.4,
          pointRadius: 4,
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ y: {{ beginAtZero: false }} }}
      }}
    }});
  }}
}});

// ─── Callout ──────────────────────────────────────────────────────────────
if (CONFIG.callout) {{
  document.getElementById("callout-container").innerHTML =
    `<div class="callout">${{CONFIG.callout}}</div>`;
}}

// ─── Process Flow ─────────────────────────────────────────────────────────
if (CONFIG.steps && CONFIG.steps.length) {{
  const flow = document.createElement("div");
  flow.className = "process-flow";
  CONFIG.steps.forEach((step, i) => {{
    flow.innerHTML += `
      <div class="process-step">
        <div class="step-circle">${{i + 1}}</div>
        <div class="step-label">${{step}}</div>
      </div>`;
  }});
  document.getElementById("flow-container").appendChild(flow);
}}
</script>
</body>
</html>"""


def generate_html(config: dict, output_path: str) -> Path:
    """Generate a self-contained HTML infographic from a config dict."""
    palette_key = config.get("palette", "modern-blue")
    palettes = {
        "modern-blue": {
            "primary": "#1A73E8", "secondary": "#0D47A1", "accent": "#FF6D00",
            "neutral": "#5F6368", "light": "#E8F0FE", "bg": "#FFFFFF", "text": "#202124",
        },
        "dark-professional": {
            "primary": "#4FC3F7", "secondary": "#81C784", "accent": "#FFD54F",
            "neutral": "#90A4AE", "light": "#263238", "bg": "#1A1A2E", "text": "#ECEFF1",
        },
        "warm-report": {
            "primary": "#E53935", "secondary": "#FB8C00", "accent": "#43A047",
            "neutral": "#757575", "light": "#FFF8E1", "bg": "#FAFAFA", "text": "#212121",
        },
        "accessible": {
            "primary": "#0077BB", "secondary": "#33BBEE", "accent": "#EE7733",
            "neutral": "#BBBBBB", "light": "#F5F5F5", "bg": "#FFFFFF", "text": "#111111",
        },
    }
    p = palettes.get(palette_key, palettes["modern-blue"])

    html = HTML_TEMPLATE.format(
        title=config.get("title", "Infographic"),
        subtitle=config.get("subtitle", ""),
        footer=config.get("footer", ""),
        config_json=json.dumps(config),
        primary=p["primary"], secondary=p["secondary"], accent=p["accent"],
        neutral=p["neutral"], light=p["light"], bg=p["bg"], text=p["text"],
    )

    out = Path(output_path)
    out.write_text(html, encoding="utf-8")
    print(f"✅ Interactive infographic saved → {out.resolve()}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="JSON config file path")
    parser.add_argument("--output", default="infographic.html")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    generate_html(config, args.output)
