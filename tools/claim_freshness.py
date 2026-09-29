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
from datetime import datetime, timezone

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

def _valid_observed_at(value: str | None, now: datetime | None = None) -> bool:
    """Require a real, non-future UTC second-resolution timestamp."""
    if not value:
        return False
    try:
        observed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    else:
        reference = reference.astimezone(timezone.utc)
    return observed <= reference

class Verdict(str, Enum):
    USABLE = "usable"
    REFRESH = "refresh"
    HISTORICAL = "historical"
    WARNING = "warning"

def _validate_portable_json(value: object) -> None:
    """Reject values whose JSON representation is not reliably cross-runtime."""
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        # Keep integers exactly representable by common IEEE-754 JSON consumers.
        if abs(value) > 2**53 - 1:
            raise ValueError("integer exceeds portable JSON safe range")
        return
    if isinstance(value, float):
        # 1.0 vs 1 is serialized differently across common runtimes; disallow
        # floats rather than pretending this lightweight format is RFC 8785.
        raise ValueError("floats are not supported in portable scope JSON")
    if isinstance(value, list):
        for item in value:
            _validate_portable_json(item)
        return
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("scope object keys must be strings")
        for item in value.values():
            _validate_portable_json(item)
        return
    raise ValueError(f"unsupported scope value type: {type(value).__name__}")


def canonical_scope_sha(value: object) -> str:
    """Return a deterministic Git-style blob SHA for portable structured JSON.

    This intentionally accepts a conservative JSON subset so independent
    runtimes do not silently hash different serializations of the same value.
    """
    _validate_portable_json(value)
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


@dataclass(frozen=True)
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
    now: datetime | None = None,
    verified_historical_shas: set[str] | frozenset[str] | None = None,
) -> Verdict:
    """Return the minimum action a consumer should take before using claim.

    If scoped provenance is present, both scope name and digest must match.
    Otherwise the check falls back to whole-file blob identity. Partial scoped
    metadata is a warning rather than silently falling back to file identity.
    """
    if not _valid_observed_at(claim.observed_at, now):
        return Verdict.WARNING
    if claim.claim_kind == "historical_observation":
        if not claim.source_path:
            return Verdict.WARNING
        scoped_history = any((claim.source_scope, claim.source_scope_sha))
        if scoped_history:
            if (
                not claim.source_scope
                or not claim.source_scope_sha
                or not SHA_RE.fullmatch(claim.source_scope_sha)
            ):
                return Verdict.WARNING
        elif not claim.source_blob_sha or not SHA_RE.fullmatch(claim.source_blob_sha):
            return Verdict.WARNING
        provenance_sha = claim.source_scope_sha if scoped_history else claim.source_blob_sha
        if verified_historical_shas is None or provenance_sha not in verified_historical_shas:
            return Verdict.WARNING
        return Verdict.HISTORICAL
    if claim.claim_kind != "current_state":
        return Verdict.WARNING
    if not claim.source_path or not current_source_path or claim.source_path != current_source_path:
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
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, **base), changed_blob, path) == Verdict.WARNING
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, **base), changed_blob, path,
                    verified_historical_shas={old_blob}) == Verdict.HISTORICAL
    assert evaluate(Claim("current_state", source_blob_sha=None, **base), same_blob, path) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, **base), same_blob, "shared/heartbeat.json") == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, source_path=path, observed_at="not-a-time"), same_blob, path) == Verdict.WARNING
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, source_path=path, observed_at=None), changed_blob, path) == Verdict.WARNING
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, source_path=path, observed_at="2026-99-99T99:99:99Z"), changed_blob, path) == Verdict.WARNING
    reference_now = datetime(2026, 9, 27, 10, 0, 0, tzinfo=timezone.utc)
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, source_path=path,
                          observed_at="2026-09-27T10:00:01Z"),
                    same_blob, path, now=reference_now) == Verdict.WARNING
    assert evaluate(Claim("current_state", source_blob_sha=same_blob, source_path=path,
                          observed_at="2026-09-27T10:00:00Z"),
                    same_blob, path, now=reference_now) == Verdict.USABLE
    assert evaluate(Claim("historical_observation", source_blob_sha="not-a-sha", **base), changed_blob, path) == Verdict.WARNING
    assert evaluate(Claim("historical_observation", source_blob_sha=old_blob, source_path=None, observed_at=base["observed_at"]), changed_blob, path) == Verdict.WARNING
    assert evaluate(Claim("historical_observation", source_path=path, source_scope="worker_c",
                          source_scope_sha="a"*40, observed_at=base["observed_at"]),
                    changed_blob, path, verified_historical_shas={"a"*40}) == Verdict.HISTORICAL
    assert evaluate(Claim("historical_observation", source_path=path, source_scope="worker_c",
                          source_scope_sha="bad", observed_at=base["observed_at"]),
                    changed_blob, path) == Verdict.WARNING

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

    # Reject values with unstable or lossy representations across JSON runtimes.
    for nonportable in (
        {"value": float("nan")},
        {"value": float("inf")},
        {"value": 1.0},
        {"value": 2**53},
        {1: "non-string-key"},
        {"value": ("tuple",)},
    ):
        try:
            canonical_scope_sha(nonportable)
        except ValueError:
            pass
        else:
            raise AssertionError("non-portable scope JSON must be rejected")

if __name__ == "__main__":
    _self_test()
    print("claim freshness self-test: PASS")
