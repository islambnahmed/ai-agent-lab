"""Keystone: matched-opportunity six-probe selective-feedback test.
Run: python observation_budget_schedules.py --n 4000
Only numpy required. Exogenous latent Bernoulli outcomes; expected-loss regret.
Policies: slow EWMA(.03) updated only after risky actions; optional risky probes.
"""
import argparse
import json
import numpy as np

T=240
ALPHA=.03
P0=.9
RATIOS=[.055,.095,.115]
POLICIES=['never','front6','periodic6','random6']
SEEDS=[202610081731,202610081732]

def regimes():
    t=np.arange(T)
    return {
        'null_90':np.full(T,.9),
        'stable_95':np.full(T,.95),
        'early_gain_95':np.where(t<40,.9,.95),
        'late_gain_95':np.where(t<160,.9,.95),
        'stable_78':np.full(T,.78),
        'collapse_50':np.where(t<80,.9,.5),
    }

def run_case(q,ratio,n,seed):
    rng=np.random.default_rng(seed)
    x=rng.random((n,T))<q
    # Six random time opportunities, selected without future outcome information.
    u=rng.random((n,T))
    ids=np.argpartition(u,6,axis=1)[:,:6]
    random_calendar=np.zeros((n,T),dtype=bool)
    random_calendar[np.arange(n)[:,None],ids]=True
    pred=np.full((4,n),P0)
    total=np.zeros((4,n))
    forced_count=np.zeros((4,n))
    feedback_count=np.zeros((4,n))
    oracle=np.minimum(1-q,ratio)
    threshold=1-ratio
    for t in range(T):
        natural=pred>threshold
        scheduled=np.stack([
            np.zeros(n,bool),
            np.full(n,t<6,bool),
            np.full(n,t%40==0,bool),
            random_calendar[:,t],
        ])
        forced=scheduled&~natural
        risky=natural|forced
        total+=np.where(risky,1-q[t],ratio)-oracle[t]
        forced_count+=forced
        feedback_count+=risky
        pred+=ALPHA*risky*(x[:,t][None,:]-pred)
    return total,forced_count,feedback_count

def main(n):
    out={'protocol':'frozen six exogenous probe opportunities per 240 steps; per path',
         'n_per_seed_regime_cost':n,'seeds':SEEDS,'T':T,'ratios':RATIOS,
         'policies':POLICIES,'regimes':list(regimes()),'results':{}}
    for name,q in regimes().items():
        for ratio in RATIOS:
            a=[];b=[];c=[]
            for k,seed in enumerate(SEEDS):
                z=run_case(q,ratio,n,seed+117*k+sum(map(ord,name))*43+int(ratio*1000))
                a.append(z[0]);b.append(z[1]);c.append(z[2])
            regret=np.concatenate(a,axis=1)
            forced=np.concatenate(b,axis=1)
            feedback=np.concatenate(c,axis=1)
            delta=regret-regret[0:1]
            se=delta.std(axis=1,ddof=1)/np.sqrt(delta.shape[1])
            key=f'{name}|ratio={ratio}'
            out['results'][key]={
                'mean_regret':dict(zip(POLICIES,np.round(regret.mean(axis=1),6).tolist())),
                'delta_vs_never':dict(zip(POLICIES,np.round(delta.mean(axis=1),6).tolist())),
                'paired_MC_CI95':dict(zip(POLICIES,[[round(float(m-1.96*s),6),round(float(m+1.96*s),6)] for m,s in zip(delta.mean(axis=1),se)])),
                'forced_probes':dict(zip(POLICIES,np.round(forced.mean(axis=1),4).tolist())),
                'observed_outcomes':dict(zip(POLICIES,np.round(feedback.mean(axis=1),4).tolist())),
            }
            print(key,'delta',np.round(delta.mean(axis=1),3),
                  'forced',np.round(forced.mean(axis=1),2),flush=True)
    with open('observation_budget_results.json','w') as f:json.dump(out,f,indent=2)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=4000)
    a=p.parse_args();main(a.n)
