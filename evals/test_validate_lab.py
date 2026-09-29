"""Regression tests for tools/validate_lab.py.

These tests execute the validator against a temporary copy of the lab so
malformed fixtures cannot mutate shared lab state.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_case(tmp_path, mutate):
    lab = tmp_path / "lab"
    shutil.copytree(ROOT, lab, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    state_path = lab / "shared" / "state.json"
    heartbeat_path = lab / "shared" / "heartbeat.json"
    state = json.loads(state_path.read_text())
    heartbeat = json.loads(heartbeat_path.read_text())
    mutate(state, heartbeat)
    state_path.write_text(json.dumps(state))
    heartbeat_path.write_text(json.dumps(heartbeat))
    return subprocess.run(
        [sys.executable, str(lab / "tools" / "validate_lab.py")],
        capture_output=True, text=True,
    )

def message(result):
    return result.stdout + result.stderr

def test_bool_state_cycle_rejected(tmp_path):
    result = run_case(tmp_path, lambda s, h: s["agents"]["agent_0"].__setitem__("cycle_count", True))
    assert result.returncode != 0
    assert "Invalid state cycle_count: agent_0" in message(result)

def test_bool_heartbeat_total_rejected(tmp_path):
    result = run_case(tmp_path, lambda s, h: h["agent_0"].__setitem__("total_cycles", True))
    assert result.returncode != 0
    assert "Invalid heartbeat total_cycles: agent_0" in message(result)

def test_malformed_last_successful_cycle_is_cleanly_rejected(tmp_path):
    result = run_case(tmp_path, lambda s, h: h["agent_0"].__setitem__("last_successful_cycle", "5"))
    assert result.returncode != 0
    assert "Invalid heartbeat last_successful_cycle: agent_0" in message(result)
    assert "Traceback" not in message(result)

def test_cycle_drift_rejected(tmp_path):
    def mutate(state, heartbeat):
        heartbeat["agent_0"]["total_cycles"] = state["agents"]["agent_0"]["cycle_count"] + 1
    result = run_case(tmp_path, mutate)
    assert result.returncode != 0
    assert "Cycle drift for agent_0" in message(result)
