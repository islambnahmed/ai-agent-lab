"""Seeded synthetic Monte Carlo: multi-agent sequential false discoveries."""
import json
import random
from multiplicity_gate import FamilywiseGate

SEED = 424
TRIALS = 1200
ROUNDS = 100
CANDIDATES = 12

def simulate(replicates=TRIALS):
    scenarios = {
        'seo_independent_all_null': ('independent', 0),
        'finance_shared_shock_all_null': ('shared', 0),
        'seo_independent_two_positive': ('independent', 2),
        'finance_shared_shock_two_positive': ('shared', 2),
    }
    result = {'seed': SEED, 'replicates': replicates, 'rounds': ROUNDS,
              'candidates': CANDIDATES, 'alpha': .05, 'synthetic': True,
              'scenarios': {}}
    for idx,(name,(dependence,n_positive)) in enumerate(scenarios.items()):
        rng=random.Random(SEED+idx*1000)
        tallies={'unadjusted_any_null':0,'fixed_any_null':0,'online_any_null':0,
                 'unadjusted_all_positive':0,'fixed_all_positive':0,'online_all_positive':0}
        for _ in range(replicates):
            gates={
                'fixed': FamilywiseGate(alpha=.05, slots=CANDIDATES),
                'online': FamilywiseGate(alpha=.05, mode='online'),
            }
            unadjusted=[FamilywiseGate(alpha=.05,slots=1) for _ in range(CANDIDATES)]
            for j in range(CANDIDATES):
                name_j=f'a{j}'
                gates['fixed'].register(name_j)
                gates['online'].register(name_j)
                unadjusted[j].register(name_j)
            for t in range(1,ROUNDS+1):
                shared = 1 if rng.random()<.5 else -1
                gains={}
                for j in range(CANDIDATES):
                    if j<n_positive:
                        x=1 if rng.random()<.68 else -1
                    elif dependence=='shared':
                        x=shared if rng.random()<.8 else (1 if rng.random()<.5 else -1)
                    else:
                        x=1 if rng.random()<.5 else -1
                    gains[f'a{j}']=x
                    unadjusted[j].observe(t,{f'a{j}':x})
                gates['fixed'].observe(t,gains)
                gates['online'].observe(t,gains)
            for label, flagged in [('unadjusted',{f'a{j}' for j,g in enumerate(unadjusted) if g.crossings}),
                                   ('fixed',set(gates['fixed'].crossings)),
                                   ('online',set(gates['online'].crossings))]:
                tallies[label+'_any_null']+=any(int(x[1:])>=n_positive for x in flagged)
                if n_positive:
                    tallies[label+'_all_positive']+=all(f'a{j}' in flagged for j in range(n_positive))
        result['scenarios'][name]={'dependence':dependence,'positive_agents':n_positive,
                                  'counts':tallies,
                                  'rates':{k:round(v/replicates,5) for k,v in tallies.items()}}
    persistent_counts={'positive_global_shock_crosses':0,'negative_global_shock_crosses':0}
    for sign in (1,-1):
        g=FamilywiseGate(alpha=.05,slots=CANDIDATES)
        for j in range(CANDIDATES):g.register(f'a{j}')
        for t in range(1,ROUNDS+1):g.observe(t,{f'a{j}':sign for j in range(CANDIDATES)})
        persistent_counts['positive_global_shock_crosses' if sign==1 else 'negative_global_shock_crosses']=int(bool(g.crossings))
    selected=FamilywiseGate(alpha=.05,slots=CANDIDATES)
    for j in range(CANDIDATES):selected.register(f'a{j}')
    for t in range(1,ROUNDS+1):
        selected.observe(t,{f'a{j}':1 for j in range(CANDIDATES)} if t%2 else {})
    result['counterexamples']={
        'global_shock_unconditional_false_positive_probability':.5,
        'global_shock_sign_outcomes':persistent_counts,
        'selective_positive_only_logging_any_rejection':bool(selected.crossings),
        'explanation':'Both violate conditional-null assumptions; no FWER guarantee applies.'}
    return result

if __name__=='__main__':
    print(json.dumps(simulate(),indent=2,sort_keys=True))
