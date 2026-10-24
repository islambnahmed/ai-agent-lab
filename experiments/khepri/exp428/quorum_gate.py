"""Research-only quorum reconciliation of independent outcome receipts.

Trust boundary: witness identities and their channels must be authenticated by a
separate system. A hash commitment is not a signature. A strict majority of
independent witnesses must report identical raw observations per opportunity.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from baseline_manifest_gate import manifest as source_manifest, commitment, evaluate as baseline_evaluate


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def policy(experiment, candidates, slots, witnesses, quorum):
    m = source_manifest(experiment, candidates, slots)
    if type(witnesses) not in (tuple, list) or len(witnesses) < 3:
        raise ValueError('need at least three witnesses')
    if any(type(w) is not str or not w for w in witnesses) or len(set(witnesses)) != len(witnesses):
        raise ValueError('invalid witness identities')
    if type(quorum) is not int or not (len(witnesses)//2 < quorum <= len(witnesses)):
        raise ValueError('quorum must be a strict majority')
    return {'schema': 1, 'manifest': m, 'witnesses': list(witnesses),
            'quorum': quorum, 'metric': 'bounded_pair_v1'}


def policy_hash(p):
    return hashlib.sha256(canonical(p)).hexdigest()


def _pair(v):
    return (type(v) in (tuple, list) and len(v) == 2
            and all(type(x) is int and 0 <= x <= 10000 for x in v))


def score(pair):
    before, after = pair
    return (after-before)/max(1, before, after)


@dataclass(frozen=True)
class QuorumResult:
    policy_sha256: str
    source_result: object
    dissenting_witness_values: int
    missing_witness_slots: int
    resolved_candidate_observations: int


def evaluate(p, expected_policy_hash, receipts, *, alpha=0.05, lambdas=(0.8,)):
    """Use witness quorum only, never untrusted agent-submitted score rows.

    Any missing majority blocks *all* conclusions. Duplicate, unknown, and
    malformed receipts are rejected. Caller must independently trust witness
    identity binding and the expected policy hash; no authentication here.
    """
    if type(p) is not dict or set(p) != {'schema','manifest','witnesses','quorum','metric'}:
        raise ValueError('invalid policy shape')
    if type(expected_policy_hash) is not str or len(expected_policy_hash) != 64:
        raise ValueError('invalid expected policy hash')
    clean = policy(p['manifest']['experiment'], p['manifest']['candidates'],
                   p['manifest']['slots'], p['witnesses'], p['quorum'])
    if p != clean or p['schema'] != 1 or p['metric'] != 'bounded_pair_v1' or policy_hash(clean) != expected_policy_hash:
        raise ValueError('policy commitment mismatch')
    if type(receipts) not in (list, tuple):
        raise ValueError('invalid receipt sequence')
    witnesses = set(clean['witnesses'])
    candidates = tuple(clean['manifest']['candidates'])
    slots = {tuple(s) for s in clean['manifest']['slots']}
    seen = {}
    for r in receipts:
        if type(r) is not dict or set(r) != {'witness','source','slot','measurements'}:
            raise ValueError('invalid receipt shape')
        w, source, slot = r['witness'], r['source'], r['slot']
        if type(w) is not str or w not in witnesses or type(source) is not str or type(slot) is not str or (source,slot) not in slots:
            raise ValueError('unknown witness or slot')
        key = (w,source,slot)
        if key in seen:
            raise ValueError('duplicate witness-slot receipt')
        m = r['measurements']
        if type(m) is not dict or set(m) != set(candidates) or not all(_pair(v) for v in m.values()):
            raise ValueError('invalid raw measurement')
        seen[key] = {c: tuple(m[c]) for c in candidates}
    dissent = 0
    missing = 0
    trusted_rows = []
    for source,slot in clean['manifest']['slots']:
        present = [seen[(w,source,slot)] for w in clean['witnesses'] if (w,source,slot) in seen]
        missing += len(witnesses)-len(present)
        values = {}
        for c in candidates:
            counts = {}
            for m in present:
                pair = m[c]
                counts[pair] = counts.get(pair,0)+1
            winners = [pair for pair,n in counts.items() if n >= clean['quorum']]
            if len(winners) != 1:
                raise ValueError(f'no independent quorum for {source}/{slot}/{c}')
            winner = winners[0]
            dissent += sum(m[c] != winner for m in present)
            values[c] = score(winner)
        trusted_rows.append({'source':source,'slot':slot,'scores':values})
    result = baseline_evaluate(clean['manifest'], commitment(clean['manifest']), trusted_rows,
                               alpha=alpha,lambdas=lambdas)
    return QuorumResult(expected_policy_hash,result,dissent,missing,len(trusted_rows)*len(candidates))
