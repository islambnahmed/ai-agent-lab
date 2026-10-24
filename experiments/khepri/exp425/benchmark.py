"""Seeded synthetic opportunity-ledger experiment; no external data."""
import json, random, math
from opportunity_gate import OpportunityGate, DEFAULT_LAMBDAS

SEED=425
TRIALS=600
ROUNDS=100
AGENTS=8
ALPHA=.05

def run(trials=TRIALS):
    scenarios={'seo_null_hide_losses':('null','losses'),
               'finance_null_hide_losses_shared_shock':('shared','losses'),
               'seo_positive_full':('positive','full'),
               'seo_positive_hide_random_half':('positive','random')}
    out={'seed':SEED,'trials':trials,'rounds':ROUNDS,'agents':AGENTS,'alpha':ALPHA,'synthetic':True,'scenarios':{}}
    for index,(scenario,(process,missing)) in enumerate(scenarios.items()):
        rng=random.Random(SEED+index*1000)
        tally={'naive_any_cross':0,'safe_any_cross':0,'naive_mean_missing':0,'safe_mean_missing':0}
        for _ in range(trials):
            names=[f'agent{j}' for j in range(AGENTS)]
            safe=OpportunityGate(names,alpha=ALPHA)
            naive_logs={name:[0.]*len(DEFAULT_LAMBDAS) for name in names}
            naive_hit=False
            for t in range(1,ROUNDS+1):
                common=1 if rng.random()<.5 else -1
                obs={}
                for name in names:
                    if process=='shared':
                        x=common if rng.random()<.85 else (1 if rng.random()<.5 else -1)
                    else:
                        x=1 if rng.random()<(0.68 if process=='positive' else .5) else -1
                    seen=(missing=='full' or (missing=='losses' and x>0) or (missing=='random' and rng.random()<.5))
                    if seen:obs[name]=x
                    # Naive missing -> zero, as a frequent 'neutral missing' shortcut.
                    nx=x if seen else 0
                    logs=naive_logs[name]
                    for i,lam in enumerate(DEFAULT_LAMBDAS):logs[i]+=math.log1p(lam*nx)
                    maximum=max(logs)
                    log_e=maximum+math.log(math.fsum(math.exp(z-maximum) for z in logs)/len(logs))
                    if log_e>=-math.log(ALPHA/AGENTS):naive_hit=True
                safe.observe(t,obs)
            tally['naive_any_cross']+=int(naive_hit)
            tally['safe_any_cross']+=int(bool(safe.crossings))
            tally['safe_mean_missing']+=sum(safe.missing_counts.values())/(ROUNDS*AGENTS)
        out['scenarios'][scenario]={
            'process':process,'observation_policy':missing,
            'naive_any_cross_count':tally['naive_any_cross'],
            'safe_any_cross_count':tally['safe_any_cross'],
            'naive_any_cross_rate':round(tally['naive_any_cross']/trials,5),
            'safe_any_cross_rate':round(tally['safe_any_cross']/trials,5),
            'missing_fraction':round(tally['safe_mean_missing']/trials,5)}
    return out

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
