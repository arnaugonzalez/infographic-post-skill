import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "infographic"

# `from scripts.x import ...` needs the skill dir; `import x` needs scripts/.
for p in (SKILL_DIR, SKILL_DIR / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
