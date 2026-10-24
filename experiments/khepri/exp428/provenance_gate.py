"""Research-only provenance-domain quorum, not identity/provenance authentication.

Witnesses sharing a declared upstream measurement domain get at most one vote.
An internally inconsistent domain abstains. A strict majority of declared
upstream domains must agree on every candidate/opportunity, or fail closed.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from quorum_gate import policy as witness_policy, canonical, _pair, score
from baseline_manifest_gate import evaluate as manifest_evaluate, commitment


def policy(experiment, candidates, slots, witness_domains):
    if type(witness_domains) is not dict or len(witness_domains) < 3:
        raise ValueError('need at least three witnesses with declared domains')
    if any(type(w) is not str or not w or type(d) is not str or not d
           for w, d in witness_domains.items()):
        raise ValueError('invalid witness/domain identifier')
    domains = set(witness_domains.values())
    if len(domains) < 2:
        raise ValueError('need at least two declared independent domains')
    base = witness_policy(experiment, candidates, slots, sorted(witness_domains),
                          len(witness_domains)//2+1)
    return {'schema':1, 'base_policy':base,
            'witness_domains':dict(sorted(witness_domains.items())),
            'domain_quorum':len(domains)//2+1, 'rule':'unanimous_domain_vote_v1'}


def policy_hash(p):
    return hashlib.sha256(canonical(p)).hexdigest()


@dataclass(frozen=True)
class Result:
    policy_sha256: str
    source_result: object
    domain_disagreements: int
    missing_domain_opportunities: int
    resolved_candidate_observations: int


def evaluate(p, expected_policy_hash, receipts, *, alpha=.05, lambdas=(.8,)):
    if type(p) is not dict or set(p) != {'schema','base_policy','witness_domains','domain_quorum','rule'}:
        raise ValueError('invalid policy')
    if type(expected_policy_hash) is not str or len(expected_policy_hash) != 64:
        raise ValueError('invalid policy commitment')
    base = p['base_policy']
    if type(base) is not dict or set(base) != {'schema','manifest','witnesses','quorum','metric'}:
        raise ValueError('invalid base policy')
    m = base['manifest']
    if type(m) is not dict or not {'experiment','candidates','slots'} <= set(m):
        raise ValueError('invalid manifest')
    clean = policy(m['experiment'], m['candidates'], m['slots'], p['witness_domains'])
    if p != clean or policy_hash(clean) != expected_policy_hash:
        raise ValueError('policy commitment mismatch')
    if type(receipts) not in (tuple,list):
        raise ValueError('invalid receipts')
    witnesses = clean['witness_domains']
    domains = sorted(set(witnesses.values()))
    candidates = tuple(clean['base_policy']['manifest']['candidates'])
    slots = {tuple(s) for s in clean['base_policy']['manifest']['slots']}
    seen = {}
    for r in receipts:
        if type(r) is not dict or set(r) != {'witness','source','slot','measurements'}:
            raise ValueError('invalid receipt')
        w,source,slot = r['witness'],r['source'],r['slot']
        if type(w) is not str or w not in witnesses or type(source) is not str or type(slot) is not str or (source,slot) not in slots:
            raise ValueError('unknown witness or slot')
        key = (w,source,slot)
        if key in seen:
            raise ValueError('duplicate receipt')
        obs = r['measurements']
        if type(obs) is not dict or set(obs) != set(candidates) or not all(_pair(v) for v in obs.values()):
            raise ValueError('invalid measurements')
        seen[key] = {c:tuple(obs[c]) for c in candidates}
    rows=[]
    disagreements=0
    missing=0
    for source,slot in clean['base_policy']['manifest']['slots']:
        votes={c:{} for c in candidates}
        for domain in domains:
            members = [w for w,d in witnesses.items() if d == domain and (w,source,slot) in seen]
            if not members:
                missing+=1
                continue
            for c in candidates:
                values={seen[(w,source,slot)][c] for w in members}
                if len(values)==1:
                    votes[c][domain]=next(iter(values))
                else:
                    disagreements+=1  # disagreement counts per candidate and slot
        scores={}
        for c in candidates:
            counts={}
            for pair in votes[c].values():
                counts[pair]=counts.get(pair,0)+1
            winners=[pair for pair,n in counts.items() if n >= clean['domain_quorum']]
            if len(winners)!=1:
                raise ValueError(f'no independent domain quorum for {source}/{slot}/{c}')
            scores[c]=score(winners[0])
        rows.append({'source':source,'slot':slot,'scores':scores})
    result=manifest_evaluate(clean['base_policy']['manifest'],
                             commitment(clean['base_policy']['manifest']),
                             rows,alpha=alpha,lambdas=lambdas)
    return Result(expected_policy_hash,result,disagreements,missing,len(rows)*len(candidates))
