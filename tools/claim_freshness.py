#!/usr/bin/env python3
"""Evaluate whether a coordination claim is safe to use without refresh.

Freshness is tied to the source file's immutable blob SHA, not the repository
commit SHA. An unrelated commit must not invalidate an otherwise unchanged
claim.
"""

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
    source_blob_sha: str | None = None
    source_path: str | None = None
    observed_at: str | None = None

def evaluate(claim: Claim, current_source_blob_sha: str) -> Verdict:
    """Return the minimum action a consumer should take before using claim."""
    if claim.claim_kind == "historical_observation":
        return Verdict.HISTORICAL
    if claim.claim_kind != "current_state":
        return Verdict.WARNING

    if (
        not claim.source_blob_sha
        or not SHA_RE.fullmatch(claim.source_blob_sha)
        or not SHA_RE.fullmatch(current_source_blob_sha)
        or not claim.source_path
        or not claim.observed_at
    ):
        return Verdict.WARNING

    if claim.source_blob_sha != current_source_blob_sha:
        return Verdict.REFRESH
    return Verdict.USABLE

def _self_test() -> None:
    old_blob = "1" * 40
    same_blob = "2" * 40
    changed_blob = "3" * 40
    base = dict(source_path="shared/state.json", observed_at="2026-09-26T00:00:00Z")

    assert evaluate(Claim("current_state", source_blob_sha=old_blob, **base), changed_blob) == Verdict.REFRESH
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob) == Verdict.USABLE
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, **base), changed_blob) == Verdict.HISTORICAL
    assert evaluate(Claim("current_state", source_blob_sha=None, **base), same_blob) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha="main", **base), same_blob) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), "main") == Verdict.WARNING

    # Repository HEAD may advance for unrelated files while the source blob
    # remains unchanged. Blob identity keeps the claim usable in that case.
    unrelated_new_commit = "f" * 40
    assert unrelated_new_commit != same_blob
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob) == Verdict.USABLE

if __name__ == "__main__":
    _self_test()
    print("claim freshness self-test: PASS")
