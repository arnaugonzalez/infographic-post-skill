"""Flag the generic "AI infographic" patterns the brief bans. Warnings, not errors."""
from __future__ import annotations

import re

_CHECKS: list[tuple[str, str]] = [
    (r"(linear|radial|conic)-gradient\(", "gradient"),
    (r"backdrop-filter|filter\s*:\s*blur", "blur / glassmorphism"),
    (r"box-shadow\s*:\s*(?!none)", "box-shadow"),
    (r"text-shadow\s*:\s*(?!none)", "glow (text-shadow)"),
    (r"background-clip\s*:\s*text", "gradient text"),
    (r"#(6d28d9|7c3aed|8b5cf6|a855f7|9333ea|6366f1|4f46e5|818cf8)\b", "purple/indigo palette"),
    (r"Technical Architecture Overview|Follow for more|Get [Ss]tarted", "generic subtitle / CTA"),
    (r"[\U0001F300-\U0001FAFF☀-➿]", "emoji"),
]
_GENERIC_FONTS = {"Inter", "Manrope", "Roboto", "Poppins", "Montserrat"}
_FAMILY = re.compile(r"family=([A-Za-z+]+)")
_DECISION = re.compile(r"<!--.*?thesis:.*?hero:.*?archetype:.*?-->", re.S | re.I)
_BORDER_RADIUS = re.compile(r"border-radius\s*:\s*(\d+)px")


def lint_html(html: str, archetype: str | None = None) -> list[str]:
    """Return one warning per banned pattern found in ``html``."""
    declared = re.search(r"archetype:\s*(\w+)", html)
    archetype = archetype or (declared.group(1).lower() if declared else None)
    warnings = [f"{label}" for pattern, label in _CHECKS if re.search(pattern, html)]
    # Blueprint draws its grid paper with repeating linear-gradients sized by background-size.
    if archetype == "blueprint" and "background-size" in html:
        warnings = [w for w in warnings if w != "gradient"]
    families = {f.replace("+", " ") for f in _FAMILY.findall(html)}
    if families and families <= _GENERIC_FONTS:
        warnings.append("only generic fonts (" + ", ".join(sorted(families)) + ")")
    if archetype != "brutalist":
        radii = [int(r) for r in _BORDER_RADIUS.findall(html)]
        if sum(r >= 12 for r in radii) >= 4:
            warnings.append("many rounded cards (border-radius ≥ 12px)")
    if not _DECISION.search(html):
        warnings.append("missing thesis/hero/archetype comment")
    return warnings
