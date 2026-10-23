"""Lumen 366: as-of audit for delayed and corrected synthetic labels.

This is a deterministic lab demonstration, NOT independent label attestation.
The source field and ingestion timestamps are assertions by the lab producer.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

FIELDS = {"id", "case_id", "ingested_at", "label", "status", "supersedes", "source"}
STATUSES = {"provisional", "final"}


class LedgerError(ValueError):
    pass


def parse_utc(value):
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise LedgerError("timestamps must be YYYY-MM-DDTHH:MM:SSZ")
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise LedgerError("invalid UTC timestamp") from exc
    if dt.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise LedgerError("noncanonical UTC timestamp")
    return dt


def validate_ledger(case_ids, events):
    """Enforce one append-only, chronological revision chain per case.

    This validates the representation; it cannot authenticate real-world times,
    producer independence, truth of a label, or completeness of a population.
    """
    if (not isinstance(case_ids, list) or not case_ids or
            any(not isinstance(c, str) or not c for c in case_ids) or
            len(set(case_ids)) != len(case_ids)):
        raise LedgerError("invalid case frame")
    if not isinstance(events, list):
        raise LedgerError("events must be a list")
    seen = set()
    latest = {}
    prev_time = None
    for event in events:
        if not isinstance(event, dict) or set(event) != FIELDS:
            raise LedgerError("event fields mismatch")
        eid, cid = event["id"], event["case_id"]
        if not isinstance(eid, str) or not eid or eid in seen:
            raise LedgerError("duplicate/invalid event ID")
        if cid not in case_ids:
            raise LedgerError("unknown case ID")
        if type(event["label"]) is not int or event["label"] not in (0, 1):
            raise LedgerError("label must be binary integer")
        if event["status"] not in STATUSES:
            raise LedgerError("unknown label status")
        if not isinstance(event["source"], str) or not event["source"]:
            raise LedgerError("missing declared source")
        at = parse_utc(event["ingested_at"])
        if prev_time is not None and at <= prev_time:
            raise LedgerError("events must have strictly increasing ingestion times")
        previous = latest.get(cid)
        expected_parent = previous["id"] if previous else None
        if event["supersedes"] != expected_parent:
            raise LedgerError("revision must supersede latest event for same case")
        if previous and previous["status"] == "final":
            raise LedgerError("final labels cannot be silently overwritten; start a new versioned evaluation")
        latest[cid] = event
        seen.add(eid)
        prev_time = at
    return True


def snapshot(case_ids, events, as_of, *, threshold=0.4, final_only=True):
    cutoff = parse_utc(as_of)
    if not isinstance(events, list):
        raise LedgerError("events must be a list")
    # An as-of snapshot consumes only the receipt-order prefix available then.
    # Validate the full ledger separately when auditing later arrivals.
    prefix = []
    passed_cutoff = False
    for event in events:
        if not isinstance(event, dict) or "ingested_at" not in event:
            raise LedgerError("invalid event envelope")
        at = parse_utc(event["ingested_at"])
        if at > cutoff:
            passed_cutoff = True
            continue
        if passed_cutoff:
            raise LedgerError("out-of-order as-of event after future-dated event")
        prefix.append(event)
    validate_ledger(case_ids, prefix)
    if type(threshold) not in (int, float) or not 0 <= threshold <= 1:
        raise LedgerError("threshold outside [0,1]")
    if type(final_only) is not bool:
        raise LedgerError("final_only must be bool")
    current = {}
    for event in prefix:
        current[event["case_id"]] = event
    known = {c: e["label"] for c, e in current.items()
             if not final_only or e["status"] == "final"}
    unknown = sorted(set(case_ids) - set(known))
    n = len(case_ids)
    lower = sum(known.values()) / n
    upper = (sum(known.values()) + len(unknown)) / n
    decision = ("accept" if upper <= threshold else
                "reject" if lower > threshold else "abstain")
    return {"as_of": as_of, "policy": "final_only" if final_only else "naive_latest",
            "known": len(known), "unknown": unknown, "lower_rate": lower,
            "upper_rate": upper, "decision": decision,
            "provenance": "self_declared_synthetic_lab_events_not_external_attestation"}


def run_demo():
    here = Path(__file__).resolve().parent
    frame = json.loads((here / "lumen365_membership_precommit.json").read_text())
    ledger = json.loads((here / "lumen366_events.json").read_text())
    ids, events = frame["case_ids"], ledger["events"]
    return [{"safe": snapshot(ids, events, time, final_only=True),
             "naive": snapshot(ids, events, time, final_only=False)}
            for time in ledger["cutoffs"]]


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
