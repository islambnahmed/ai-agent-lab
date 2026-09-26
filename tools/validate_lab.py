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

    state_cycles = state["agents"][key].get("cycle_count")
    if not isinstance(state_cycles, int) or state_cycles < 0:
        raise SystemExit(f"Invalid state cycle_count: {key}")
    cycle_delta = agent_heartbeat["total_cycles"] - state_cycles
    # A heartbeat may legitimately land one cycle before the derived shared
    # state is reconciled by an independent agent.  Treat that single-step
    # lead as an in-flight update, while still rejecting impossible reverse
    # ordering and durable (>1 cycle) drift.
    if cycle_delta < 0 or cycle_delta > 1:
        raise SystemExit(
            f"Cycle drift for {key}: state={state_cycles}, heartbeat={agent_heartbeat['total_cycles']}"
        )
    successful_cycle = agent_heartbeat.get("last_successful_cycle")
    if successful_cycle is not None and successful_cycle > agent_heartbeat["total_cycles"]:
        raise SystemExit(f"Heartbeat successful cycle exceeds total_cycles: {key}")

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
