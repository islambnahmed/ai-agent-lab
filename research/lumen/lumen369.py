"""Lumen 369: case-level divergence audit across explicit correction forks.

Read-only analysis. A matching aggregate error rate or decision is not proof
that branches agree about individual cases or evidence provenance. Inputs,
including receipt times and source names, are lab declarations, not attested.
"""

from lumen366 import LedgerError, parse_utc
from lumen368 import validate_versions, versioned_snapshot


def _state_at(case_ids, base_events, versions_by_id, lineage, cutoff):
    """Reconstruct case-level evidence on one already-validated lineage."""
    state = {}
    for event in base_events:
        if parse_utc(event["ingested_at"]) <= cutoff:
            state[event["case_id"]] = {
                "evidence_id": event["id"], "label": event["label"],
                "status": event["status"], "declared_source": event["source"]}
    for version_id in lineage[1:]:
        for correction in versions_by_id[version_id]["corrections"]:
            if parse_utc(correction["recorded_at"]) > cutoff:
                continue
            previous = state.get(correction["case_id"])
            if (previous is None or previous["evidence_id"] != correction["supersedes"]
                    or previous["status"] != "final"):
                raise LedgerError("correction evidence mismatch at cutoff")
            state[correction["case_id"]] = {
                "evidence_id": correction["id"], "label": correction["label"],
                "status": "final", "declared_source": correction["source"]}
    return {cid: state.get(cid) for cid in sorted(case_ids)}


def compare_version_forks(case_ids, base_events, versions, left_id, right_id,
                          as_of, *, threshold=0.4, final_only=True):
    """Compare branches at the same cutoff, without attempting an auto-merge.

    Returns evidence differences, label differences, common ancestry, and
    independent decisions. Any differing evidence requires manual adjudication,
    even when the decisions and aggregate error rates match. Does not certify
    that a declared source or correction is truthful.
    """
    lineage_by_id = validate_versions(case_ids, base_events, versions)
    if left_id not in lineage_by_id or right_id not in lineage_by_id:
        raise LedgerError("unknown comparison version")
    cutoff = parse_utc(as_of)
    by_id = {v["id"]: v for v in versions}
    for vid in (left_id, right_id):
        if cutoff < parse_utc(by_id[vid]["created_at"]):
            raise LedgerError("comparison version not yet created at cutoff")
    left_snapshot = versioned_snapshot(
        case_ids, base_events, versions, left_id, as_of,
        threshold=threshold, final_only=final_only)
    right_snapshot = versioned_snapshot(
        case_ids, base_events, versions, right_id, as_of,
        threshold=threshold, final_only=final_only)
    left_lineage, right_lineage = lineage_by_id[left_id], lineage_by_id[right_id]
    left = _state_at(case_ids, base_events, by_id, left_lineage, cutoff)
    right = _state_at(case_ids, base_events, by_id, right_lineage, cutoff)
    evidence_differences = []
    label_differences = []
    for cid in sorted(case_ids):
        a, b = left[cid], right[cid]
        if a != b:
            evidence_differences.append({"case_id": cid, "left": a, "right": b})
        if (a is None) != (b is None) or (a is not None and b is not None and
                                        (a["label"], a["status"]) !=
                                        (b["label"], b["status"])):
            label_differences.append(cid)
    common = None
    for a, b in zip(left_lineage, right_lineage):
        if a != b:
            break
        common = a
    return {
        "left_version": left_id, "right_version": right_id,
        "as_of": as_of, "common_ancestor": common,
        "left_lineage": left_lineage, "right_lineage": right_lineage,
        "left_decision": left_snapshot["decision"],
        "right_decision": right_snapshot["decision"],
        "left_bounds": [left_snapshot["lower_rate"], left_snapshot["upper_rate"]],
        "right_bounds": [right_snapshot["lower_rate"], right_snapshot["upper_rate"]],
        "same_decision": left_snapshot["decision"] == right_snapshot["decision"],
        "same_bounds": (left_snapshot["lower_rate"], left_snapshot["upper_rate"]) ==
                       (right_snapshot["lower_rate"], right_snapshot["upper_rate"]),
        "evidence_differences": evidence_differences,
        "label_differences": label_differences,
        "merge_gate": "manual_adjudication_required" if evidence_differences else "identical_evidence",
        "provenance": "synthetic_self_declared_not_independently_attested",
    }
