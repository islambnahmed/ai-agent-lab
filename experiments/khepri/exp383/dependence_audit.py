"""Audit serial dependence in paired backtest loss differences.

Nonoverlapping forecast horizons do not imply independent forecast errors.
Positive mean (candidate absolute error - baseline absolute error) favors
the baseline.  Intervals are descriptive and NOT selection-adjusted.
Standard library only.
"""
from __future__ import annotations
import math
import statistics
from datetime import date

Z95 = 1.959963984540054

def _validate(values):
    xs = [float(x) for x in values]
    if len(xs) < 3 or any(not math.isfinite(x) for x in xs):
        raise ValueError("Require >=3 finite paired loss differences")
    return xs

def paired_losses(results):
    """Extract losses from tools/gold_walkforward.py-style result rows."""
    out, previous = [], None
    for row in results:
        day = date.fromisoformat(row["target_date"])
        if previous is not None and day <= previous:
            raise ValueError("Target dates must increase strictly")
        previous = day
        a, b = float(row["candidate_abs_error"]), float(row["baseline_abs_error"])
        if not math.isfinite(a) or not math.isfinite(b) or min(a, b) < 0:
            raise ValueError("Absolute errors must be nonnegative and finite")
        out.append(a-b)
    return _validate(out)

def autocov(xs, lag):
    if not 0 <= lag < len(xs):
        raise ValueError("Invalid lag")
    avg = statistics.fmean(xs)
    return sum((xs[i]-avg)*(xs[i-lag]-avg) for i in range(lag,len(xs)))/len(xs)

def audit(values, max_lag=12):
    xs = _validate(values)
    n = len(xs)
    if not isinstance(max_lag,int) or not 0 <= max_lag < n:
        raise ValueError("max_lag must be integer in [0,n-1]")
    avg = statistics.fmean(xs)
    gamma0 = autocov(xs,0)
    lrv = gamma0 + 2*sum((1-lag/(max_lag+1))*autocov(xs,lag)
                         for lag in range(1,max_lag+1))
    lrv = max(0.0,lrv)
    iid_se = math.sqrt(gamma0/n)
    hac_se = math.sqrt(lrv/n)
    return {
        "n":n, "mean_candidate_minus_baseline":avg,
        "lag1_autocorrelation":autocov(xs,1)/gamma0 if gamma0>0 else None,
        "hac_max_lag":max_lag,
        "iid_95_interval":[avg-Z95*iid_se,avg+Z95*iid_se],
        "hac_95_interval":[avg-Z95*hac_se,avg+Z95*hac_se],
        "iid_se":iid_se,"hac_se":hac_se,
        "effective_n_heuristic":n*gamma0/lrv if lrv>0 else None,
        "warning":"Disjoint windows do not imply independent errors. "
                  "HAC assumes approximate stationarity and weak dependence. "
                  "Check lag sensitivity. Not selection-adjusted."
    }

def ci_contains_zero(interval):
    return interval[0] <= 0 <= interval[1]
