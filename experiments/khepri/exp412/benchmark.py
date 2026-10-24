"""Fixed-seed, synthetic expected-reward benchmark. No network access."""
import json,random
from planner import Item,plan,evaluate


def sample(rng,kind):
    n=rng.randint(3,5)
    if kind=='seo':
        items=[Item(f'page-{i}',rng.randint(1,3),rng.uniform(2,40),rng.choice([.01,.03,.1,.3,.7])) for i in range(n)]
    elif kind=='feeds':
        items=[Item(f'feed-{i}',rng.randint(1,3),rng.uniform(3,20),rng.choice([.03,.15,.4,1.])) for i in range(n)]
    else:raise ValueError(kind)
    return items,rng.randint(2,4),rng.randint(3,5)


def run(n=300):
    output={'method':'exact expected rewards for independent Poisson change process; 300 seeded synthetic small cases per domain; no live data','cases':{}}
    for j,kind in enumerate(('seo','feeds')):
        rng=random.Random(412+j)
        wins=ties=0;gains=[];max_case=None;wrong_harm=0;wrong_gains=[]
        for k in range(n):
            items,budget,horizon=sample(rng,kind)
            optimal=plan(items,budget,horizon)
            myopic=plan(items,budget,horizon,'myopic')
            vopt=evaluate(items,budget,optimal)
            vmyo=evaluate(items,budget,myopic)
            delta=vopt-vmyo
            if delta>1e-8:wins+=1
            elif abs(delta)<=1e-8:ties+=1
            gains.append(delta)
            if max_case is None or delta>max_case['absolute_gain']:
                max_case={'items':[x.__dict__ for x in items],'budget':budget,'horizon':horizon,'optimal_actions':optimal,'myopic_actions':myopic,'optimal_expected':round(vopt,6),'myopic_expected':round(vmyo,6),'absolute_gain':round(delta,6)}
            # Deliberately misspecify: overestimate low-impact change rates and
            # underestimate high-impact rates. Both policies use same wrong model.
            threshold=sum(x.impact for x in items)/len(items)
            wrong=[Item(x.id,x.cost,x.impact,x.rate*(.05 if x.impact>=threshold else 10.)) for x in items]
            vwrong=evaluate(items,budget,plan(wrong,budget,horizon))
            vwrongmyo=evaluate(items,budget,plan(wrong,budget,horizon,'myopic'))
            wrong_gains.append(vwrong-vwrongmyo)
            if vwrong+1e-8<vwrongmyo:wrong_harm+=1
        output['cases'][kind]={'n':n,'optimal_beats_myopic':wins,'ties':ties,'mean_absolute_expected_gain':round(sum(gains)/n,6),'mean_gain_pct_of_myopic':None,'max_case':max_case,'misspecified_optimal_worse_than_misspecified_myopic':wrong_harm,'mean_misspecified_gain':round(sum(wrong_gains)/n,6)}
    return output


if __name__=='__main__':print(json.dumps(run(),indent=2))
