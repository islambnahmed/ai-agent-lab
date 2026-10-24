"""Paired synthetic evaluation of conflicting refresh objectives."""
import json,math,random,statistics
from reward_audit import make_schedule,replay,sample_counts

POLICIES=('censored','naive','oracle','round_robin','freshness_oracle')
DOMAINS={
 'seo':{'impacts':[10,8,7,5,3], 'rates':[.02,.05,.12,.45,1.8]},
 'feed':{'impacts':[7,10,8,6,4], 'rates':[.03,.2,.5,1.2,2.8]},
 'high_churn':{'impacts':[12,10,9,8,7], 'rates':[.03,.06,.2,1.4,2.5]},
}

def ci95(xs):
    n=len(xs);mean=statistics.mean(xs)
    return [mean-1.96*statistics.stdev(xs)/math.sqrt(n),mean+1.96*statistics.stdev(xs)/math.sqrt(n)]

def evaluate(seed=414,reps=150,days=90,budget=2):
    rng=random.Random(seed);out={}
    for name,scenario in DOMAINS.items():
        rows=[]
        for _ in range(reps):
            counts=sample_counts(scenario['rates'],days,rng)
            rows.append({p:replay(scenario['impacts'],counts,
                    make_schedule(scenario['impacts'],scenario['rates'],counts,p,budget))
                    for p in POLICIES})
        metrics=('binary_hits','timely_events','stale_days','stale_days_after')
        stats={}
        for metric in metrics:
            means={p:statistics.mean(r[p][metric] for r in rows) for p in POLICIES}
            best=max(means,key=means.get) if not metric.startswith('stale_days') else min(means,key=means.get)
            delta=[r['censored'][metric]-r['naive'][metric] for r in rows]
            stats[metric]={'means':means,'best':best,
                    'censored_minus_naive':statistics.mean(delta),
                    'paired_ci95':ci95(delta),
                    'censored_wins':sum(x>0 for x in delta) if not metric.startswith('stale_days') else sum(x<0 for x in delta)}
        out[name]={'reps':reps,'days':days,'budget':budget,'metrics':stats}
    return {'seed':seed,'domains':out}

if __name__=='__main__':
    results=evaluate()
    with open('results.json','w') as f:json.dump(results,f,indent=2,sort_keys=True)
    print(json.dumps(results,indent=2,sort_keys=True))
