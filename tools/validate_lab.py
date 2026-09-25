import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "AGENT_CAPABILITIES.md",
    ROOT / "PROTOCOL.md",
    ROOT / "shared" / "state.json",
    ROOT / "shared" / "task_queue.json",
    ROOT / "shared" / "heartbeat.json",
    ROOT / "shared" / "role_pool.json",
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

heartbeat = json.loads((ROOT / "shared" / "heartbeat.json").read_text())
if heartbeat.get("schema_version") != 1:
    raise SystemExit("Unsupported heartbeat schema_version")
for key in ("agent_0", "agent_1"):
    agent_heartbeat = heartbeat.get(key)
    if not isinstance(agent_heartbeat, dict):
        raise SystemExit(f"Missing heartbeat state: {key}")
    if not isinstance(agent_heartbeat.get("total_cycles"), int) or agent_heartbeat["total_cycles"] < 0:
        raise SystemExit(f"Invalid heartbeat total_cycles: {key}")
    for field in ("last_seen", "last_successful_cycle", "last_error"):
        if field not in agent_heartbeat:
            raise SystemExit(f"Missing heartbeat field {field}: {key}")

queue = json.loads((ROOT / "shared" / "task_queue.json").read_text())
if queue.get("schema_version") != 2:
    raise SystemExit("Unsupported task queue schema_version")
if not queue.get("policy", {}).get("allow_subtasks"):
    raise SystemExit("Task queue must allow subtask decomposition")

roles = json.loads((ROOT / "shared" / "role_pool.json").read_text())
role_names = {r.get("name") for r in roles.get("default_roles", [])}
required_roles = {"Researcher", "Skeptic", "Builder", "Tester", "Judge", "Archivist", "Coordinator"}
missing_roles = required_roles - role_names
if missing_roles:
    raise SystemExit("Missing required virtual roles: " + ", ".join(sorted(missing_roles)))

suite = json.loads((ROOT / "evals" / "suite.json").read_text())
ids = [task["id"] for task in suite.get("tasks", [])]
if not ids or len(ids) != len(set(ids)):
    raise SystemExit("Eval task ids must be present and unique")

print("AI Agent Lab validation passed")
