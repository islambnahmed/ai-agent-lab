"""Seeded synthetic stress test of common-shock dependence; no live vendors."""
import json
import random
from pathlib import Path
from statistics import mean
from planner import Tool, Plan
from joint_planner import ShockModel, joint_success, independent_success, select, monte_carlo_joint

SEED = 404
N = 2000


def make_case(domain, architecture, rng):
    is_gold = domain == 'gold'
    reward = 10.0 if is_gold else 12.0
    shock = rng.uniform(.07, .33) if is_gold else rng.uniform(.05, .28)
    low_a, low_b = rng.uniform(.001,.05), rng.uniform(.001,.05)
    high_a, high_b = rng.uniform(.65,.99), rng.uniform(.65,.99)
    q_c = rng.uniform(.01,.12)
    if architecture == 'parallel':
        healthy_a = rng.uniform(.95,.999)
        outage_a = rng.uniform(.005,.15)
        healthy_c = rng.uniform(.90,.99)
        outage_c = rng.uniform(.08,.45)
        cost_ab = rng.uniform(.18,.60)
        cost_c = rng.uniform(.6,1.6)
        plans = (Plan('pair',(('a','b'),)), Plan('single',(('c',),)))
    else:
        healthy_a = rng.uniform(.95,.999)
        outage_a = rng.uniform(.005,.15)
        healthy_c = rng.uniform(.88,.99)
        outage_c = rng.uniform(.08,.45)
        cost_ab = rng.uniform(.12,.42)
        cost_c = rng.uniform(.65,1.6)
        plans = (Plan('pair',(('a',),('b',))), Plan('single',(('c',),)))
    tools = {
        'a': Tool('a','a',healthy_a,outage_a,cost_ab),
        'b': Tool('b','b',healthy_a,outage_a,cost_ab),
        'c': Tool('c','c',healthy_c,outage_c,cost_c),
    }
    model = ShockModel(shock, {'a':low_a,'b':low_b,'c':q_c}, {'a':high_a,'b':high_b,'c':q_c})
    return tools, model, plans, reward


def assess(domain, architecture):
    rng = random.Random(SEED + {'gold':0,'seo':1}[domain]*10 + {'parallel':0,'serial':1}[architecture])
    disagreement = 0
    regrets = []
    misestimated_regrets = []
    probability_errors = []
    mc_max_error = 0.0
    focal = None
    for i in range(N):
        tools, model, plans, reward = make_case(domain,architecture,rng)
        correct, actual = select(tools,model,plans,reward,'joint')
        indep, _ = select(tools,model,plans,reward,'independent')
        wrong_model = ShockModel(model.probability*.5,model.calm,model.shocked)
        wrong_choice, _ = select(tools,wrong_model,plans,reward,'joint')
        disagreement += correct != indep
        regrets.append(actual[correct]-actual[indep])
        misestimated_regrets.append(actual[correct]-actual[wrong_choice])
        probability_errors.append(independent_success(tools,model,plans[0])-joint_success(tools,model,plans[0]))
        if correct != indep and focal is None:
            focal = {'case_index':i, 'shock_probability':round(model.probability,5),
                     'calm_outages':{k:round(v,5) for k,v in model.calm.items()},
                     'shocked_outages':{k:round(v,5) for k,v in model.shocked.items()},
                     'joint_choice':correct, 'independence_choice':indep,
                     'actual_utilities':{k:round(v,5) for k,v in actual.items()}}
        if i < 8:
            for p in plans:
                observed = monte_carlo_joint(tools,model,p,12000,SEED+100*i+(0 if p.name=='pair' else 1))
                mc_max_error=max(mc_max_error,abs(observed-joint_success(tools,model,p)))
    return {
        'scenarios':N,
        'independence_wrong_choices':disagreement,
        'independence_mean_true_utility_regret':round(mean(regrets),6),
        'independence_worst_true_utility_regret':round(max(regrets),6),
        'pair_independence_minus_joint_mean_probability':round(mean(probability_errors),6),
        'pair_independence_minus_joint_min_probability':round(min(probability_errors),6),
        'pair_independence_minus_joint_max_probability':round(max(probability_errors),6),
        'half_shock_wrong_choices':sum(x>1e-10 for x in misestimated_regrets),
        'half_shock_mean_true_utility_regret':round(mean(misestimated_regrets),6),
        'mc_max_abs_error_first_16_checks':round(mc_max_error,6),
        'first_disagreement':focal,
    }


def focal():
    tools = {'a':Tool('a','a',1,0,.1),'b':Tool('b','b',1,0,.1),
             'c':Tool('c','c',1,0,.5)}
    m=ShockModel(.2,{'a':0,'b':0,'c':.1},{'a':1,'b':1,'c':.1})
    parallel=Plan('parallel',(('a','b'),))
    serial=Plan('serial',(('a',),('b',)))
    fallback=Plan('fallback',(('c',),))
    return {'shock_probability':.2,
            'parallel_joint_success':joint_success(tools,m,parallel),
            'parallel_independent_success':independent_success(tools,m,parallel),
            'serial_joint_success':joint_success(tools,m,serial),
            'serial_independent_success':independent_success(tools,m,serial),
            'fallback_success':joint_success(tools,m,fallback),
            'joint_choice':select(tools,m,(parallel,fallback),10,'joint')[0],
            'independent_choice':select(tools,m,(parallel,fallback),10,'independent')[0]}

if __name__=='__main__':
    result={'seed':SEED,'scenarios_per_domain_architecture':N,'focal':focal(),
            'gold':{arch:assess('gold',arch) for arch in ('parallel','serial')},
            'seo':{arch:assess('seo',arch) for arch in ('parallel','serial')}}
    Path('results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result,indent=2))
