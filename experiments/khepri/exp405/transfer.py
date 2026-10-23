"""Transfer test: four SEO retrieval tools across three failure domains."""
import json
from random import Random
from statistics import mean
from pathlib import Path
from adaptive_planner import Tool, Model, optimize
from benchmark import naive_policy, actual_adaptive, simulate

N=2000
SEED=40577

def seo_case(rng):
    # Different topology and distributions from the three-tool gold/SEO benchmark.
    model=Model(rng.uniform(.02,.16),
                {'x':rng.uniform(.02,.09),'y':rng.uniform(.005,.04),'z':rng.uniform(.01,.05)},
                {'x':rng.uniform(.75,.99),'y':rng.uniform(.35,.65),'z':rng.uniform(.02,.2)})
    tools={
        'a':Tool('a','x',rng.uniform(.95,.999),rng.uniform(.01,.1),rng.uniform(.1,.4)),
        'b':Tool('b','x',rng.uniform(.91,.98),rng.uniform(.02,.3),rng.uniform(.05,.25)),
        'c':Tool('c','y',rng.uniform(.82,.96),rng.uniform(.15,.4),rng.uniform(.35,1.1)),
        'd':Tool('d','z',rng.uniform(.72,.93),rng.uniform(.3,.6),rng.uniform(.8,2.2)),
    }
    return tools,model,18

def run(deadline):
    rng=Random(SEED+int(deadline*100))
    gain=[]; naive_regret=[]; disagreements=0; mc=[]
    for i in range(N):
        tools,model,reward=seo_case(rng)
        opt=optimize(tools,model,reward,deadline)
        gain.append(opt['gain'])
        f,b=naive_policy(tools,model,reward,deadline)
        disagreements+=(f!=opt['adaptive']['first'] or b!=opt['adaptive']['fallback'])
        naive_regret.append(opt['adaptive']['utility']-actual_adaptive(tools,model,reward,f,b,deadline))
        if i<6:
            p=opt['adaptive']
            mc.append(abs(simulate(tools,model,reward,p['first'],p['fallback'],deadline,25000,SEED+i)-p['utility']))
    return {'n':N,'adaptive_beats_static':sum(x>1e-9 for x in gain),
            'mean_adaptive_minus_static':round(mean(gain),6),
            'marginal_policy_disagreements':disagreements,
            'mean_marginal_policy_regret':round(mean(naive_regret),6),
            'mc_max_abs_utility_error_first_6':round(max(mc),6)}

if __name__=='__main__':
    out={'seed':SEED,'description':'four SEO retrieval tools across three failure domains',
         'deadline_1':run(1.),'deadline_0_25':run(.25)}
    Path('transfer_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
