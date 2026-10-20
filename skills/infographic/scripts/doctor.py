"""Diagnostic CLI for infographic backends and environment readiness.

Prints a table of supported backends, whether each is installed, its default model,
and whether it uses a subscription CLI or a pay-per-use API. Never prints API key values.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backends  # noqa: E402


def _agy_models() -> str:
    """Run ``agy models`` with a 20s timeout and return a comma-separated list of model IDs."""
    if not shutil.which("agy"):
        return "no disponible"
    try:
        res = subprocess.run(
            ["agy", "models"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=20,
            start_new_session=True,
        )
    except (OSError, subprocess.SubprocessError):
        return "no disponible"
    if res.returncode != 0 or not (res.stdout or "").strip():
        return "no disponible"
    ids: list[str] = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line or line.lower().startswith(("model", "id", "available", "-", "=")):
            continue
        tok = re.split(r"\s+", line)[0].strip("*•- ")
        if tok and re.match(r"^[a-z0-9][a-z0-9._\-]+$", tok, re.IGNORECASE):
            ids.append(tok)
    return ", ".join(ids) if ids else res.stdout.strip().splitlines()[0]


def run_doctor() -> str:
    """Build and return the diagnostic report string."""
    rows: list[tuple[str, str, str, str]] = []
    for name, spec in backends.BACKENDS.items():
        binary = spec["binary"]
        if binary:
            installed = "sí" if shutil.which(binary) else "no"
        elif name == "api":
            has_key = bool(os.environ.get("ANTHROPIC_API_KEY")) or bool(os.environ.get("INFG_API_KEY"))
            installed = "sí" if has_key else "no"
        elif name == "session":
            installed = "sí" if bool(os.environ.get("CLAUDECODE")) else "no"
        else:
            installed = "no"

        default_model = spec["default_model"] or ("claude-opus-5-5 / gemini-3.8-flash" if name == "api" else "-")
        billing = "API (por uso)" if name == "api" else "suscripción"
        rows.append((name, installed, str(default_model), billing))

    lines = [
        "| Backend | Instalado | Modelo por defecto | Tipo |",
        "|---------|-----------|--------------------|------|",
    ]
    for name, installed, default_model, billing in rows:
        lines.append(f"| {name} | {installed} | {default_model} | {billing} |")

    lines.append("")
    lines.append(
        "Variables de entorno (presentes, sin valores): "
        f"ANTHROPIC_API_KEY={'sí' if os.environ.get('ANTHROPIC_API_KEY') else 'no'}, "
        f"INFG_API_KEY={'sí' if os.environ.get('INFG_API_KEY') else 'no'}, "
        f"CLAUDECODE={'sí' if os.environ.get('CLAUDECODE') else 'no'}"
    )
    lines.append(f"Modelos agy: {_agy_models()}")
    return "\n".join(lines)


def main() -> None:
    print(run_doctor())


if __name__ == "__main__":
    main()
