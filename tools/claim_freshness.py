#!/usr/bin/env python3
"""Evaluate whether a coordination claim is safe to use without refresh.

Freshness is tied to the immutable identity of the smallest practical source
scope. Whole-file blob provenance remains supported; callers may instead bind
a claim to a stable scope (for example worker_c) and a digest of that scope.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

class Verdict(str, Enum):
    USABLE = "usable"
    REFRESH = "refresh"
    HISTORICAL = "historical"
    WARNING = "warning"

@dataclass(frozen=True)
def canonical_scope_sha(value: object) -> str:
    """Return a deterministic Git-style blob SHA for structured scope content.

    Canonical JSON prevents irrelevant object-key ordering from changing scope
    identity while preserving meaningful value/list-order changes.
    """
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


class Claim:
    claim_kind: str
    source_blob_sha: str | None = None
    source_path: str | None = None
    source_scope: str | None = None
    source_scope_sha: str | None = None
    observed_at: str | None = None

def evaluate(
    claim: Claim,
    current_source_blob_sha: str,
    current_source_path: str | None = None,
    *,
    current_source_scope: str | None = None,
    current_source_scope_sha: str | None = None,
) -> Verdict:
    """Return the minimum action a consumer should take before using claim.

    If scoped provenance is present, both scope name and digest must match.
    Otherwise the check falls back to whole-file blob identity. Partial scoped
    metadata is a warning rather than silently falling back to file identity.
    """
    if claim.claim_kind == "historical_observation":
        return Verdict.HISTORICAL
    if claim.claim_kind != "current_state":
        return Verdict.WARNING
    if not claim.source_path or not current_source_path or claim.source_path != current_source_path or not claim.observed_at:
        return Verdict.WARNING

    scoped = any((claim.source_scope, claim.source_scope_sha, current_source_scope, current_source_scope_sha))
    if scoped:
        if (
            not claim.source_scope
            or not claim.source_scope_sha
            or not current_source_scope
            or not current_source_scope_sha
            or not SHA_RE.fullmatch(claim.source_scope_sha)
            or not SHA_RE.fullmatch(current_source_scope_sha)
            or claim.source_scope != current_source_scope
        ):
            return Verdict.WARNING
        return Verdict.USABLE if claim.source_scope_sha == current_source_scope_sha else Verdict.REFRESH

    if (
        not claim.source_blob_sha
        or not SHA_RE.fullmatch(claim.source_blob_sha)
        or not SHA_RE.fullmatch(current_source_blob_sha)
    ):
        return Verdict.WARNING
    return Verdict.USABLE if claim.source_blob_sha == current_source_blob_sha else Verdict.REFRESH

def _self_test() -> None:
    old_blob, same_blob, changed_blob = "1"*40, "2"*40, "3"*40
    path = "shared/state.json"
    base = dict(source_path=path, observed_at="2026-09-27T10:00:00Z")

    assert evaluate(Claim("current_state", source_blob_sha=old_blob, **base), changed_blob, path) == Verdict.REFRESH
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob, path) == Verdict.USABLE
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, **base), changed_blob, path) == Verdict.HISTORICAL
    assert evaluate(Claim("current_state", source_blob_sha=None, **base), same_blob, path) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob, "shared/heartbeat.json") == Verdict.WARNING

    # Scoped provenance prevents unrelated edits elsewhere in the same file
    # from invalidating a claim about worker_c.
    scoped = Claim("current_state", source_path=path, source_scope="worker_c",
                   source_scope_sha="a"*40, observed_at=base["observed_at"])
    assert evaluate(scoped, changed_blob, path, current_source_scope="worker_c",
                    current_source_scope_sha="a"*40) == Verdict.USABLE
    assert evaluate(scoped, changed_blob, path, current_source_scope="worker_c",
                    current_source_scope_sha="b"*40) == Verdict.REFRESH
    assert evaluate(scoped, changed_blob, path, current_source_scope="worker_a",
                    current_source_scope_sha="a"*40) == Verdict.WARNING
    assert evaluate(scoped, changed_blob, path) == Verdict.WARNING

    # Scope digests have one reproducible construction rather than relying on
    # callers to invent incompatible 40-character hashes.
    scope_a = {"cycle_count": 6, "name": "Khepri"}
    scope_a_reordered = {"name": "Khepri", "cycle_count": 6}
    scope_b = {"cycle_count": 7, "name": "Khepri"}
    assert canonical_scope_sha(scope_a) == canonical_scope_sha(scope_a_reordered)
    assert canonical_scope_sha(scope_a) != canonical_scope_sha(scope_b)

if __name__ == "__main__":
    _self_test()
    print("claim freshness self-test: PASS")
