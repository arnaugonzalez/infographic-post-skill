"""Selectable CLI and API backends for structuring and HTML rendering.

Priority in ``resolve()``: explicit argument > ``INFG_BACKEND`` / ``INFG_MODEL`` > ``auto``.
``auto`` selects ``session`` inside Claude Code (``CLAUDECODE`` set) or the first installed
subscription CLI in ``detect()`` — it never selects a paid API without being asked.
"""
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROMPTS_DIR = _SCRIPTS_DIR / "prompts"

NO_BACKEND_MESSAGE = (
    "No AI backend found. Install one of the supported subscription CLIs or configure an API key:\n"
    "  • claude   — Claude Code CLI: npm install -g @anthropic-ai/claude-code\n"
    "  • agy      — Antigravity CLI: see https://antigravity.dev\n"
    "  • codex    — OpenAI Codex CLI: npm install -g @openai/codex\n"
    "  • copilot  — GitHub Copilot CLI: gh extension install github/gh-copilot\n"
    "  • opencode — OpenCode CLI: npm install -g opencode-ai\n"
    "  • session  — Run inside Claude Code (CLAUDECODE=1) or pass --backend session\n"
    "  • api      — Pass --backend api with ANTHROPIC_API_KEY or INFG_API_KEY set"
)


class BackendError(RuntimeError):
    """Raised when a backend CLI exits non-zero or returns unusable output."""

    def __init__(self, backend: str, stderr: str = "") -> None:
        self.backend = backend
        self.stderr = stderr
        super().__init__(f"{backend}: {stderr}" if stderr else backend)


def family_of(model: str | None, default: str = "other") -> str:
    """Map a model identifier to one of: claude | gemini | gpt | glm | deepseek | other."""
    if not model or model == "auto":
        return default
    name = model.lower().strip()
    if "/" in name:
        name = name.split("/", 1)[1]
    if "claude" in name or name.startswith(("opus", "sonnet", "haiku", "fable")):
        return "claude"
    if "gemini" in name or name.startswith("gemma"):
        return "gemini"
    if name.startswith(("gpt", "o1", "o3", "o4", "codex")) or "gpt-" in name:
        return "gpt"
    if name.startswith("glm") or "glm-" in name:
        return "glm"
    if "deepseek" in name:
        return "deepseek"
    return "other"


BACKENDS: dict[str, dict] = {
    "claude": {
        "binary": "claude",
        "argv": ["claude", "-p", "--model", "{model}", "--tools", "", "--strict-mcp-config"],
        "stdin": True,
        "default_model": "claude-opus-5-5",
        "family_of": lambda m: family_of(m, "claude"),
        "timeout_s": 600,
    },
    "agy": {
        "binary": "agy",
        # agy needs --output-format json in print mode; the answer is in the last JSON line's "response".
        "argv": ["agy", "--print", "{prompt}", "--output-format", "json", "--model", "{model}",
                 "--print-timeout", "600s"],
        "stdin": False,
        "json_field": "response",
        "default_model": "claude-opus-5-5-low",
        "family_of": lambda m: family_of(m, "claude"),
        "timeout_s": 600,
    },
    "codex": {
        "binary": "codex",
        "argv": ["codex", "exec", "--skip-git-repo-check", "-m", "{model}", "-"],
        "stdin": True,
        "default_model": None,
        "family_of": lambda m: family_of(m, "gpt"),
        "timeout_s": 600,
    },
    "copilot": {
        "binary": "copilot",
        "argv": ["copilot", "-p", "{prompt}", "--model", "auto"],
        "stdin": False,
        "default_model": "auto",
        "family_of": lambda m: family_of(m, "gpt"),
        "timeout_s": 600,
    },
    "opencode": {
        "binary": "opencode",
        "argv": ["opencode", "run", "-m", "{model}", "{prompt}"],
        "stdin": False,
        "default_model": None,
        "family_of": lambda m: family_of(m, "other"),
        "timeout_s": 600,
    },
    "api": {
        "binary": None,
        "argv": [],
        "stdin": False,
        "default_model": None,
        "family_of": lambda m: family_of(m, "claude"),
        "timeout_s": 600,
    },
    "session": {
        "binary": None,
        "argv": [],
        "stdin": False,
        "default_model": None,
        "family_of": lambda m: family_of(m, "claude"),
        "timeout_s": 600,
    },
}

_CLI_ORDER = ("claude", "agy", "codex", "copilot", "opencode")


def detect() -> list[str]:
    """Return available backends in priority order without reading or printing key values."""
    found = [name for name in _CLI_ORDER if shutil.which(BACKENDS[name]["binary"])]
    if bool(os.environ.get("ANTHROPIC_API_KEY")) or bool(os.environ.get("INFG_API_KEY")):
        found.append("api")
    return found


def resolve(backend: str | None = None, model: str | None = None) -> tuple[str, str | None]:
    """Resolve (backend, model) with priority: argument > env INFG_BACKEND/INFG_MODEL > auto."""
    chosen_backend = (backend or os.environ.get("INFG_BACKEND") or "auto").strip().lower()
    chosen_model = (model if model is not None else os.environ.get("INFG_MODEL") or "").strip() or None

    if chosen_backend == "auto":
        if os.environ.get("CLAUDECODE"):
            chosen_backend = "session"
        else:
            cli_backends = [b for b in detect() if b != "api"]
            if not cli_backends:
                raise SystemExit(NO_BACKEND_MESSAGE)
            chosen_backend = cli_backends[0]

    if chosen_backend not in BACKENDS:
        raise SystemExit(f"Unknown backend {chosen_backend!r}.\n\n{NO_BACKEND_MESSAGE}")

    if chosen_model is None:
        chosen_model = BACKENDS[chosen_backend]["default_model"]
    return chosen_backend, chosen_model


def build_argv(backend: str, model: str | None, prompt: str) -> list[str]:
    """Expand the argv template for *backend*, omitting ``-m``/``--model`` when model is None."""
    spec = BACKENDS[backend]
    effective_model = model if model is not None else spec["default_model"]
    out: list[str] = []
    for token in spec["argv"]:
        if token == "{model}":
            if effective_model is None:
                if out and out[-1] in ("-m", "--model"):
                    out.pop()
            else:
                out.append(str(effective_model))
        elif token == "auto" and backend == "copilot" and out and out[-1] == "--model" and effective_model:
            out.append(str(effective_model))
        elif token == "{prompt}":
            out.append(prompt)
        else:
            out.append(token)
    return out


def run(backend: str, model: str | None, prompt: str) -> str:
    """Execute *backend* with *prompt* and return stdout."""
    if backend not in BACKENDS:
        raise BackendError(backend, f"Unknown backend: {backend}")
    spec = BACKENDS[backend]

    if backend == "session":
        raise BackendError("session", "session backend is handled by the host agent")

    if backend == "api":
        if model and "/" in model and (model.lower().startswith("google/") or "gemini" in model.lower()):
            raise BackendError("api", "OpenRouter is forbidden for Gemini models; use AI Studio (INFG_API_KEY)")
        from content_structurer import _CALLERS, resolve_provider
        import content_structurer as cs
        provider, resolved_model, api_key = resolve_provider(model)
        if not api_key:
            raise BackendError("api", f"Missing API key for provider {provider}")
        caller = getattr(cs, _CALLERS[provider])
        return caller(prompt, resolved_model, api_key)

    cmd = build_argv(backend, model, prompt)
    kwargs: dict = {
        "capture_output": True,
        "text": True,
        "timeout": spec["timeout_s"],
        "start_new_session": True,
    }
    if spec["stdin"]:
        kwargs["input"] = prompt
    else:
        kwargs["stdin"] = subprocess.DEVNULL

    field = spec.get("json_field")
    # Agentic CLIs run in an empty scratch dir so they cannot touch the user's project.
    with tempfile.TemporaryDirectory(prefix="infg-") as scratch:
        if field:
            return _run_until_json(backend, cmd, scratch, spec["timeout_s"], field)
        res = subprocess.run(cmd, cwd=scratch, **kwargs)
    if res.returncode != 0:
        stderr = (res.stderr or "")[-2000:]
        raise BackendError(backend, stderr)
    return res.stdout


def _run_until_json(backend: str, cmd: list[str], cwd: str, timeout_s: int, field: str) -> str:
    """Read stdout until a JSON line carrying ``field`` arrives, then stop the process group.

    agy prints its JSON result and sometimes keeps running afterwards, so waiting for exit hangs.
    """
    proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    lines: queue.Queue[str | None] = queue.Queue()

    def pump() -> None:
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    deadline = time.monotonic() + timeout_s
    seen: list[str] = []
    try:
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                line = lines.get(timeout=remaining)
            except queue.Empty:
                break
            if line is None:
                break
            seen.append(line)
            if line.lstrip().startswith("{"):
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("status", "SUCCESS") != "SUCCESS":
                    raise BackendError(backend, f"status {data.get('status')}: {str(data.get('error', ''))[:500]}")
                if field in data:
                    return str(data[field])
        tail = "".join(seen)[-500:]
        raise BackendError(backend, f"no JSON result with {field!r} before exit or {timeout_s}s timeout: {tail}")
    finally:
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def extract_html(text: str) -> str:
    """Extract from the first ``<!doctype html`` or ``<html`` to the last ``</html>``."""
    cleaned = re.sub(r"```(?:html)?\s*", "", text or "", flags=re.IGNORECASE).replace("```", "")
    start_match = re.search(r"<!doctype\s+html|<html\b", cleaned, flags=re.IGNORECASE)
    if not start_match:
        raise BackendError("html", "No HTML document found in output")
    end_matches = list(re.finditer(r"</html\s*>", cleaned, flags=re.IGNORECASE))
    if not end_matches or end_matches[-1].end() <= start_match.start():
        raise BackendError("html", "Incomplete HTML document (missing </html>)")
    return cleaned[start_match.start():end_matches[-1].end()].strip()


def extract_json(text: str) -> dict:
    """Strip markdown fences / preamble and parse JSON into a dict."""
    from content_structurer import _strip_json_fences
    cleaned = _strip_json_fences(text or "")
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise BackendError("json", f"Invalid JSON output: {exc}") from exc
    if not isinstance(data, dict):
        raise BackendError("json", "Expected a JSON object")
    return data


def build_prompt(
    task: str,
    backend: str | None,
    model: str | None,
    spec: dict,
    *,
    style: str | None = None,
    kind: str = "architecture",
    fmt: str | None = None,
    style_dir: str | None = None,
) -> str:
    """Combine task brief + backend contract + model-family note + spec JSON."""
    b_name = (backend or "claude").lower()
    entry = BACKENDS.get(b_name, BACKENDS["claude"])
    effective_model = model if model is not None else entry["default_model"]
    fam = entry["family_of"](effective_model)

    spec_json = json.dumps(spec, indent=1, ensure_ascii=False)
    if task == "structure":
        from content_structurer import _STRUCTURER_PROMPT
        report_text = spec.get("summary_text") if isinstance(spec, dict) else None
        base = _STRUCTURER_PROMPT.format(codebase_report=report_text or spec_json)
        if report_text:
            base = f"{base}\n\nSPEC JSON:\n{spec_json}"
    else:
        from design import render_brief
        base = render_brief(spec, kind=kind, style=style, fmt=fmt, style_dir=style_dir)

    backend_file = _PROMPTS_DIR / "backends" / f"{b_name}.md"
    if not backend_file.exists():
        backend_file = _PROMPTS_DIR / "backends" / "claude.md"
    backend_note = backend_file.read_text(encoding="utf-8").strip()

    model_file = _PROMPTS_DIR / "models" / f"{fam}.md"
    if not model_file.exists():
        model_file = _PROMPTS_DIR / "models" / "other.md"
    model_note = model_file.read_text(encoding="utf-8").strip()

    return f"{base}\n\n{backend_note}\n\n{model_note}"
