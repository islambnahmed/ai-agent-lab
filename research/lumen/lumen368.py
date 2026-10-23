"""Lumen 368: explicit, immutable-in-model forks for corrections to final labels.

All timestamps and source fields are lab assertions, NOT independent attestation.
Base event ledger is frozen before any child fork; this intentionally excludes
streaming ingestion after a fork. No external state or network access.
"""
from datetime import datetime
from lumen366 import LedgerError, parse_utc, validate_ledger

VERSION_FIELDS = {"id", "parent", "created_at", "corrections"}
CORRECTION_FIELDS = {"id", "case_id", "supersedes", "label", "recorded_at", "reason", "source"}


def _valid_name(x):
    return isinstance(x, str) and bool(x.strip())


def validate_versions(case_ids, base_events, versions):
    """Validate a frozen base ledger and a DAG of explicit correction forks.

    Child forks may branch from earlier versions. Each correction must point to
    the exact preceding final evidence (event or correction) for that case.
    """
    validate_ledger(case_ids, base_events)
    if not isinstance(versions, list) or not versions:
        raise LedgerError("versions must be a nonempty list")
    base_latest = {e["case_id"]: e for e in base_events}
    base_end = parse_utc(base_events[-1]["ingested_at"]) if base_events else None
    seen_ids = {e["id"] for e in base_events}
    states = {}
    lineage = {}
    last_times = {}
    for index, version in enumerate(versions):
        if not isinstance(version, dict) or set(version) != VERSION_FIELDS:
            raise LedgerError("version fields mismatch")
        vid = version["id"]
        if not _valid_name(vid) or vid in states:
            raise LedgerError("duplicate/invalid version ID")
        at = parse_utc(version["created_at"])
        parent = version["parent"]
        if index == 0:
            if parent is not None or version["corrections"] != []:
                raise LedgerError("root must have no parent or corrections")
            if base_events and at > parse_utc(base_events[0]["ingested_at"]):
                raise LedgerError("root must predate base ingestion")
            state = {cid: (e["id"], e["label"], e["status"]) for cid, e in base_latest.items()}
            chain = [vid]
            last_time = base_end if base_end is not None else at
        else:
            if not isinstance(parent, str) or parent not in states:
                raise LedgerError("parent must be an earlier version")
            if base_end is not None and at <= base_end:
                raise LedgerError("fork must occur after frozen base ledger")
            if at <= last_times[parent]:
                raise LedgerError("fork must occur after parent latest correction")
            state = states[parent].copy()
            chain = lineage[parent] + [vid]
            last_time = at
        corrections = version["corrections"]
        if not isinstance(corrections, list):
            raise LedgerError("corrections must be a list")
        for correction in corrections:
            if not isinstance(correction, dict) or set(correction) != CORRECTION_FIELDS:
                raise LedgerError("correction fields mismatch")
            cid, eid = correction["case_id"], correction["id"]
            if not _valid_name(eid) or eid in seen_ids:
                raise LedgerError("duplicate/invalid correction ID")
            if not isinstance(cid, str) or cid not in case_ids:
                raise LedgerError("unknown corrected case")
            if not _valid_name(correction["reason"]) or not _valid_name(correction["source"]):
                raise LedgerError("correction reason and declared source required")
            if type(correction["label"]) is not int or correction["label"] not in (0, 1):
                raise LedgerError("corrected label must be binary integer")
            t = parse_utc(correction["recorded_at"])
            if t <= last_time:
                raise LedgerError("correction receipt time must increase")
            old = state.get(cid)
            if old is None or old[2] != "final":
                raise LedgerError("only existing final evidence can be corrected")
            if correction["supersedes"] != old[0]:
                raise LedgerError("correction must anchor to latest final evidence")
            if correction["label"] == old[1]:
                raise LedgerError("no-op correction must not rewrite evidence")
            state[cid] = (eid, correction["label"], "final")
            seen_ids.add(eid)
            last_time = t
        states[vid] = state
        lineage[vid] = chain
        last_times[vid] = last_time
    return lineage


def versioned_snapshot(case_ids, base_events, versions, version_id, as_of,
                       *, threshold=0.4, final_only=True):
    lineage = validate_versions(case_ids, base_events, versions)
    cutoff = parse_utc(as_of)
    if version_id not in lineage:
        raise LedgerError("unknown evaluation version")
    if type(threshold) not in (int, float) or not 0 <= threshold <= 1:
        raise LedgerError("threshold outside [0,1]")
    if type(final_only) is not bool:
        raise LedgerError("final_only must be bool")
    by_id = {v["id"]: v for v in versions}
    chosen = by_id[version_id]
    if cutoff < parse_utc(chosen["created_at"]):
        raise LedgerError("evaluation version not yet created at cutoff")
    latest = {}
    for event in base_events:
        if parse_utc(event["ingested_at"]) <= cutoff:
            latest[event["case_id"]] = (event["id"], event["label"], event["status"])
    applied = []
    for vid in lineage[version_id][1:]:
        for correction in by_id[vid]["corrections"]:
            if parse_utc(correction["recorded_at"]) <= cutoff:
                cid = correction["case_id"]
                old = latest.get(cid)
                if old is None or old[0] != correction["supersedes"] or old[2] != "final":
                    raise LedgerError("historical correction anchor mismatch")
                latest[cid] = (correction["id"], correction["label"], "final")
                applied.append(correction["id"])
    known = {cid: item[1] for cid, item in latest.items()
             if not final_only or item[2] == "final"}
    unknown = sorted(set(case_ids) - set(known))
    n = len(case_ids)
    lower = sum(known.values()) / n
    upper = (sum(known.values()) + len(unknown)) / n
    decision = "accept" if upper <= threshold else "reject" if lower > threshold else "abstain"
    return {"version_id": version_id, "lineage": lineage[version_id],
            "as_of": as_of, "policy": "final_only" if final_only else "naive_latest",
            "known": len(known), "unknown": unknown,
            "lower_rate": lower, "upper_rate": upper, "decision": decision,
            "applied_corrections": applied,
            "provenance": "synthetic_self_declared_not_independently_attested"}
