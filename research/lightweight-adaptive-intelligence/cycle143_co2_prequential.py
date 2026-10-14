#!/usr/bin/env python3
"""Chronological Mauna Loa CO2 forecasting; historical feedback lags are SIMULATED."""
import argparse, collections, json
import numpy as np
import pandas as pd
from statsmodels.datasets import co2

PERIOD=52.18
EXPERTS=('last','seasonal','seasonal_drift','harmonic')

def data():
    s=co2.load_pandas().data['co2'].astype(float)
    assert len(s)==2284 and s.index.is_monotonic_increasing
    return s

def harmonic_predict(values,t,cutoff,window=156):
    idx=np.flatnonzero(np.isfinite(values[:cutoff+1]))[-window:]
    if len(idx)<80:return np.nan
    def design(x):
        x=np.asarray(x,dtype=float); z=(x-t)/PERIOD
        return np.column_stack((np.ones_like(x),z,
            np.sin(2*np.pi*x/PERIOD),np.cos(2*np.pi*x/PERIOD),
            np.sin(4*np.pi*x/PERIOD),np.cos(4*np.pi*x/PERIOD)))
    beta=np.linalg.lstsq(design(idx),values[idx],rcond=None)[0]
    return float(design([t])[0]@beta)

def expert_predictions(values,t,cutoff):
    if cutoff<0:raise ValueError('no history')
    seen=np.flatnonzero(np.isfinite(values[:cutoff+1]))
    if len(seen)==0:raise ValueError('no observed history')
    last=float(values[seen[-1]])
    seas=float(values[t-52]) if 0<=t-52<=cutoff and np.isfinite(values[t-52]) else last
    if 0<=t-104<=cutoff and np.isfinite(values[t-104]) and 0<=t-52<=cutoff and np.isfinite(values[t-52]):
        drift=2*float(values[t-52])-float(values[t-104])
    else:drift=seas
    harm=harmonic_predict(values,t,cutoff)
    if not np.isfinite(harm):harm=last
    return np.array([last,seas,drift,harm],dtype=float)

def evaluate(values,index,start,end,lag=0,eta=.2,forgetting=.97,record_trace=False):
    assert lag>=0 and 0<=start<end<=len(values)
    q=collections.deque();state=np.zeros(len(EXPERTS))
    sums={k:[] for k in (*EXPERTS,'equal','hedge')};trace=[]
    for t in range(start,end):
        while q and q[0][0]<=t:
            _,losses=q.popleft()
            state=forgetting*state+(1-forgetting)*losses
        cutoff=t-lag-1
        p=expert_predictions(values,t,cutoff)
        logw=np.maximum(-eta*(state-state.min()),-100.)
        w=np.exp(logw);w=w/w.sum()
        preds=dict(zip(EXPERTS,p))
        preds['equal']=float(np.mean(p));preds['hedge']=float(w@p)
        y=values[t]
        if np.isfinite(y):
            q.append((t+lag+1,(p-y)**2))
            for k,v in preds.items():sums[k].append(float((v-y)**2))
            if record_trace:trace.append({'date':str(index[t].date()),'y':float(y),
                'cutoff':str(index[cutoff].date()),'weights':w.round(5).tolist(),
                'predictions':{k:round(float(v),5) for k,v in preds.items()}})
    out={'start':str(index[start].date()),'end':str(index[end-1].date()),
         'n_scored':len(sums['last']),
         'rmse':{k:float(np.sqrt(np.mean(v))) for k,v in sums.items()},
         'mse':{k:float(np.mean(v)) for k,v in sums.items()}}
    if record_trace:out['trace']=trace
    return out

def run():
    s=data();v=s.to_numpy();ix=s.index
    val_start=int(ix.searchsorted(pd.Timestamp('1978-01-01')))
    test_start=int(ix.searchsorted(pd.Timestamp('1990-01-01')))
    results={}
    for lag in (0,4,12):
        grid={}
        for eta in (0.,.02,.1,.5,2.):
            for f in (.9,.97,.995):
                grid[(eta,f)]=evaluate(v,ix,val_start,test_start,lag,eta,f)['mse']['hedge']
        best=min(grid,key=lambda x:(grid[x],x[0],x[1]))
        vr=evaluate(v,ix,val_start,test_start,lag,*best)
        te=evaluate(v,ix,test_start,len(v),lag,*best,record_trace=True)
        selected=min((*EXPERTS,'equal','hedge'),key=lambda k:vr['mse'][k])
        annual={}
        for year in range(1990,2002):
            rows=[r for r in te['trace'] if r['date'][:4]==str(year)]
            annual[str(year)]={'n':len(rows),
                'mse':{k:float(np.mean([(r['predictions'][k]-r['y'])**2 for r in rows]))
                for k in (*EXPERTS,'equal','hedge')}}
        results[f'lag{lag}']={'selected_eta':best[0],'selected_forgetting':best[1],
            'validation_selected_policy':selected,'selected_policy_test_rmse':te['rmse'][selected],
            'validation':{k:vr[k] for k in ('start','end','n_scored','rmse','mse')},
            'test':{k:te[k] for k in ('start','end','n_scored','rmse','mse')},
            'test_years':annual,
            'hedge_vs_best_test_expert_mse':te['mse']['hedge']-min(te['mse'][k] for k in EXPERTS)}
    return {'dataset':'statsmodels.datasets.co2, Mauna Loa weekly measured CO2 (ppm)',
        'missing_observations':int(s.isna().sum()),'total_weeks':len(s),
        'feedback_delay':'SIMULATED: y[t] settles at t+lag+1; real release vintages unknown',
        'warmup':'1958-1977','validation':'1978-1989','test':'1990-2001',
        'results':results}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='cycle143_results.json')
    args=ap.parse_args();result=run()
    with open(args.output,'w') as f:json.dump(result,f,indent=2)
    for lag,r in result['results'].items():
        print(lag,r['validation_selected_policy'],r['selected_policy_test_rmse'])
