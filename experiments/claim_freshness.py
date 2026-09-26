#!/usr/bin/env python3
"""Claim provenance plus semantic-consistency experiment.

Freshness answers whether evidence identities changed after observation.
Semantic checks answer whether the current evidence agrees internally.
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


def cycle_consistency(
    state: Mapping[str, Any], heartbeat: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    """Classify each state agent as consistent, mismatch, or unverifiable."""
    results: dict[str, dict[str, Any]] = {}
    agents = state.get("agents")
    if not isinstance(agents, Mapping):
        return {"_state": {"status": "unverifiable", "reason": "missing_or_malformed_agents"}}

    for agent_id, state_record in agents.items():
        heartbeat_record = heartbeat.get(agent_id)
        if not isinstance(state_record, Mapping) or not isinstance(heartbeat_record, Mapping):
            results[agent_id] = {
                "status": "unverifiable",
                "reason": "missing_or_malformed_record",
            }
            continue

        state_cycle = state_record.get("cycle_count")
        heartbeat_cycle = heartbeat_record.get("total_cycles")
        if not isinstance(state_cycle, int) or not isinstance(heartbeat_cycle, int):
            results[agent_id] = {
                "status": "unverifiable",
                "reason": "missing_or_malformed_cycle",
            }
        elif state_cycle == heartbeat_cycle:
            results[agent_id] = {
                "status": "consistent",
                "state": state_cycle,
                "heartbeat": heartbeat_cycle,
            }
        else:
            results[agent_id] = {
                "status": "mismatch",
                "state": state_cycle,
                "heartbeat": heartbeat_cycle,
            }
    return results


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

    assert cycle_consistency(
        {"agents": {"agent_0": {"cycle_count": 5}}},
        {"agent_0": {"total_cycles": 5}},
    ) == {"agent_0": {"status": "consistent", "state": 5, "heartbeat": 5}}

    assert cycle_consistency(
        {"agents": {"agent_1": {"cycle_count": 4}}},
        {"agent_1": {"total_cycles": 5}},
    ) == {"agent_1": {"status": "mismatch", "state": 4, "heartbeat": 5}}

    assert cycle_consistency(
        {"agents": {"agent_2": {"cycle_count": 1}}},
        {},
    ) == {
        "agent_2": {
            "status": "unverifiable",
            "reason": "missing_or_malformed_record",
        }
    }

    assert cycle_consistency(
        {"agents": {"agent_3": {"cycle_count": "unknown"}}},
        {"agent_3": {"total_cycles": 1}},
    ) == {
        "agent_3": {
            "status": "unverifiable",
            "reason": "missing_or_malformed_cycle",
        }
    }

    print("claim_freshness self-test: 7/7 passed")


if __name__ == "__main__":
    _self_test()
