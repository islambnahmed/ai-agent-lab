"""Lumen 361: committed group membership audit for sharp aggregate-error bounds.

Requires independent, pre-outcome anchoring of the trusted SHA-256 digest.
A hash only detects deviation from its anchor; it does not establish source honesty.
All results are partial-identification bounds, NOT confidence intervals.
"""
import hashlib
import hmac
import json
from lumen360 import Group, InvalidEvidence, robust_bounds

SCHEMA = 'lumen-membership-v1'


def _validate_frame_and_groups(entities, groups):
    entities = tuple(entities)
    groups = tuple(groups)
    if not entities or any(type(e) is not str or not e for e in entities) or len(set(entities)) != len(entities):
        raise InvalidEvidence('canonical entity IDs must be unique nonempty strings')
    if any(type(g.name) is not str or not g.name for g in groups):
        raise InvalidEvidence('group IDs must be nonempty strings')
    if len(set(g.name for g in groups)) != len(groups):
        raise InvalidEvidence('duplicate group IDs')
    for g in groups:
        if g.kind not in ('or', 'count'):
            raise InvalidEvidence(f'{g.name}: unsupported kind')
        if not g.members or any(type(m) is not str or m not in entities for m in g.members):
            raise InvalidEvidence(f'{g.name}: missing/unknown member')
        if len(set(g.members)) != len(g.members):
            raise InvalidEvidence(f'{g.name}: duplicate member')
    return entities, groups


def snapshot_payload(entities, groups, *, frame_version):
    """Canonical snapshot excludes observed aggregate VALUES (which may arrive later)."""
    entities, groups = _validate_frame_and_groups(entities, groups)
    if type(frame_version) is not str or not frame_version.strip():
        raise InvalidEvidence('nonempty external frame_version required')
    return {
        'schema': SCHEMA,
        'frame_version': frame_version,
        'entities': sorted(entities),
        'groups': [
            {'name': g.name, 'kind': g.kind, 'members': sorted(g.members)}
            for g in sorted(groups, key=lambda g: g.name)
        ],
    }


def canonical_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest_snapshot(payload):
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def verify_snapshot(snapshot, trusted_digest):
    if not isinstance(snapshot, dict) or set(snapshot) != {'schema', 'frame_version', 'entities', 'groups'}:
        raise InvalidEvidence('malformed snapshot')
    if snapshot['schema'] != SCHEMA:
        raise InvalidEvidence('wrong schema')
    try:
        groups = tuple(Group(g['name'], tuple(g['members']), g['kind'], 0)
                       for g in snapshot['groups'])
        canonical = snapshot_payload(snapshot['entities'], groups,
                                     frame_version=snapshot['frame_version'])
    except (TypeError, KeyError, AttributeError) as e:
        raise InvalidEvidence('malformed snapshot contents') from e
    if snapshot != canonical:
        raise InvalidEvidence('snapshot must be in canonical form')
    if type(trusted_digest) is not str or len(trusted_digest) != 64:
        raise InvalidEvidence('trusted SHA256 digest required')
    actual = digest_snapshot(canonical)
    if not hmac.compare_digest(actual, trusted_digest.lower()):
        raise InvalidEvidence('snapshot differs from externally trusted digest')
    return canonical


def audited_bounds(snapshot, trusted_digest, reports, *, max_corrupt_values=0,
                   max_nodes=250_000):
    """Reject membership changes; allow up to k corrupted aggregate values.

    trusted_digest MUST come from an independent, prior commitment, not the
    party presenting snapshot/reports. This function cannot verify that.
    """
    canonical = verify_snapshot(snapshot, trusted_digest)
    reports = tuple(reports)
    entities, reports = _validate_frame_and_groups(canonical['entities'], reports)
    spec = {g['name']: g for g in canonical['groups']}
    if set(g.name for g in reports) != set(spec):
        raise InvalidEvidence('group set changed from committed snapshot')
    for g in reports:
        expected = spec[g.name]
        if g.kind != expected['kind'] or sorted(g.members) != expected['members']:
            raise InvalidEvidence(f'{g.name}: membership/kind mismatch')
    result = robust_bounds(entities, reports, max_corrupt=max_corrupt_values,
                           max_nodes=max_nodes)
    return {
        'snapshot_sha256': digest_snapshot(canonical),
        'frame_version': canonical['frame_version'],
        'membership_check': 'matches_supplied_external_anchor',
        'anchor_independence': 'NOT_VERIFIED_BY_SOFTWARE',
        **result,
    }


def counterexample():
    entities = tuple('ABCDEF')
    original = [
        Group('g0', ('A','B','C'), 'count', 1),
        Group('g1', ('B','C','D','F'), 'or', 1),
        Group('g2', ('B','C'), 'count', 0),
        Group('g3', ('C','F'), 'count', 0),
        Group('g4', ('A','B','D'), 'or', 1),
        Group('g5', ('B','E','F'), 'count', 1),
        Group('g6', ('A','B','C','F'), 'or', 1),
    ]
    tampered = [Group(g.name, ('A','D') if g.name == 'g2' else g.members,
                      g.kind, g.value) for g in original]
    snapshot = snapshot_payload(entities, original, frame_version='synthetic-361')
    anchor = digest_snapshot(snapshot)
    honest = audited_bounds(snapshot, anchor, original)
    unanchored = robust_bounds(entities, tampered)
    try:
        audited_bounds(snapshot, anchor, tampered)
    except InvalidEvidence as e:
        tamper_rejected = str(e)
    else:
        raise AssertionError('tampering was not rejected')
    forged = snapshot_payload(entities, tampered, frame_version='synthetic-361')
    self_signed = audited_bounds(forged, digest_snapshot(forged), tampered)
    return {
        'true_outcomes': {'A':1,'B':0,'C':0,'D':1,'E':1,'F':0},
        'authentic_rate': [honest['lower_rate'], honest['upper_rate']],
        'tampered_unanchored_rate': [unanchored['lower_rate'], unanchored['upper_rate']],
        'independently_anchored_tamper_rejection': tamper_rejected,
        'self_signed_forgery_accepted_rate': [self_signed['lower_rate'],self_signed['upper_rate']],
        'trusted_digest': anchor,
        'tampered_group': 'g2',
        'old_members': ['B','C'],
        'new_members': ['A','D'],
    }


if __name__ == '__main__':
    print(json.dumps(counterexample(), indent=2, sort_keys=True))
