#!/usr/bin/env python3
"""Evaluate whether a coordination claim is safe to use without refresh.

Freshness is tied to the source file's immutable blob SHA, not the repository
commit SHA. The source path is also bound into the check so identical blobs at
different paths cannot accidentally validate each other's claims.
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

def evaluate(
    claim: Claim,
    current_source_blob_sha: str,
    current_source_path: str | None = None,
) -> Verdict:
    """Return the minimum action a consumer should take before using claim.

    Consumers should pass the path they actually refreshed. Omitting it is
    tolerated as WARNING during migration, never as USABLE.
    """
    if claim.claim_kind == "historical_observation":
        return Verdict.HISTORICAL
    if claim.claim_kind != "current_state":
        return Verdict.WARNING

    if (
        not claim.source_blob_sha
        or not SHA_RE.fullmatch(claim.source_blob_sha)
        or not SHA_RE.fullmatch(current_source_blob_sha)
        or not claim.source_path
        or not current_source_path
        or claim.source_path != current_source_path
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
    path = "shared/state.json"
    base = dict(source_path=path, observed_at="2026-09-26T00:00:00Z")

    assert evaluate(Claim("current_state", source_blob_sha=old_blob, **base), changed_blob, path) == Verdict.REFRESH
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob, path) == Verdict.USABLE
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, **base), changed_blob, path) == Verdict.HISTORICAL
    assert evaluate(Claim("current_state", source_blob_sha=None, **base), same_blob, path) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha="main", **base), same_blob, path) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), "main", path) == Verdict.WARNING

    # A blob SHA alone is not enough: identical content at another path must
    # not validate a claim about shared/state.json.
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob, "shared/heartbeat.json") == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob) == Verdict.WARNING

    # Repository HEAD may advance for unrelated files while the source blob
    # remains unchanged. Blob identity keeps the claim usable in that case.
    unrelated_new_commit = "f" * 40
    assert unrelated_new_commit != same_blob
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob, path) == Verdict.USABLE

if __name__ == "__main__":
    _self_test()
    print("claim freshness self-test: PASS")
