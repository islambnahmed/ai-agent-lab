"""Deterministic adversarial stress test, not a statistical calibration study."""
import copy
import json
import random
from baseline_manifest_gate import evaluate as baseline_evaluate,commitment
from quorum_gate import policy,policy_hash,evaluate


def trial(domain, trial_index, slots_n):
    rng=random.Random(427_000+trial_index+(0 if domain=='seo' else 100_000))
    source='crawl' if domain=='seo' else 'ledger'
    candidates=['agentA'] if domain=='seo' else ['agentA','agentB']
    slots=[(source,f'{domain}-{trial_index}-{i}') for i in range(slots_n)]
    p=policy(domain,candidates,slots,['w1','w2','w3'],2)
    anchor=policy_hash(p)
    # Balanced +/- signs, randomized within each pair. This ensures no genuine
    # advantage; not an IID Bernoulli-null false-positive-rate experiment.
    signs=[]
    for _ in range(slots_n//2):
        pair=[-1,1];rng.shuffle(pair);signs.extend(pair)
    def raw(s):
        if domain=='seo':return [0,1] if s>0 else [1,0]
        return [1000,1001] if s>0 else [1001,1000]
    rows=[]
    for w in p['witnesses']:
        for i,(s,id_) in enumerate(slots):
            values={'agentA':raw(signs[i])}
            if domain=='finance':values['agentB']=[1000,1000]
            rows.append({'witness':w,'source':s,'slot':id_,'measurements':values})
    forged_agent_rows=[{'source':s,'slot':id_,'scores':{'agentA':1,**({'agentB':0} if domain=='finance' else {})}}
                       for s,id_ in slots]
    baseline=baseline_evaluate(p['manifest'],commitment(p['manifest']),forged_agent_rows,lambdas=(.8,))
    scenarios={
        'honest':copy.deepcopy(rows),
        'one_poisoned_witness':copy.deepcopy(rows),
        'two_colluding_witnesses':copy.deepcopy(rows),
        'one_honest_witness_offline':[copy.deepcopy(r) for r in rows if r['witness']!='w3'],
        'offline_plus_poisoned':[copy.deepcopy(r) for r in rows if r['witness']!='w2'],
    }
    for name,rec in scenarios.items():
        for r in rec:
            poison = ((name=='one_poisoned_witness' and r['witness']=='w3')
                      or (name=='two_colluding_witnesses' and r['witness'] in ('w2','w3'))
                      or (name=='offline_plus_poisoned' and r['witness']=='w3'))
            if poison:r['measurements']['agentA']=[0,10000]
    out={'baseline_forged_agent':int('agentA' in baseline.first_crossings)}
    for name,rec in scenarios.items():
        try:
            result=evaluate(p,anchor,rec,lambdas=(.8,))
            out[name]={'crossing':int('agentA' in result.source_result.first_crossings),
                       'rejected':0,'dissent':result.dissenting_witness_values}
        except ValueError as exc:
            if 'no independent quorum' not in str(exc):raise
            out[name]={'crossing':0,'rejected':1,'dissent':0}
    return out


def benchmark(trials=200):
    results={}
    for domain,n in [('seo',80),('finance',60)]:
        total={}
        for i in range(trials):
            r=trial(domain,i,n)
            for name,value in r.items():
                if isinstance(value,int):
                    total.setdefault(name,{'crossing':0})['crossing']+=value
                else:
                    t=total.setdefault(name,{'crossing':0,'rejected':0,'dissent':0})
                    for k,v in value.items():t[k]+=v
        results[domain]={'trials':trials,'opportunities_per_trial':n,'outcomes':total}
    return results

if __name__=='__main__':print(json.dumps(benchmark(),indent=2,sort_keys=True))
