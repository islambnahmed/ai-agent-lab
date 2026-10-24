"""Precommitted opportunity-manifest reconciliation for bounded e-processes.

Research-only. An external, trustworthy authority must define opportunities and
anchor the commitment *before* observing outcomes. A public hash does not
authenticate outcome values or prove schedule completeness.
"""
from __future__ import annotations
import hashlib
import json
import math
from dataclasses import dataclass

LAMBDAS = (0.05, 0.1, 0.2, 0.4, 0.8)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def _hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _names(names):
    if type(names) not in (tuple, list) or not names or any(type(x) is not str or not x for x in names):
        raise ValueError('roster must contain nonempty strings')
    if len(set(names)) != len(names):
        raise ValueError('duplicate roster member')
    return tuple(names)


def manifest(experiment, candidates, slots):
    """Build a deterministic manifest from independently chosen scheduled slots.

    slots are pairs (source_namespace, immutable_source_id), NOT sequential
    counters generated from observed events. Caller must trust their origin.
    """
    if type(experiment) is not str or not experiment:
        raise ValueError('invalid experiment')
    roster = _names(candidates)
    if type(slots) not in (tuple, list) or not slots:
        raise ValueError('empty slots')
    ids = []
    for pair in slots:
        if type(pair) not in (tuple, list) or len(pair) != 2 or any(type(x) is not str or not x for x in pair):
            raise ValueError('invalid source slot')
        ids.append(list(pair))
    if len({tuple(x) for x in ids}) != len(ids):
        raise ValueError('duplicate source slot')
    return {'schema': 1, 'experiment': experiment, 'candidates': list(roster), 'slots': ids}


def commitment(m):
    return _hash(m)


def _check_manifest(m):
    if type(m) is not dict or set(m) != {'schema','experiment','candidates','slots'} or type(m['schema']) is not int or m['schema'] != 1:
        raise ValueError('invalid manifest schema')
    return manifest(m['experiment'], m['candidates'], m['slots'])


def _score(x):
    return type(x) in (int, float) and math.isfinite(x) and -1 <= x <= 1


@dataclass(frozen=True)
class Result:
    manifest_sha256: str
    total_opportunities: int
    missing_opportunities: int
    missing_scores: dict
    first_crossings: dict
    final_log_e: dict


def evaluate(m, expected_commitment, events, alpha=0.05, lambdas=LAMBDAS):
    """Fail-closed validation, then reconcile all scheduled slots in order.

    events are untrusted, so they cannot add/drop/relabel *slots*, but this
    routine cannot verify whether an event's reported score is truthful.
    """
    clean = _check_manifest(m)
    if type(expected_commitment) is not str or len(expected_commitment) != 64 or commitment(clean) != expected_commitment:
        raise ValueError('manifest commitment mismatch')
    if type(alpha) not in (float, int) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('invalid alpha')
    if type(lambdas) not in (tuple,list) or not lambdas or any(type(l) not in (int,float) or not math.isfinite(l) or not 0 <= l < 1 for l in lambdas):
        raise ValueError('invalid bets')
    if type(events) not in (list, tuple):
        raise ValueError('events must be a sequence')
    roster = tuple(clean['candidates'])
    expected = {tuple(s) for s in clean['slots']}
    by_slot = {}
    for ev in events:
        if type(ev) is not dict or set(ev) != {'source','slot','scores'}:
            raise ValueError('invalid event shape')
        key = (ev['source'],ev['slot'])
        if any(type(x) is not str for x in key) or key not in expected:
            raise ValueError('unregistered source slot')
        if key in by_slot:
            raise ValueError('duplicate source slot event')
        scores = ev['scores']
        if type(scores) is not dict or set(scores) - set(roster):
            raise ValueError('invalid scores roster')
        if any(v is not None and not _score(v) for v in scores.values()):
            raise ValueError('invalid score')
        by_slot[key] = scores
    logs = {n:[0.0]*len(lambdas) for n in roster}
    missing_scores = {n:0 for n in roster}
    crossings = {}
    threshold = -math.log(alpha/len(roster))
    for t,slot in enumerate(clean['slots'],1):
        scores = by_slot.get(tuple(slot),{})
        for n in roster:
            x = scores.get(n)
            if x is None:
                x = -1.0
                missing_scores[n] += 1
            for i,l in enumerate(lambdas):
                logs[n][i] += math.log1p(l*x)
            if n not in crossings and _logmeanexp(logs[n]) >= threshold:
                crossings[n] = t
    return Result(expected_commitment, len(clean['slots']), len(clean['slots'])-len(by_slot),
                  missing_scores, crossings, {n:_logmeanexp(logs[n]) for n in roster})


def _logmeanexp(logs):
    high = max(logs)
    return high + math.log(math.fsum(math.exp(x-high) for x in logs)/len(logs))


def naive_reindexed(events, candidates, alpha=0.05, lambdas=LAMBDAS):
    """Vulnerable comparison: assumes submitted events exhaust opportunities."""
    m = manifest('naive', candidates, [('reindexed',str(i)) for i in range(len(events))] or [('reindexed','empty')])
    rows = [{'source':'reindexed','slot':str(i),'scores':ev['scores']} for i,ev in enumerate(events)]
    return evaluate(m, commitment(m), rows, alpha, lambdas)
