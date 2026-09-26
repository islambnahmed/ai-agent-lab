#!/usr/bin/env python3
"""Claim provenance plus semantic-consistency experiment.

Freshness answers whether evidence identities changed after observation.
Semantic checks answer whether the *current* evidence agrees internally.
Neither result implies the other.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class Evidence:
    path: str
    blob_sha: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    observed_at: str
    evidence: Sequence[Evidence]


def classify_freshness(claim: Claim, current_shas: Mapping[str, str]) -> str:
    """Return current or needs_revalidation based on dependency identity."""
    for item in claim.evidence:
        if current_shas.get(item.path) != item.blob_sha:
            return "needs_revalidation"
    return "current"


def cycle_consistency(state: Mapping[str, Any], heartbeat: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    """Report agents whose state cycle_count differs from heartbeat total_cycles.

    The mapping is intentionally explicit: state agent_0/agent_1 correspond to
    heartbeat agent_0/agent_1. Missing/malformed records are skipped here rather
    than conflated with semantic disagreement; schema validation is a separate layer.
    """
    mismatches: dict[str, dict[str, int]] = {}
    agents = state.get("agents", {})
    for agent_id, state_record in agents.items():
        heartbeat_record = heartbeat.get(agent_id)
        if not isinstance(state_record, Mapping) or not isinstance(heartbeat_record, Mapping):
            continue
        state_cycle = state_record.get("cycle_count")
        heartbeat_cycle = heartbeat_record.get("total_cycles")
        if isinstance(state_cycle, int) and isinstance(heartbeat_cycle, int) and state_cycle != heartbeat_cycle:
            mismatches[agent_id] = {"state": state_cycle, "heartbeat": heartbeat_cycle}
    return mismatches


def _self_test() -> None:
    claim = Claim(
        claim_id="demo-1",
        statement="The observed artifacts agreed at observation time.",
        observed_at="2026-09-26T00:00:00Z",
        evidence=(Evidence("state.json", "aaa"), Evidence("heartbeat.json", "bbb")),
    )
    assert classify_freshness(claim, {"state.json": "aaa", "heartbeat.json": "bbb"}) == "current"
    assert classify_freshness(claim, {"state.json": "changed", "heartbeat.json": "bbb"}) == "needs_revalidation"
    assert classify_freshness(claim, {"state.json": "aaa"}) == "needs_revalidation"

    consistent_state = {"agents": {"agent_0": {"cycle_count": 5}}}
    consistent_heartbeat = {"agent_0": {"total_cycles": 5}}
    assert cycle_consistency(consistent_state, consistent_heartbeat) == {}

    inconsistent_state = {"agents": {"agent_1": {"cycle_count": 4}}}
    inconsistent_heartbeat = {"agent_1": {"total_cycles": 5}}
    assert cycle_consistency(inconsistent_state, inconsistent_heartbeat) == {
        "agent_1": {"state": 4, "heartbeat": 5}
    }

    # Real lab artifact identities observed on sandbox/worker-a.
    lab_claim = Claim(
        claim_id="lab-snapshot-1",
        statement="This claim depends on the observed shared state and heartbeat snapshots.",
        observed_at="2026-09-26T09:22:00Z",
        evidence=(
            Evidence("shared/state.json", "93bc5fb1b7977cfcbb1754f04a854e33a8d4b688"),
            Evidence("shared/heartbeat.json", "0c7c13d5151ba898dde4ac57d75f6b20198f1f4e"),
        ),
    )
    observed = {
        "shared/state.json": "93bc5fb1b7977cfcbb1754f04a854e33a8d4b688",
        "shared/heartbeat.json": "0c7c13d5151ba898dde4ac57d75f6b20198f1f4e",
    }
    assert classify_freshness(lab_claim, observed) == "current"

    # Fresh evidence can still disagree semantically: this is the key counterexample.
    real_state = {
        "agents": {
            "agent_0": {"cycle_count": 5},
            "agent_1": {"cycle_count": 4},
        }
    }
    real_heartbeat = {
        "agent_0": {"total_cycles": 5},
        "agent_1": {"total_cycles": 5},
    }
    assert cycle_consistency(real_state, real_heartbeat) == {
        "agent_1": {"state": 4, "heartbeat": 5}
    }

    deliberately_stale = dict(observed)
    deliberately_stale["shared/heartbeat.json"] = "simulated-new-blob-sha"
    assert classify_freshness(lab_claim, deliberately_stale) == "needs_revalidation"

    print("claim_freshness self-test: 8/8 passed")


if __name__ == "__main__":
    _self_test()
