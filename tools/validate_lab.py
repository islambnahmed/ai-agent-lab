import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "PROTOCOL.md",
    ROOT / "shared" / "state.json",
    ROOT / "shared" / "messages" / "README.md",
    ROOT / "evals" / "suite.json",
]
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    raise SystemExit("Missing required files: " + ", ".join(missing))

state = json.loads((ROOT / "shared" / "state.json").read_text())
if state.get("schema_version") != 1:
    raise SystemExit("Unsupported state schema_version")
for key in ("agent_0", "agent_1"):
    if key not in state.get("agents", {}):
        raise SystemExit(f"Missing agent state: {key}")
if "shared" not in state:
    raise SystemExit("Missing shared state")

suite = json.loads((ROOT / "evals" / "suite.json").read_text())
ids = [task["id"] for task in suite.get("tasks", [])]
if not ids or len(ids) != len(set(ids)):
    raise SystemExit("Eval task ids must be present and unique")

print("AI Agent Lab validation passed")
