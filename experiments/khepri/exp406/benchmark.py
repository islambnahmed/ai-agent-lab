"""Seeded synthetic uncertainty-set benchmark; no external data or services."""
import json
import random
from robust_planner import Tool, Model, choose, utility


def make_case(rng, regime):
    # Three tools; A/B share failure domain X, C uses Y.
    if regime == 'gold':
        reward, deadline = 10., rng.uniform(.3,1)
        costs=[rng.uniform(.1,1.3),rng.uniform(.1,1.3),rng.uniform(.1,1.6)]
    else:
        reward, deadline = 15., rng.uniform(.2,.95)
        costs=[rng.uniform(.3,2.0),rng.uniform(.3,2.0),rng.uniform(.3,2.3)]
    tools={'a':Tool('a','x',rng.uniform(.88,.995),rng.uniform(.01,.18),costs[0]),
           'b':Tool('b','x',rng.uniform(.88,.995),rng.uniform(.01,.18),costs[1]),
           'c':Tool('c','y',rng.uniform(.78,.98),rng.uniform(.05,.3),costs[2])}
    cx=rng.uniform(.005,.13);cy=rng.uniform(.005,.13)
    sx=rng.uniform(.65,.99);sy=rng.uniform(.10,.92)
    shock=rng.uniform(.05,.5)
    models=[Model(shock,{'x':cx,'y':cy},{'x':sx,'y':sy}),
            Model(max(.005,shock*.3),{'x':cx,'y':cy},{'x':sx,'y':sy}),
            Model(min(.95,shock*2.3),{'x':cx,'y':cy},{'x':sx,'y':sy}),
            Model(shock,{'x':cx,'y':cy},{'x':sx,'y':min(.99,sy+.28)})]
    # Deliberately outside the uncertainty set: much worse Y outages.
    outside=Model(.98,{'x':cx,'y':cy},{'x':sx,'y':.999})
    return tools,models,outside,reward,deadline


def run(seed=406, per_regime=2000):
    rng=random.Random(seed)
    results={'seed':seed,'per_regime':per_regime,'regimes':{}}
    for regime in ('gold','seo'):
        improvements=[]; sacrifices=[]; outside_losses=[]
        different=0; worst_improved=0; examples=[]
        for i in range(per_regime):
            tools,models,outside,reward,deadline=make_case(rng,regime)
            r=choose(tools,models,reward,deadline)
            improvement=r['robust_worst']-r['nominal_worst']
            sacrifice=r['nominal_values'][0]-r['robust_values'][0]
            outside_loss=utility(tools,outside,reward,deadline,r['nominal'])-utility(tools,outside,reward,deadline,r['robust'])
            improvements.append(improvement);sacrifices.append(sacrifice);outside_losses.append(outside_loss)
            different+=r['nominal']!=r['robust']
            worst_improved+=improvement>1e-8
            if improvement>.25 and sacrifice>.05 and len(examples)<2:
                examples.append({'case':i,'nominal':r['nominal'],'robust':r['robust'],
                                 'nominal_values':[round(x,6) for x in r['nominal_values']],
                                 'robust_values':[round(x,6) for x in r['robust_values']],
                                 'worst_gain':round(improvement,6),'nominal_sacrifice':round(sacrifice,6),
                                 'outside_nominal_minus_robust':round(outside_loss,6),
                                 'deadline':round(deadline,5),
                                 'tools':{n:vars(t) for n,t in tools.items()},
                                 'models':[vars(m) for m in models]})
        results['regimes'][regime]={
            'scenarios':per_regime,'policies_per_case':13,'model_candidates':4,
            'different_policy_count':different,'robust_strictly_improves_worst_count':worst_improved,
            'mean_worst_case_improvement':sum(improvements)/per_regime,
            'max_worst_case_improvement':max(improvements),
            'mean_nominal_sacrifice':sum(sacrifices)/per_regime,
            'max_nominal_sacrifice':max(sacrifices),
            'out_of_set_robust_worse_count':sum(v>1e-8 for v in outside_losses),
            'out_of_set_max_robust_loss':max(outside_losses),
            'examples':examples}
    return results


if __name__=='__main__':
    with open('results.json','w',encoding='utf8') as f:json.dump(run(),f,indent=2,ensure_ascii=False)
    r=run()
    for k,v in r['regimes'].items():
        print(k,{a:round(b,6) if isinstance(b,float) else b for a,b in v.items() if a!='examples'})
        print('examples',len(v['examples']))
