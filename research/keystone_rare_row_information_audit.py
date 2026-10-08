"""Keystone: rare-row detector audit (paired Markov simulations, calibrated e-processes)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.stats import beta

H=400; CHANGE=120; P01=1/36; P11=.75
ALPHA=.04; DELTA=.01; CAL_N=2000
GROUPS=12; PER_GROUP=250; N=GROUPS*PER_GROUP
SEED=202610082333
TARGET=[(0,'up',.12),(1,'up',.90),(1,'down',.20)]
WEIGHTS=np.array([.25,.375,.375])
GENERAL=[(r,d,f) for r in (0,1) for d in ('up','down') for f in (.15,.35)]
SCENARIOS={
 'stable':(P01,P11),'p01_up':(.12,P11),'p11_up':(P01,.90),
 'p11_down':(P01,.20),'both_up':(.12,.90),'p01_down':(.007,P11),
 'p11_mild_up':(P01,.83),'p11_mild_down':(P01,.55),
 'p01_small_up':(.06,P11),'p11_large_up':(P01,.97),
 'null_predictable_in_interval':None,
}

def cp(k,n=CAL_N):
    tail=DELTA/4
    return (0. if k==0 else float(beta.ppf(tail,k,n-k+1)),
            1. if k==n else float(beta.ppf(1-tail,k+1,n-k)))

def factors(lo,hi,channels):
    rows=np.array([r for r,_,_ in channels],dtype=np.int8)
    up=np.array([d=='up' for _,d,_ in channels])[:,None]
    b=np.where(up,hi[:,rows].T,lo[:,rows].T)
    q=np.empty_like(b)
    for i,(r,d,v) in enumerate(channels):
        if len(channels)==len(GENERAL):
            q[i]=b[i]+(1-b[i])*v if d=='up' else b[i]*(1-v)
        else:
            q[i]=np.maximum(v,b[i]) if d=='up' else np.minimum(v,b[i])
    ok=np.where(up,b<1,b>0)
    b=np.where(ok,b,.5);q=np.where(ok,q,.5)
    return rows,q/b,(1-q)/(1-b)

def run(scenario,lo,hi,seed):
    rng=np.random.default_rng(seed)
    gr,ga,gb=factors(lo,hi,GENERAL)
    tr,ta,tb=factors(lo,hi,TARGET)
    general=np.zeros((len(GENERAL),N))
    targeted=np.zeros((len(TARGET),N))
    oracle=np.ones(N)
    alarm=np.zeros((3,N),dtype=np.int16)
    prev=np.zeros(N,dtype=np.int8)
    for t in range(1,H+1):
        if scenario=='null_predictable_in_interval':
            p=np.where(prev==0,np.where(t%2==0,lo[:,0],hi[:,0]),
                       np.where(t%3==0,hi[:,1],lo[:,1]))
        else:
            p0,p1=(P01,P11) if t<=CHANGE else SCENARIOS[scenario]
            p=np.where(prev==0,p0,p1)
        x=(rng.random(N)<p).astype(np.int8)
        glr=np.where(gr[:,None]==prev[None,:],np.where(x[None,:]==1,ga,gb),1.)
        tlr=np.where(tr[:,None]==prev[None,:],np.where(x[None,:]==1,ta,tb),1.)
        general=(general+1/(len(GENERAL)*H))*glr
        targeted=(targeted+WEIGHTS[:,None]/H)*tlr
        eg=1-t/H+general.sum(axis=0)
        et=1-t/H+targeted.sum(axis=0)
        oracle_idx={'p01_up':0,'p11_up':1,'p11_down':2}.get(scenario)
        if oracle_idx is not None and t>CHANGE:
            oracle*=tlr[oracle_idx]
        for j,score in enumerate((eg,et,oracle)):
            mask=(alarm[j]==0)&(score>=1/ALPHA)
            alarm[j,mask]=t
        prev=x
    return alarm

def summarise(a):
    d={}
    for i,name in enumerate(('general_8','targeted_3','oracle_change_time')):
        x=a[i];hit=x>0;post=x>CHANGE
        d[name]={'hits':int(hit.sum()),'n':N,
          'alarm_rate':round(float(hit.mean()),6),
          'prechange_rate':round(float(((x>0)&(x<=CHANGE)).mean()),6),
          'median_delay_postchange':float(np.median(x[post]-CHANGE)) if post.any() else None}
    diff=(a[1]>0).astype(float)-(a[0]>0).astype(float)
    cluster=diff.reshape(GROUPS,PER_GROUP).mean(axis=1)
    se=cluster.std(ddof=1)/np.sqrt(GROUPS)
    d['paired_target_minus_general']={'difference':round(float(diff.mean()),6),
         'cluster_standard_error':round(float(se),6),
         'approx_95_ci':[round(float(diff.mean()-2.201*se),6),
                         round(float(diff.mean()+2.201*se),6)]}
    return d

def validate_martingale():
    tests=0;worst=-1e99
    for l,u in ((.02,.08),(.65,.81),(.001,.03),(.85,.99)):
        for d in ('up','down'):
            b=u if d=='up' else l
            qs=([b+(1-b)*.15,b+(1-b)*.35,.999] if d=='up'
                else [b*.85,b*.65,.001])
            for q in qs:
                for p in np.linspace(l,u,101):
                    ef=p*q/b+(1-p)*(1-q)/(1-b)
                    worst=max(worst,float(ef-1));tests+=1
                    assert ef<=1+1e-12
    assert abs(WEIGHTS.sum()-1)<1e-12
    return {'checked_one_step_expectations':tests,'max_excess':worst}

def main():
    verification=validate_martingale()
    rng=np.random.default_rng(SEED)
    ci0=np.array([cp(int(k)) for k in rng.binomial(CAL_N,P01,GROUPS)])
    ci1=np.array([cp(int(k)) for k in rng.binomial(CAL_N,P11,GROUPS)])
    lo=np.repeat(np.column_stack((ci0[:,0],ci1[:,0])),PER_GROUP,axis=0)
    hi=np.repeat(np.column_stack((ci0[:,1],ci1[:,1])),PER_GROUP,axis=0)
    cover=((ci0[:,0]<=P01)&(P01<=ci0[:,1])&
           (ci1[:,0]<=P11)&(P11<=ci1[:,1]))
    out={'seed':SEED,'horizon':H,'change_after':CHANGE,
      'paths_per_scenario':N,'calibration_groups':GROUPS,
      'calibration_per_row':CAL_N,'calibration_covered_groups':int(cover.sum()),
      'alpha':ALPHA,'delta':DELTA,'target_channels':TARGET,
      'target_weights':WEIGHTS.tolist(),'general_channels':GENERAL,
      'verification':verification,'results':{}}
    for i,s in enumerate(SCENARIOS):
        a=run(s,lo,hi,SEED+100+i)
        out['results'][s]=summarise(a)
        print(s,{k:out['results'][s][k]['alarm_rate']
                  for k in ('general_8','targeted_3','oracle_change_time')},
              flush=True)
    path=Path('keystone_rare_row_information_audit_results.json')
    path.write_text(json.dumps(out,indent=2))
    print('SAVED',path)
if __name__=='__main__':main()
