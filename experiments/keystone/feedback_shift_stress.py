"""Keystone feedback-shift falsification. Reproduce with numpy:
python feedback_shift_stress.py --n 1000 --seeds 2026101201 2026101202
Full/missing/risky-only/5% exploration; paired latent outcomes and frozen policies.
"""
import argparse,json
import numpy as np

COSTS=[(5,.275),(7,.595),(13,1.495),(10,1.65),(11,2.255),(4,.38),(14,2.52)]
def regimes():
    t=np.arange(240)
    return {
        'null_p90':np.full(240,.9), 'stable_p86':np.full(240,.86),
        'stable_p78':np.full(240,.78), 'stable_p69':np.full(240,.69),
        'stable_p45':np.full(240,.45), 'stable_p95':np.full(240,.95),
        'moderate_late':np.where(t<90,.9,.6),
        'large_mid':np.where(t<110,.9,.3),
        'tiny_mid':np.where(t<110,.9,.85),
        'early_short_shock':np.where((t>=40)&(t<52),.2,.9),
        'late_recovery':np.where(t<70,.9,np.where(t<190,.25,.9)),
        'piecewise_cycle':np.where(t<60,.85,np.where(t<115,.5,np.where(t<170,.7,.4))),
        'slow_rise':np.interp(t,[0,50,190,239],[.4,.4,.85,.85]),
    }
T=240; P0=.9; A=np.array([.01,.03,.10,.30]); POL=['slow03','shrink25','ewma01','ewma05','ewma10']

def choose(pred,score,p05):
    z=-score;z=z-z.max(axis=-1,keepdims=True)
    w=np.exp(z);w/=w.sum(axis=-1,keepdims=True)
    mix=(w*pred).sum(axis=-1)
    if pred.ndim==2:
        return np.stack([pred[:,1],.75*pred[:,1]+.25*mix,pred[:,0],p05,pred[:,2]])
    return np.stack([pred[0,:,1],.75*pred[1,:,1]+.25*mix[1],pred[2,:,0],p05[3],pred[4,:,2]])

def update(pred,score,p05,obs,visible):
    v=visible[...,None]
    y=obs[...,None]
    p=np.clip(pred,1e-6,1-1e-6)
    loss=-(y*np.log(p)+(1-y)*np.log1p(-p))
    score=np.where(v,.97*score+loss,score)
    pred=np.where(v,pred+A*(y-pred),pred)
    p05=np.where(visible,p05+.05*(obs-p05),p05)
    return pred,score,p05

def full_or_mcar(x,q,mode,seed):
    n,tmax=x.shape;pred=np.full((n,4),P0);score=np.zeros((n,4));p05=np.full(n,P0)
    rng=np.random.default_rng(seed)
    masks=rng.random((n,tmax))<.5 if mode=='mcar50' else np.ones((n,tmax),bool)
    forecasts=np.empty((5,n,tmax),dtype=np.float32)
    for t in range(tmax):
        forecasts[:,:,t]=choose(pred,score,p05)
        pred,score,p05=update(pred,score,p05,x[:,t].astype(float),masks[:,t])
    return forecasts,masks.mean()

def risky_only(x,q,ratio,epsilon=0.,seed=0):
    n,tmax=x.shape
    pred=np.full((5,n,4),P0)
    score=np.zeros((n,4));p05=np.full(n,P0)
    regrets=np.zeros((5,n));visible_count=np.zeros((5,n))
    rng=np.random.default_rng(seed)
    for t in range(tmax):
        z=-score;z-=z.max(axis=1,keepdims=True)
        w=np.exp(z);w/=w.sum(axis=1,keepdims=True)
        mix=(w*pred[1]).sum(axis=1)
        phat=np.stack([pred[0,:,1],.75*pred[1,:,1]+.25*mix,
                       pred[2,:,0],p05,pred[4,:,2]])
        risky=phat>1-ratio
        if epsilon: risky=risky | (rng.random(n)[None,:]<epsilon)
        regrets+=np.where(risky,1-q[t],ratio)-min(1-q[t],ratio)
        visible_count+=risky
        obs=x[:,t].astype(float)
        p=np.clip(pred[1],1e-6,1-1e-6)
        loss=-(obs[:,None]*np.log(p)+(1-obs[:,None])*np.log1p(-p))
        score=np.where(risky[1,:,None],.97*score+loss,score)
        pred+=risky[:,:,None]*A[None,None,:]*(obs[None,:,None]-pred)
        p05+=risky[3]*.05*(obs-p05)
    return regrets,visible_count/T

def main(n,seeds):
    names=list(regimes());modes=['full','mcar50','risky_only','risky_eps05']
    sums={mode:np.zeros((len(names),5)) for mode in modes}
    obs_sums={mode:np.zeros(5) for mode in modes}
    seed_mean={mode:[] for mode in modes}
    paired={mode:[] for mode in modes}
    for seed in seeds:
        seed_out={mode:np.zeros((len(names),5)) for mode in modes}
        for i,(name,q) in enumerate(regimes().items()):
            rng=np.random.default_rng(seed+i*113)
            x=rng.random((n,T))<q
            for mi,mode in enumerate(modes):
                if mode in ('full','mcar50'):
                    forecast,observed=full_or_mcar(x,q,mode,seed+1009*i+13007*mi)
                    act=forecast[:,:,None,:]>np.array([1-s/c for c,s in COSTS])[None,None,:,None]
                    reg=np.where(act,1-q[None,None,None,:],
                                 np.array([s/c for c,s in COSTS])[None,None,:,None])
                    reg-=np.minimum(1-q[None,None,None,:],
                                    np.array([s/c for c,s in COSTS])[None,None,:,None])
                    path_regret=reg.sum(axis=-1).mean(axis=2)
                    r=path_regret.mean(axis=1)
                    obs_sums[mode]+=observed/len(names)/len(seeds)
                else:
                    tmp=[];observed=[]
                    for c,s in COSTS:
                        rr,oo=risky_only(x,q,s/c,epsilon=.05 if mode=='risky_eps05' else 0.,
                            seed=seed+1009*i+13007*mi+701*len(tmp))
                        tmp.append(rr);observed.append(oo.mean(axis=1))
                    path_regret=np.mean(tmp,axis=0)
                    r=path_regret.mean(axis=1)
                    obs_sums[mode]+=np.mean(observed,axis=0)/len(names)/len(seeds)
                seed_out[mode][i]=r
                paired[mode].append(path_regret[1]-path_regret[0])
        for mode in modes:
            sums[mode]+=seed_out[mode]/len(seeds)
            seed_mean[mode].append((seed_out[mode][:,1]-seed_out[mode][:,0]).mean())
        print('finished',seed,flush=True)
    report={'n_per_regime_seed':n,'seeds':seeds,'cost_pairs':COSTS,'regimes':names}
    for mode in modes:
        v=sums[mode]
        d=v[:,1]-v[:,0]
        dominant=.8*v[names.index('stable_p78')]+.2*(v.sum(axis=0)-v[names.index('stable_p78')])/(len(names)-1)
        delta=np.concatenate(paired[mode]);se=float(delta.std(ddof=1)/np.sqrt(len(delta)))
        d78=float(d[names.index('stable_p78')]);other=float((d.sum()-d78)/(len(names)-1))
        critical=float(-other/(d78-other)) if abs(d78-other)>1e-10 else None
        report[mode]={
          'paired_delta_CI95_conditional':list(np.round([delta.mean()-1.96*se,delta.mean()+1.96*se],6)),
          'p78_weight_break_even':round(critical,6) if critical is not None else None,
          'mean_regret':dict(zip(POL,np.round(v.mean(axis=0),6).tolist())),
          'shrink_vs_slow':round(float(d.mean()),6),
          'shrink_vs_ewma05':round(float((v[:,1]-v[:,3]).mean()),6),
          'by_regime_shrink_vs_slow':dict(zip(names,np.round(d,6).tolist())),
          'by_regime_shrink_vs_ewma05':dict(zip(names,np.round(v[:,1]-v[:,3],6).tolist())),
          'p78_dominant_mean_regret':dict(zip(POL,np.round(dominant,6).tolist())),
          'fraction_feedback':dict(zip(POL,np.round(obs_sums[mode],5).tolist())),
          'seed_avg_deltas':seed_mean[mode],
        }
    with open('keystone_feedback_shift_stress_results.json','w') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--n',type=int,default=1200)
    parser.add_argument('--seeds',nargs='+',type=int,default=[2026101201,2026101202]);a=parser.parse_args()
    main(a.n,a.seeds)
