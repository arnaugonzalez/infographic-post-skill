# Benchmark — infographic pipeline, Oct 2026

Run 2026-10-11 with `benchmark/bench.py`. Total spend **$5.24** (Anthropic $2.72, Gemini $2.52),
under the $3 + $3 budget. Raw outputs: `results/` (PNGs, HTML, specs, every judge verdict,
`ledger.jsonl` with the price of each call).

## Setup

- **Cases:** three real repos — `project-b` (Flutter + FastAPI + Terraform monorepo),
  `project-a` (Astro + FastAPI + Docker), `infographic` (this skill).
- **Structuring:** 7 configurations × 3 cases. Graded on whether each sub-project and core
  technology appears, and on noise.
- **Rendering:** every renderer got the *same* spec per case (Opus 5.5 structuring output), so only
  rendering is compared. Architecture type, `modern-dark` style, 1:1.
- **Judging:** blind; each PNG downscaled to 1024 px and scored 1–10 on 6 criteria by two judges from
  different vendors (`gemini-3.1-pro-preview`, `claude-sonnet-5-5`), given the spec. The tables show
  the mean over 3 cases × 2 judges. With n=3, gaps under ~0.5 points are noise.

## Rendering

| Renderer | $/img | s/img | text | complete | logos | hierarchy | aesthetics | publishable | **mean** |
|---|---|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 HTML v2, effort low ¹ | 0.182 | 82 | 8.0 | 8.5 | 4.8 | 7.0 | 7.3 | 6.3 | **7.00** |
| gemini-3-pro-image @2K | 0.141 | 33 | 7.3 | 7.3 | 6.2 | 7.2 | 7.7 | 6.2 | **6.97** |
| Claude Opus 5.5 HTML v1, effort medium | 0.445 | 202 | 8.3 | 8.3 | 3.7 | 7.0 | 7.5 | 5.3 | 6.69 |
| Hybrid: Opus HTML → gemini-3-pro-image restyle | 0.137 ² | 25 | 6.2 | 8.3 | 3.8 | 7.0 | 7.5 | 4.7 | 6.25 |
| gemini-3.1-flash-image @2K | 0.102 | 16 | 5.2 | 6.2 | 4.8 | 6.7 | 7.3 | 4.0 | 5.69 |
| Claude Haiku 5.5 HTML | 0.013 | 112 | 6.5 | 8.2 | 3.2 | 6.5 | 5.8 | 4.0 | 5.69 |
| Claude Sonnet 5.5 HTML | 0.086 | 53 | 6.2 | 7.5 | 2.7 | 6.3 | 5.5 | 3.8 | 5.33 |
| Jinja template (free) | 0 | 0 | 6.7 | 7.0 | 3.3 | 5.2 | 5.3 | 3.3 | 5.14 |
| gemini-3.1-flash-lite-image @1K | 0.034 | 4 | 4.2 | 5.7 | 4.3 | 5.8 | 6.5 | 3.0 | 4.92 |
| **gemini-3.1-flash-image @1K (old default)** | 0.068 | 11 | 4.2 | 3.7 | 4.8 | 5.8 | 6.8 | **2.5** | **4.64** |

¹ v2 = the brief rewritten after reading the v1 judge errors, plus the icon-registry fixes
(monogram fallback, progressive slug matching). The v1 Claude rows used the old 🔧 emoji fallback,
so their logo scores are depressed by that.
² Image cost only; it also needs the Opus HTML render as input.

**Readings**

- The old default was the worst renderer. At 1K the flash image model garbles text and drops items.
  Asking for 2K alone moves it from 2.5 to 4.0 publishable.
- The two top renderers fail in opposite ways. Claude HTML typesets the text, so names are exact
  and complete (8.0 / 8.5). Its weak point is logos, because many techs have no Simple Icons
  mark. Gemini 3 Pro Image paints convincing logos and atmosphere (6.2 / 7.7), but it still drops
  or renames items on 20+ item specs.
- Opus at effort `low` beat effort `medium` while costing 59% less ($0.18 vs $0.45) and running
  2.5× faster. Effort `medium` mostly spent tokens on denser layouts, and the judges penalised that
  density.
- Sonnet 5.5 and Haiku 5.5 HTML are not good substitutes for Opus on layout design. Haiku is very
  cheap and complete, but the result looks plain.
- The hybrid (image model restyling the Opus render) keeps completeness (8.3). It also
  re-introduces spelling errors (6.2) and still loses on logos, so it is not worth a second call.

## Structuring

| Config | input | $/call | s | layers | items | Notes |
|---|---|---|---|---|---|---|
| **old: gemini-2.5-flash on raw report** | 50k tok | 0.0335 | 32 | 5.3 | 18.0 | Misses project-a's Astro frontend; turns `.media-analysis/` one-off scripts into a core layer |
| gemini-2.5-flash on digest | ~1.5–5k tok | 0.0145 | 26 | 5.3 | 20.0 | Good; some generic items ("Shell Scripting", "HTML") |
| gemini-3.8-flash | digest | 0.0116 | 17 | 4.3 | 14.3 | Accurate, fewer items |
| gemini-3.1-flash-lite | digest | 0.0016 | 2 | 4.3 | 11.3 | Too sparse |
| **claude-haiku-5-5** (new default) | digest | **0.0011** | 6 | 4.7 | 17.3 | Accurate, every sub-project |
| claude-sonnet-5-5 | digest | 0.0210 | 8 | 5.3 | 21.3 | Very good |
| claude-opus-5-5 (effort low) | digest | 0.0413 | 10 | 5.3 | 22.3 | Most complete and best grouped |

The input matters more than the model. `read_codebase` sorts `main.py`/`__init__.py` first, then
`.py` files by size, then *everything else*. So README, `package.json`, `pubspec.yaml` and
`docker-compose.yml` were cut by the 40k-token budget. The project-b report had 0 Dart files and
the project-a report had 0 TypeScript files. `project_digest.py` replaces it for structuring.

## Cost per infographic (new defaults)

| Path | Structuring | Rendering | Total |
|---|---|---|---|
| Inside Claude Code, in-session HTML | $0.001 (Haiku) | $0 (the agent writes the HTML) | **~$0.001** |
| `--renderer image` | $0.001 | $0.134 | ~$0.135 |
| `--renderer claude-html` | $0.001 | ~$0.13–0.28 | ~$0.18 |
| Old default (as shipped) | ~$0.03 (OpenRouter) | $0.067 (reported as $0.039) | ~$0.10, and the worst quality |

## Not tested / next

- `gemini-3-pro-image` with a prompt tuned from its judge errors (cap items per layer, an explicit
  exact-text list). That is the cheapest likely gain for the image path.
- Other infographic types (process, comparison, cheatsheet) and the light/illustrated styles.
- A human preference check. Both judges are LLMs, and they agreed within 1 point on most renders.
