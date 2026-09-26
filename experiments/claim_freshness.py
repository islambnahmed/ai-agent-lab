#!/usr/bin/env python3
"""Minimal claim-freshness classifier.

Input is a claim record plus a mapping of current evidence blob SHAs.
This deliberately does not decide whether changed content still supports a claim:
a changed or missing dependency requires semantic revalidation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


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


def classify(claim: Claim, current_shas: Mapping[str, str]) -> str:
    """Return current or needs_revalidation based on dependency identity."""
    for item in claim.evidence:
        if current_shas.get(item.path) != item.blob_sha:
            return "needs_revalidation"
    return "current"


def _self_test() -> None:
    claim = Claim(
        claim_id="demo-1",
        statement="The observed artifacts agreed at observation time.",
        observed_at="2026-09-26T00:00:00Z",
        evidence=(Evidence("state.json", "aaa"), Evidence("heartbeat.json", "bbb")),
    )
    assert classify(claim, {"state.json": "aaa", "heartbeat.json": "bbb"}) == "current"
    assert classify(claim, {"state.json": "changed", "heartbeat.json": "bbb"}) == "needs_revalidation"
    assert classify(claim, {"state.json": "aaa"}) == "needs_revalidation"
    print("claim_freshness self-test: 3/3 passed")


if __name__ == "__main__":
    _self_test()
