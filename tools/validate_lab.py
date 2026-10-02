"""Validate only core lab invariants.

AUTONOMY_CHARTER.md makes protocols, queues, heartbeats, roles, evals, and CI
optional infrastructure. This validator therefore must not make any of those
systems a prerequisite for a healthy lab.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The charter is the authority for what is non-optional inside the repository.
charter = ROOT / "AUTONOMY_CHARTER.md"
if not charter.is_file():
    raise SystemExit("Missing core authority: AUTONOMY_CHARTER.md")

text = charter.read_text(encoding="utf-8")
for heading in ("## Hard Boundaries", "## Continuity"):
    if heading not in text:
        raise SystemExit(f"Autonomy charter missing core section: {heading}")

print("AI Agent Lab validation passed")
