"""Validate present AI Agent Lab artifacts without mandating optional workflows.

The autonomy charter makes roles, queues, dashboards, and heartbeat formats
revisable. A missing optional artifact is not a validation failure. When an
artifact follows the current known shape, catch obvious corruption; a future
schema version is not silently judged using old rules.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message):
    raise SystemExit(message)


def read_optional(path):
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"Expected JSON object in {path.relative_to(ROOT)}")
    return value


def current_schema(doc, version):
    return doc is not None and doc.get("schema_version") == version


def validate():
    # This file documents the lab's hard safety and authorization boundaries.
    if not (ROOT / "AUTONOMY_CHARTER.md").is_file():
        fail("Missing AUTONOMY_CHARTER.md: review hard boundaries before removing it")

    shared = ROOT / "shared"
    state = read_optional(shared / "state.json")
    if current_schema(state, 1):
        if not isinstance(state.get("agents"), dict) or not isinstance(state.get("shared"), dict):
            fail("Invalid shared/state.json v1: agents and shared must be objects")

    heartbeat = read_optional(shared / "heartbeat.json")
    if current_schema(heartbeat, 1):
        for key, entry in heartbeat.items():
            if key == "schema_version":
                continue
            if not isinstance(entry, dict):
                fail(f"Invalid heartbeat entry: {key}")
            count = entry.get("total_cycles")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                fail(f"Invalid heartbeat total_cycles: {key}")
            successful = entry.get("last_successful_cycle")
            if successful is not None and (isinstance(successful, bool) or not isinstance(successful, int) or successful < 0 or successful > count):
                fail(f"Invalid heartbeat last_successful_cycle: {key}")

    queue = read_optional(shared / "task_queue.json")
    if current_schema(queue, 2) and not isinstance(queue.get("tasks"), list):
        fail("Invalid task queue v2: tasks must be a list")

    roles = read_optional(shared / "role_pool.json")
    if current_schema(roles, 1):
        role_list = roles.get("default_roles")
        if not isinstance(role_list, list):
            fail("Invalid role pool v1: default_roles must be a list")
        names = [r.get("name") if isinstance(r, dict) else None for r in role_list]
        if any(not isinstance(n, str) or not n.strip() for n in names) or len(set(names)) != len(names):
            fail("Invalid role pool v1: names must be nonempty and unique")

    suite = read_optional(ROOT / "evals" / "suite.json")
    if suite is not None and "tasks" in suite:
        tasks = suite["tasks"]
        if not isinstance(tasks, list):
            fail("Invalid eval suite: tasks must be a list")
        ids = [t.get("id") if isinstance(t, dict) else None for t in tasks]
        if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(set(ids)):
            fail("Invalid eval suite: task ids must be nonempty and unique")

    print("AI Agent Lab validation passed (optional artifacts are optional)")


if __name__ == "__main__":
    validate()
