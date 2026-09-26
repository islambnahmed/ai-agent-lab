#!/usr/bin/env python3
"""Evaluate whether a coordination claim is safe to use without refresh."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

class Verdict(str, Enum):
    USABLE = "usable"
    REFRESH = "refresh"
    HISTORICAL = "historical"
    WARNING = "warning"

@dataclass(frozen=True)
class Claim:
    claim_kind: str
    source_ref: str | None = None
    source_path: str | None = None
    observed_at: str | None = None

def evaluate(claim: Claim, current_source_ref: str) -> Verdict:
    """Return the minimum action a consumer should take before using claim."""
    if claim.claim_kind == "historical_observation":
        return Verdict.HISTORICAL
    if claim.claim_kind != "current_state":
        return Verdict.WARNING

    # A mutable branch name is not provenance: require immutable commit SHAs.
    if (
        not claim.source_ref
        or not SHA_RE.fullmatch(claim.source_ref)
        or not SHA_RE.fullmatch(current_source_ref)
        or not claim.source_path
        or not claim.observed_at
    ):
        return Verdict.WARNING

    if claim.source_ref != current_source_ref:
        return Verdict.REFRESH
    return Verdict.USABLE

def _self_test() -> None:
    old = "1" * 40
    new = "2" * 40
    base = dict(source_path="shared/state.json", observed_at="2026-09-26T00:00:00Z")
    assert evaluate(Claim("current_state", source_ref=old, **base), new) == Verdict.REFRESH
    assert evaluate(Claim("current_state", source_ref=new, **base), new) == Verdict.USABLE
    assert evaluate(Claim("historical_observation", source_ref=old, **base), new) == Verdict.HISTORICAL
    assert evaluate(Claim("current_state", source_ref=None, **base), new) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_ref="main", **base), new) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_ref=new, **base), "main") == Verdict.WARNING

if __name__ == "__main__":
    _self_test()
    print("claim freshness self-test: PASS")
