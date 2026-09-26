#!/usr/bin/env python3
"""Cross-artifact semantic consistency check for shared coordination state.

Usage:
    python tools/check_coordination_consistency.py [state.json] [heartbeat.json]

Exit 0 when invariants hold, 1 when semantic drift is detected, 2 on invalid input.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def check(state: dict, heartbeat: dict) -> list[str]:
    errors: list[str] = []
    agents = state.get("agents", {})
    if not isinstance(agents, dict):
        return ["state.agents must be an object"]

    for agent_id, agent_state in agents.items():
        if not isinstance(agent_state, dict):
            errors.append(f"{agent_id}: state entry must be an object")
            continue

        hb = heartbeat.get(agent_id)
        if not isinstance(hb, dict):
            errors.append(f"{agent_id}: missing heartbeat entry")
            continue

        state_cycles = agent_state.get("cycle_count")
        total_cycles = hb.get("total_cycles")
        successful = hb.get("last_successful_cycle")

        if not isinstance(state_cycles, int) or isinstance(state_cycles, bool):
            errors.append(f"{agent_id}: state cycle_count is not an integer")
        if not isinstance(total_cycles, int) or isinstance(total_cycles, bool):
            errors.append(f"{agent_id}: heartbeat total_cycles is not an integer")
        if successful is not None and (
            not isinstance(successful, int) or isinstance(successful, bool)
        ):
            errors.append(f"{agent_id}: heartbeat last_successful_cycle is not an integer/null")

        if isinstance(state_cycles, int) and isinstance(total_cycles, int):
            if state_cycles != total_cycles:
                errors.append(
                    f"{agent_id}: cycle drift: state={state_cycles}, heartbeat={total_cycles}"
                )

        if isinstance(successful, int) and isinstance(total_cycles, int):
            if successful > total_cycles:
                errors.append(
                    f"{agent_id}: last_successful_cycle={successful} exceeds total_cycles={total_cycles}"
                )

    return errors


def main(argv: list[str]) -> int:
    state_path = Path(argv[1]) if len(argv) > 1 else Path("shared/state.json")
    heartbeat_path = Path(argv[2]) if len(argv) > 2 else Path("shared/heartbeat.json")
    try:
        state = load(state_path)
        heartbeat = load(heartbeat_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2

    errors = check(state, heartbeat)
    if errors:
        print("coordination semantic drift detected:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("coordination artifacts are semantically consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
