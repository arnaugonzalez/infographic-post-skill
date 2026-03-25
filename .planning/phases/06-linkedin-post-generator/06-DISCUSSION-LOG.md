# Phase 6: LinkedIn Post Generator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 06-linkedin-post-generator
**Areas discussed:** Language selection, Post output destination, Post structure rigidity, LLM env var reuse

---

## Language Selection

| Option | Description | Selected |
|--------|-------------|----------|
| `--language` flag | Pass language at invocation: `python generate_posts.py ./myrepo --language es`. No prompt, fully scriptable. | ✓ |
| Interactive prompt | Script asks 'Select language:' and waits for stdin input. | |
| Flag with interactive fallback | Use --language if provided; if omitted, ask interactively. | |

**User's choice:** `--language` flag only

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed enum | Validate against whitelist like `['en', 'es', 'fr', 'de', 'pt', 'it']`. | ✓ |
| Free string, passed through | Accept any string and pass directly to system prompt. | |

**User's choice:** Fixed enum

**Notes:** Language instruction must go in system prompt (not just user turn) to prevent English drift — pre-validated decision from STATE.md.

---

## Post Output Destination

| Option | Description | Selected |
|--------|-------------|----------|
| Stdout only | Print both posts to terminal with clear separators. | |
| Write to .txt files | Save technical_post.txt and business_post.txt. | |
| Both stdout and files | Print to terminal AND write files. | |
| Write to .md file(s) (user choice) | Write to .md to preserve emojis and structure. | ✓ |

**User's choice:** Write to file (user specified: "write to txt file or md keeping emojis and structure for linkedin post")

| Option | Description | Selected |
|--------|-------------|----------|
| Single file, .md | One `linkedin_posts.md` with both posts separated by headers. | ✓ |
| Separate files, .md | `technical_post.md` and `business_post.md`. | |
| Single file, .txt | One `linkedin_posts.txt`. | |

**User's choice:** Single file, `.md`

| Option | Description | Selected |
|--------|-------------|----------|
| Current working directory, stdout too | Write to cwd AND print to stdout. | ✓ |
| Current working directory, file only | Write silently, show confirmation line only. | |
| --output flag to specify path, stdout too | Default to cwd, allow override. | |

**User's choice:** Current working directory, print to stdout too.

---

## Post Structure Rigidity

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt-guided with structural requirements | System prompt specifies opening anchors per post type; LLM writes freely within them. | ✓ |
| Fixed sections in system prompt | Explicit section breakdown: Hook → bullets → CTA. | |
| Two fully separate prompts, no shared structure | Maximum divergence, no shared structural requirements. | |

**User's choice:** Prompt-guided with structural requirements

| Option | Description | Selected |
|--------|-------------|----------|
| Soft guideline — include in prompt, accept result | Character range stated in prompt; accept what LLM returns. | |
| Warn but don't retry | Check count, print warning if outside range. | |
| Retry once if outside range | One follow-up LLM call to correct length. | ✓ |

**User's choice:** Retry once if outside 800–1,600 character range.

---

## LLM Env Var Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse INFG_OPENROUTER_API_KEY + INFG_LLM_MODEL | Same vars as generate_pretty.py. No .env changes. | ✓ |
| New INFG_POSTS_* vars | Separate vars to allow different model per script. | |
| CLI flags override, env vars as fallback | --llm-model / --api-key flags + env fallback. | |

**User's choice:** Reuse existing `INFG_OPENROUTER_API_KEY` and `INFG_LLM_MODEL`.

---

## Claude's Discretion

- Exact system prompt wording (beyond structural anchors)
- Whether to add a `--model` CLI override flag
- Default language when `--language` is omitted
- Stdout character count display per post

## Deferred Ideas

None.
