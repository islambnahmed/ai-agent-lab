"""Seeded, entirely synthetic experiment; no vendor calls."""
import json
from pathlib import Path
from random import Random
from statistics import mean
from adaptive_planner import Tool, Model, pair_stats, optimize, static_utility, adaptive_policy

SEED=405
N=2000

def case(rng, domain):
    seo=domain=='seo'
    r=15 if seo else 10
    shock=rng.uniform(.05,.32)
    calm={'x':rng.uniform(.005,.08),'y':rng.uniform(.01,.12)}
    shocked={'x':rng.uniform(.60,.995),'y':rng.uniform(.01,.25) if rng.random()<.7 else rng.uniform(.5,.95)}
    model=Model(shock,calm,shocked)
    scale=1.5 if seo else 1.
    tools={
      'a':Tool('a','x',rng.uniform(.93,.999),rng.uniform(.005,.18),rng.uniform(.08,.55)*scale),
      'b':Tool('b','x',rng.uniform(.93,.999),rng.uniform(.005,.18),rng.uniform(.08,.65)*scale),
      'c':Tool('c','y',rng.uniform(.75,.98),rng.uniform(.04,.45),rng.uniform(.25,1.6)*scale),
    }
    return tools,model,r

def actual_adaptive(tools,model,reward,first,second,deadline):
    a=tools[first]
    pa=sum(w*(a.outage if states[a.domain] else a.healthy) for w,states in __import__('adaptive_planner').worlds(model))
    score=reward*pa-a.cost
    if second:
        _,fail_b,_=pair_stats(tools,model,first,second)
        score+=reward*deadline*fail_b-(1-pa)*tools[second].cost
    return score

def naive_policy(tools,model,reward,deadline):
    # Wrong policy: uses marginal B success rather than B success given A failure.
    # Also chooses first tool under the same wrong scoring model.
    candidates=[]
    for first in sorted(tools):
        p_a=sum(w*(__import__('adaptive_planner').conditional_tool_probability(tools[first],s))
                for w,s in __import__('adaptive_planner').worlds(model))
        gains={}
        for second in sorted(tools):
            if second==first:continue
            _,_,p_b=pair_stats(tools,model,first,second)
            gains[second]=reward*deadline*p_b-tools[second].cost
        fallback=max(gains,key=gains.get)
        if gains[fallback]<=0:fallback=None
        guessed=reward*p_a-tools[first].cost+(1-p_a)*(gains[fallback] if fallback else 0)
        candidates.append((guessed,first,fallback))
    _,first,second=max(candidates)
    return first,second

def simulate(tools,model,reward,first,second,deadline,n,seed):
    rng=Random(seed)
    utility=0
    for _ in range(n):
        shock=rng.random()<model.shock
        rates=model.shocked if shock else model.calm
        outages={d:rng.random()<q for d,q in rates.items()}
        def succeeded(name):
            t=tools[name]
            return rng.random()<(t.outage if outages[t.domain] else t.healthy)
        value=-tools[first].cost
        if succeeded(first):
            value+=reward
        elif second:
            value-=tools[second].cost
            if succeeded(second) and rng.random()<deadline:
                value+=reward
        utility+=value
    return utility/n

def run_family(domain,deadline):
    rng=Random(SEED+ (100 if domain=='seo' else 0)+(1 if deadline<1 else 0))
    gains=[]; positive=0; regret_naive=[]; bad_fallback=0; regret_shock=[]; mc=[]; examples=[]
    for i in range(N):
        tools,model,reward=case(rng,domain)
        best=optimize(tools,model,reward,deadline)
        gains.append(best['gain'])
        positive+=best['gain']>1e-9
        nf,ns=naive_policy(tools,model,reward,deadline)
        naive_true=actual_adaptive(tools,model,reward,nf,ns,deadline)
        regret_naive.append(best['adaptive']['utility']-naive_true)
        bad_fallback+=(nf!=best['adaptive']['first'] or ns!=best['adaptive']['fallback'])
        # Deliberately wrong shock estimate, choose under wrong model, score under true.
        wrong=Model(model.shock*.5,model.calm,model.shocked)
        chosen=optimize(tools,wrong,reward,deadline)['adaptive']
        regret_shock.append(best['adaptive']['utility']-actual_adaptive(tools,model,reward,chosen['first'],chosen['fallback'],deadline))
        if best['gain']>0.15 and len(examples)<1:
            examples.append({'case_index':i,'shock':round(model.shock,4),'deadline':deadline,
                             'static_choice':best['static']['tools'],'adaptive_first':best['adaptive']['first'],
                             'adaptive_fallback':best['adaptive']['fallback'],
                             'gain':round(best['gain'],5)})
        if i<6:
            policy=best['adaptive']
            estimate=simulate(tools,model,reward,policy['first'],policy['fallback'],deadline,20000,SEED+i+(1000 if domain=='seo' else 0))
            mc.append(abs(estimate-policy['utility']))
    return {'n':N,'adaptive_beats_best_static':positive,'mean_adaptive_minus_static':round(mean(gains),6),
            'max_adaptive_minus_static':round(max(gains),6),'min_adaptive_minus_static':round(min(gains),6),
            'marginal_policy_disagreements':bad_fallback,'mean_marginal_policy_regret':round(mean(regret_naive),6),
            'max_marginal_policy_regret':round(max(regret_naive),6),
            'half_shock_wrong_policy_cases':sum(x>1e-9 for x in regret_shock),
            'mean_half_shock_policy_regret':round(mean(regret_shock),6),
            'max_mc_abs_utility_error_first_6':round(max(mc),6),'example':examples[0] if examples else None}

def focal():
    tools={'a':Tool('a','x',.99,.05,.2),'b':Tool('b','x',.995,.05,.2),'c':Tool('c','y',.82,.2,.7)}
    model=Model(.2,{'x':.02,'y':.1},{'x':.98,'y':.1})
    pa,fail_b,pb=pair_stats(tools,model,'a','b')
    _,fail_c,pc=pair_stats(tools,model,'a','c')
    return {'p_b_marginal':round(pb,6),'p_c_marginal':round(pc,6),
            'p_b_given_a_failed':round(fail_b/(1-pa),6),'p_c_given_a_failed':round(fail_c/(1-pa),6),
            'adaptive_after_a':adaptive_policy(tools,model,10,'a')['fallback'],
            'optimal_deadline_1':optimize(tools,model,10,1)['adaptive'],
            'optimal_deadline_0_1':optimize(tools,model,10,.1)}

if __name__=='__main__':
    results={'seed':SEED,'focal':focal(),'families':{d:{str(deadline):run_family(d,deadline) for deadline in (1.,.3)} for d in ('gold','seo')}}
    Path('results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(results,indent=2))
