"""Deterministic stress test, not a calibrated statistical error estimate."""
import json
import random
from provenance_gate import policy,policy_hash,evaluate
from quorum_gate import policy as old_policy,policy_hash as old_hash,evaluate as old_evaluate

DOM={'x1':'X','x2':'X','x3':'X','y':'Y','z':'Z'}
SCENARIOS=('honest','corrupt_one_domain','corrupt_two_domains','split_domain_labels','one_domain_missing')

def run(domain,seed,trials=200):
    rng=random.Random(seed)
    slots=80 if domain=='seo' else 60
    candidates=['agentA'] if domain=='seo' else ['agentA','agentB']
    roster=[('crawl' if domain=='seo' else 'ledger',str(i)) for i in range(slots)]
    p=policy(domain,candidates,roster,DOM)
    q=old_policy(domain,candidates,roster,list(DOM),3)
    results={s:{'old_crossings':0,'new_crossings':0,'new_rejections':0} for s in SCENARIOS}
    for _ in range(trials):
        signs=[1,-1]*(slots//2)
        rng.shuffle(signs)
        for scenario in SCENARIOS:
            receipts=[]
            for i,(source,slot) in enumerate(roster):
                truth=[0,1] if signs[i]>0 else [1,0]
                if domain=='finance':truth=[5000,6000] if signs[i]>0 else [6000,5000]
                fake=[0,1] if domain=='seo' else [5000,10000]
                for w,origin in DOM.items():
                    if scenario=='one_domain_missing' and origin=='Z':continue
                    corrupt=origin=='X' and scenario in ('corrupt_one_domain','corrupt_two_domains','split_domain_labels','one_domain_missing')
                    corrupt|=origin=='Y' and scenario=='corrupt_two_domains'
                    receipts.append({'witness':w,'source':source,'slot':slot,
                                     'measurements':{c:(fake if corrupt else truth) for c in candidates}})
            old=old_evaluate(q,old_hash(q),receipts)
            results[scenario]['old_crossings']+=int(bool(old.source_result.first_crossings))
            actual_policy=p
            if scenario=='split_domain_labels':
                actual_policy=policy(domain,candidates,roster,{'x1':'X1','x2':'X2','x3':'X3','y':'Y','z':'Z'})
            try:
                new=evaluate(actual_policy,policy_hash(actual_policy),receipts)
                results[scenario]['new_crossings']+=int(bool(new.source_result.first_crossings))
            except ValueError as exc:
                if 'no independent domain quorum' not in str(exc):raise
                results[scenario]['new_rejections']+=1
    return {'trials':trials,'slots':slots,'candidates':len(candidates),'results':results}

if __name__=='__main__':
    print(json.dumps({'seo':run('seo',42801),'finance':run('finance',42802)},indent=2,sort_keys=True))
