"""Lumen 371: independently supplied commitment guard for scoped historical replay.

A digest only detects change against an *already trusted, separately retained*
reference digest. This module DOES NOT prove receipt time, external provenance,
append-only storage, or truth of a label. Never trust a digest supplied by the
same potentially compromised ledger being checked.
"""
import hashlib
import hmac
import json
import re

from lumen366 import LedgerError, parse_utc
from lumen370 import historical_snapshot

SCHEMA = "lumen371.selected_lineage_commitment.v1"


def _replay_inputs(case_ids, base_events, versions, version_id, as_of, *, threshold, final_only):
    # Delegate validity and historical-scope semantics to the existing audited API.
    result = historical_snapshot(case_ids, base_events, versions, version_id,
                                 as_of, threshold=threshold, final_only=final_only)
    cutoff = parse_utc(as_of)
    lineage = result["lineage"]
    selected = []
    for vid in lineage:
        candidates = [v for v in versions if v["id"] == vid and
                      parse_utc(v["created_at"]) <= cutoff]
        if len(candidates) != 1:
            raise LedgerError("ambiguous historical lineage")
        v = candidates[0]
        selected.append({**v, "corrections": [c for c in v["corrections"]
                                              if parse_utc(c["recorded_at"]) <= cutoff]})
    # Preserve exact receipt order, source declarations, version metadata and
    # evaluation policy. This binds the frozen base in full, even if the
    # requested cutoff predates a base event.
    payload = {"schema": SCHEMA, "case_ids": case_ids,
               "base_events": base_events, "selected_versions": selected,
               "version_id": version_id, "as_of": as_of,
               "threshold": threshold, "final_only": final_only}
    try:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise LedgerError("noncanonical commitment payload") from exc
    return result, canonical


def make_replay_commitment(case_ids, base_events, versions, version_id, as_of,
                           *, threshold=0.4, final_only=True):
    """Compute a digest to retain independently BEFORE later ledger edits.

    The returned digest is NOT an attestation unless a trustworthy party has
    stored it separately with a verifiable time of existence.
    """
    result, canonical = _replay_inputs(case_ids, base_events, versions,
                                       version_id, as_of, threshold=threshold,
                                       final_only=final_only)
    return {"algorithm": "sha256", "schema": SCHEMA,
            "digest": hashlib.sha256(canonical).hexdigest(),
            "snapshot": result, "independently_attested": False}


def verify_replay_commitment(case_ids, base_events, versions, version_id, as_of,
                             expected_digest, *, threshold=0.4, final_only=True):
    """Fail closed if current historical inputs differ from trusted reference.

    `expected_digest` MUST come from an independent trusted channel. Passing
    `make_replay_commitment(...)["digest"]` computed on the same untrusted
    current data does not provide security.
    """
    if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise LedgerError("invalid expected commitment digest")
    result, canonical = _replay_inputs(case_ids, base_events, versions,
                                       version_id, as_of, threshold=threshold,
                                       final_only=final_only)
    actual = hashlib.sha256(canonical).hexdigest()
    if not hmac.compare_digest(actual, expected_digest):
        raise LedgerError("historical replay commitment mismatch")
    return {**result, "commitment_verified_against_supplied_digest": True,
            "digest": actual, "independent_digest_custody_verified": False}
