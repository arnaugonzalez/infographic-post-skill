# Infographic Skill for Claude Code

Generate professional, publication-ready infographics from data, text, or project context — directly from Claude Code.

## What It Does

- **PNG infographics** — KPI dashboards, process flows, comparisons, data spotlights (matplotlib, fully offline)
- **LinkedIn architecture diagrams** — Auto-reads your CLAUDE.md and project structure, outputs 1080x1080px publication-ready PNGs
- **Interactive HTML charts** — Self-contained HTML with embedded Chart.js
- **AI-powered "pretty mode"** — Uses Google Gemini to generate stunning glassmorphism designs with brand icons (optional, requires API key)

## Prerequisites

- Python 3.9+
- pip
- [Claude Code](https://claude.ai/code) (to use as a skill)
- (Optional) Google AI Studio API key or GCP project for pretty mode

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/infographic-skill.git
cd infographic-skill
pip install -r requirements.txt
```

### 2. Try the demo

```bash
python scripts/generate.py --demo
# Creates demo_infographic.png (1080x1350px)
```

### 3. Use as a Claude Code skill

Copy or symlink this directory into your Claude Code skills directory. Then ask Claude:

> "Make an infographic of our Q3 KPIs: Revenue $2.4M, NPS 72, Churn 2.1%"
> "Generate a linkedin architecture diagram for this project"
> "Make this architecture diagram pretty for linkedin"

## Setup for Pretty Mode (Optional)

Pretty mode uses Google Gemini for AI-generated designs. Core matplotlib features work without any API key.

### Option A: Google AI Studio (free tier available)

1. Get an API key at https://aistudio.google.com/apikey
2. Copy the env template: `cp .env.example .env`
3. Add your key: `INFG_API_KEY=your-key-here`

### Option B: Google Cloud Vertex AI

1. Create a GCP project with Vertex AI API enabled
2. Authenticate: `gcloud auth application-default login`
3. Copy the env template: `cp .env.example .env`
4. Set your project: `INFG_VERTEX_PROJECT=your-project-id`

### Optional setup: OpenRouter

Use OpenRouter to route text generation through any model (Claude, GPT-4o, Llama, etc.).

1. Get an API key at [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Set in `.env`:

```text
INFG_LLM_PROVIDER=openrouter
INFG_LLM_MODEL=anthropic/claude-opus-4
INFG_OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

3. Run:

```bash
python3 scripts/generate_pretty.py \
  --text "Your data here" \
  --output pretty.html
```

Note: OpenRouter only supports the HTML-output path. Image generation always uses Gemini.

### Optional: HTML to PNG screenshots

```bash
pip install playwright && playwright install chromium
```

## Usage Examples

### PNG Infographic (offline, no API key)

```bash
python scripts/generate.py --demo
```

Or via library import:

```python
from scripts.generate import InfographicCanvas
canvas = InfographicCanvas(1080, 1920, dpi=150, palette="modern-blue")
canvas.add_header("Title", subtitle="Subtitle")
canvas.add_kpi_row(kpis=[("$2.4M", "Revenue", "+18%")])
canvas.save("output.png")
```

### LinkedIn Architecture Diagram

```bash
# From project context
python scripts/parse_context.py --root /path/to/project --title "My App" --output arch.json
python scripts/generate_linkedin_arch.py --config arch.json --output arch.png

# Quick inline
python scripts/generate_linkedin_arch.py \
  --layers "Frontend:React,Next.js|Backend:FastAPI|Database:PostgreSQL" \
  --title "My App" --output arch.png
```

### Interactive HTML Chart

```bash
python scripts/generate_html.py --config templates/example-config.json --output chart.html
```

### Pretty Mode (Gemini AI)

```bash
# Architecture diagram
python scripts/generate_pretty.py --config arch.json --output pretty.png

# With learnings focus
python scripts/generate_pretty.py \
  --config arch.json \
  --learnings "FastAPI async patterns, PostgreSQL JSONB" \
  --output pretty.png

# Dashboard
python scripts/generate_pretty.py \
  --text "Revenue $2.4M (+18%), NPS 72" \
  --type dashboard --title "Q3 KPIs" --output dashboard.png
```

## Available Gemini Models

| Model | Output | Backend | Notes |
|-------|--------|---------|-------|
| `gemini-3.1-flash-image-preview` | PNG | AI Studio | Default, native image gen |
| `gemini-2.5-flash-image` | PNG | Vertex AI | Stable fallback |
| `gemini-2.5-pro` | HTML/PNG | Vertex AI | Best quality |
| `gemini-2.0-flash` | HTML/PNG | Vertex AI | Fast, low cost |

## Project Structure

```
infographic-skill/
├── scripts/
│   ├── generate.py              # Core PNG generator (matplotlib)
│   ├── generate_html.py         # Interactive HTML generator (Chart.js)
│   ├── generate_linkedin_arch.py # LinkedIn diagram generator
│   ├── generate_pretty.py       # AI-powered Gemini generator
│   └── parse_context.py         # Architecture context parser
├── references/
│   ├── design-principles.md     # Visual design rules
│   └── chart-selection.md       # Chart type decision matrix
├── templates/
│   └── example-config.json      # Example config for HTML mode
├── SKILL.md                     # Claude Code skill definition
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Ensure no secrets or API keys are committed
4. Submit a pull request

## License

MIT License — see [LICENSE](LICENSE) for details.
