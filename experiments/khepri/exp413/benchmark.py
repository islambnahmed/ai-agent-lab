"""Reproducible paired synthetic evaluation; no external data or actions."""
import json, math, random, statistics
from censored_refresh import Observation, censored_map, naive_count_rate, run_policy
SEED=413

def ci95(values):
    return [statistics.mean(values)-1.96*statistics.stdev(values)/math.sqrt(len(values)),statistics.mean(values)+1.96*statistics.stdev(values)/math.sqrt(len(values))]

def estimator_trial(rate, exposure, repeats, rng):
    observations=[Observation(exposure,rng.random()< -math.expm1(-rate*exposure)) for _ in range(repeats)]
    return censored_map(observations),naive_count_rate(observations)

def estimator_benchmark():
    rng=random.Random(SEED);output={}
    for name,rate,exposure in [('low-rate',.05,2),('moderate',.4,3),('saturated',2.,4)]:
        pairs=[estimator_trial(rate,exposure,100,rng) for _ in range(250)]
        output[name]={'true_rate':rate,'exposure':exposure,'replicates':len(pairs),
            'map_mean':statistics.mean(p[0] for p in pairs),
            'naive_mean':statistics.mean(p[1] for p in pairs),
            'map_mae':statistics.mean(abs(p[0]-rate) for p in pairs),
            'naive_mae':statistics.mean(abs(p[1]-rate) for p in pairs)}
    output['saturation-by-interval']={}
    for exposure in (1,2,4,8):
        pairs=[estimator_trial(2.0,exposure,100,rng) for _ in range(150)]
        output['saturation-by-interval'][str(exposure)]={
          'map_mean':statistics.mean(p[0] for p in pairs),
          'map_mae':statistics.mean(abs(p[0]-2.0) for p in pairs),
          'naive_mean':statistics.mean(p[1] for p in pairs)}
    return output

def policy_benchmark():
    rng=random.Random(SEED+1)
    domains={
      'seo': {'impacts':[10,8,7,5,3],'rates':[.02,.05,.12,.45,1.8]},
      'feed':{'impacts':[7,10,8,6,4],'rates':[.03,.2,.5,1.2,2.8]},
      'counterexample-low-observation':{'impacts':[1,1,1,1,1],'rates':[.02,.03,.04,.05,.06]},
    }
    out={}
    for domain,settings in domains.items():
        impacts,rates=settings['impacts'],settings['rates'];rows=[]
        for _ in range(150):
            latent=[[rng.random() < -math.expm1(-rate) for _ in range(90)] for rate in rates]
            rows.append({name:run_policy(impacts,rates,latent,name,2)[0] for name in ('censored','naive','oracle')})
        diff=[row['censored']-row['naive'] for row in rows]
        oracle_diff=[row['oracle']-row['censored'] for row in rows]
        out[domain]={'runs':len(rows),'days':90,'budget_per_day':2,
          'means':{name:statistics.mean(row[name] for row in rows) for name in ('censored','naive','oracle')},
          'map_minus_naive_mean':statistics.mean(diff),'map_minus_naive_ci95':ci95(diff),
          'map_wins':sum(x>0 for x in diff),'map_ties':sum(x==0 for x in diff),'map_losses':sum(x<0 for x in diff),
          'oracle_minus_map_mean':statistics.mean(oracle_diff)}
    return out

if __name__=='__main__':
    data={'seed':SEED,'estimator':estimator_benchmark(),'policy':policy_benchmark()}
    with open('results.json','w') as f:json.dump(data,f,indent=2,sort_keys=True)
    print(json.dumps(data,indent=2,sort_keys=True))
