"""Deterministic AR(1) null + real upstream walk-forward integration.
Run from repository root or with the exp408 offline upstream snapshot copied
as `upstream_gold_walkforward.py` next to this file.
"""
import datetime as dt
import json
import math
import random
import statistics
from dependence_audit import audit_deltas, audit_backtest, exact_ar1_variance_inflation

try:
    from tools.gold_walkforward import backtest
except ImportError:
    from upstream_gold_walkforward import backtest


def ar1_values(rng, phi, n, burn=100):
    x=0.0
    out=[]
    for i in range(n+burn):
        x=phi*x+math.sqrt(1-phi*phi)*rng.gauss(0,1)
        if i>=burn:out.append(x)
    return out


def null_calibration(n,phi,reps=2500,seed=1):
    rng=random.Random(seed)
    naive=0;hac=0; valid=0
    for _ in range(reps):
        a=audit_deltas(ar1_values(rng,phi,n))
        if a['naive_z_diagnostic'] is not None:
            valid+=1
            naive+=abs(a['naive_z_diagnostic'])>1.96
            hac+=abs(a['hac_z_diagnostic'])>1.96
    return {'n':n,'phi':phi,'reps':reps,
            'naive_abs_z_gt_1_96_rate':round(naive/valid,4),
            'hac_abs_z_gt_1_96_rate':round(hac/valid,4),
            'exact_ar1_mean_variance_inflation':round(exact_ar1_variance_inflation(n,phi),4),
            'exact_ar1_effective_n':round(n/exact_ar1_variance_inflation(n,phi),3)}


def synthetic_prices(case,seed,n=520,phi=.9):
    rng=random.Random(seed)
    state=0.0;price=100.0 if case=='gold' else 20000.0
    rows=[]
    for i in range(n):
        state=phi*state+math.sqrt(1-phi*phi)*rng.gauss(0,1)
        # SEO has an additional deterministic weekly cycle, gold does not.
        # SEO volume is positive continuous synthetic data, not observed counts.
        price*=math.exp(.004*state)
        value=price if case=='gold' else price*math.exp(.12*math.sin(2*math.pi*i/7))
        rows.append((dt.date(2025,1,1)+dt.timedelta(days=i),value))
    return rows


def upstream_integration(case,phi=.9,reps=60):
    rhos=[];statuses={};examples=[]
    for seed in range(reps):
        horizon = 7 if case == 'gold' else 3
        res=backtest(synthetic_prices(case,seed,n=400,phi=phi),horizon=horizon,train_min=120,stride=horizon)
        statuses[res['status']]=statuses.get(res['status'],0)+1
        audit=audit_backtest(res)
        rho=audit['lag1_autocorrelation']
        if rho is not None:rhos.append(rho)
        if seed==0:
            examples.append({'windows':res['independent_windows'],'status':res['status'],
                             'lag1':round(rho,4),'lag7':round(audit['autocorrelation_lags_1_to_10'][7],4),
                             'estimated_ar1_ess':round(audit['ar1_effective_n_diagnostic'],2),
                             'higher_lag_warning':audit['strong_higher_lag_structure_heuristic']})
    return {'case':case,'phi_returns':phi,'replicates':reps,'statuses':statuses,
            'mean_lag1_paired_mae_delta':round(statistics.mean(rhos),4),
            'fraction_lag1_gt_0_2':round(sum(v>.2 for v in rhos)/len(rhos),4),
            'first_example':examples[0]}


def main():
    out={'null_ar1':[null_calibration(n,p,seed=100+n+int(p*100)) for n in (20,60) for p in (0.0,.8,.9)],
         'upstream_integration':[upstream_integration(c,phi=p) for c in ('gold','seo') for p in (0.0,.9)],
         'notes':['All data synthetic. AR1 null uses Gaussian paired deltas, not actual backtest deltas.',
                  'Absolute z>1.96 is a diagnostic threshold, not a calibrated finite-sample test.',
                  'Upstream evaluation_ready is a sample-count label, not an explicit statistical significance claim.',
                  'SEO weekly seasonality with horizon=3 can create strong lag-7 dependence even when lag-1 correlation is negative; AR1 ESS is then not appropriate.']}
    print(json.dumps(out,indent=2))
    return out

if __name__=='__main__':main()
