"""Deterministic synthetic missing-opportunity and forgery comparison."""
import json
import random
from manifest_gate import manifest,commitment,evaluate,naive_reindexed


def trial(domain, n, seed, attack):
    rng=random.Random(seed)
    roster=['agentA','agentB','agentC','agentD']
    slots=[(domain,f'{domain}-scheduled-{i:03d}') for i in range(n)]
    m=manifest(f'{domain}-study',roster,slots)
    # Balanced sign pairs per candidate. Under this deterministic design,
    # there is no positive overall effect. This is NOT a stochastic FWER test.
    scores={name:[1,-1]*(n//2) for name in roster}
    for name in roster:
        rng.shuffle(scores[name])
    events=[]
    for i,(source,slot) in enumerate(slots):
        row={name:scores[name][i] for name in roster}
        if attack=='drop_negative_primary' and row['agentA']<0:
            continue
        if attack=='forge_primary':
            row['agentA']=1
        events.append({'source':source,'slot':slot,'scores':row})
    checked=evaluate(m,commitment(m),events)
    naive=naive_reindexed(events,roster)
    return {'missing':checked.missing_opportunities,'naive_primary':int('agentA' in naive.first_crossings),
            'reconciled_primary':int('agentA' in checked.first_crossings)}


def run(trials=300,n=100):
    out={}
    for domain in ('seo','finance'):
        for attack in ('drop_negative_primary','forge_primary','complete'):
            rows=[trial(domain,n,seed,attack) for seed in range(trials)]
            out[f'{domain}/{attack}']={
                'trials':trials,'opportunities_per_trial':n,
                'mean_missing_rounds':sum(r['missing'] for r in rows)/trials,
                'naive_crossings':sum(r['naive_primary'] for r in rows),
                'reconciled_crossings':sum(r['reconciled_primary'] for r in rows)}
    return out

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
