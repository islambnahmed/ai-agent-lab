"""Lumen 370: scoped historical replay for frozen-base correction forks.

A historical evaluation must not be invalidated by a *later* bad sibling or
correction. This function validates the selected ancestry and its visible
receipt-order prefix, not the entire version DAG. It is NOT a global ledger
integrity check, a source authentication scheme, or a substitute for auditing
all records at a later cutoff.
"""

from lumen366 import LedgerError, parse_utc
from lumen368 import VERSION_FIELDS, validate_versions, versioned_snapshot


def historical_snapshot(case_ids, base_events, versions, version_id, as_of,
                        *, threshold=0.4, final_only=True):
    """Evaluate a selected version as known at a cutoff, with explicit scope.

    Rejects ambiguous visible version IDs, unavailable ancestry, malformed
    selected-path envelopes, and out-of-order selected-path correction times.
    Future versions and corrections cannot change an earlier result. Invalid
    unrelated siblings are not inspected beyond their visible ID/time envelope.
    """
    cutoff = parse_utc(as_of)
    if not isinstance(versions, list) or not versions:
        raise LedgerError("versions must be a nonempty list")
    if not isinstance(version_id, str) or not version_id:
        raise LedgerError("invalid requested version ID")

    visible = {}
    for pos, version in enumerate(versions):
        if not isinstance(version, dict):
            raise LedgerError("invalid version envelope")
        vid = version.get("id")
        if not isinstance(vid, str) or not vid.strip():
            raise LedgerError("invalid version envelope ID")
        created = parse_utc(version.get("created_at"))
        if created <= cutoff:
            if vid in visible:
                raise LedgerError("ambiguous duplicate visible version ID")
            visible[vid] = (pos, version)

    if version_id not in visible:
        raise LedgerError("requested version unavailable at cutoff")
    selected = []
    seen = set()
    vid = version_id
    while True:
        if vid in seen:
            raise LedgerError("cycle in selected version ancestry")
        seen.add(vid)
        if vid not in visible:
            raise LedgerError("selected ancestor unavailable at cutoff")
        pos, version = visible[vid]
        if set(version) != VERSION_FIELDS:
            raise LedgerError("selected version fields mismatch")
        selected.append((pos, version))
        parent = version["parent"]
        if parent is None:
            if pos != 0:
                raise LedgerError("selected root is not first version")
            break
        if not isinstance(parent, str) or parent not in visible:
            raise LedgerError("selected ancestor unavailable at cutoff")
        if visible[parent][0] >= pos:
            raise LedgerError("parent must precede child in version ledger")
        vid = parent

    selected.reverse()
    projected = []
    ignored_future_corrections = 0
    for _, version in selected:
        corrections = version["corrections"]
        if not isinstance(corrections, list):
            raise LedgerError("selected corrections must be a list")
        prefix = []
        seen_future = False
        for correction in corrections:
            if not isinstance(correction, dict):
                raise LedgerError("invalid selected correction envelope")
            at = parse_utc(correction.get("recorded_at"))
            if at > cutoff:
                seen_future = True
                ignored_future_corrections += 1
            else:
                if seen_future:
                    raise LedgerError("out-of-order selected correction after future record")
                prefix.append(correction)
        projected.append({**version, "corrections": prefix})

    # Reuse the original strict validation and computation on precisely the
    # selected, visible lineage. This keeps policy and arithmetic consistent.
    validate_versions(case_ids, base_events, projected)
    result = versioned_snapshot(case_ids, base_events, projected, version_id,
                                as_of, threshold=threshold, final_only=final_only)
    return {**result,
            "validation_scope": "selected_lineage_visible_as_of_only",
            "excluded_unrelated_or_future_versions": len(versions) - len(projected),
            "excluded_future_corrections_on_lineage": ignored_future_corrections,
            "global_ledger_validated": False,
            "source_attested": False}
