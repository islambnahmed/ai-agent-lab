"""Decision utility primitives learned from experiments 15-49.

Small functions only; no universal decision policy is implied.
"""
from __future__ import annotations
import math, statistics

def robust_scale(xs):
    xs=[float(x) for x in xs]
    if not xs:return None
    m=statistics.median(xs); mad=statistics.median(abs(x-m) for x in xs)
    return {"median":m,"mad":mad}

def bounded_retry(successes, attempts, prior=(1,1)):
    """Beta-binomial posterior mean; descriptive, not a guarantee."""
    a,b=prior
    if attempts<0 or successes<0 or successes>attempts:raise ValueError("bad counts")
    return (a+successes)/(a+b+attempts)

def value_of_information(decision_values, info_cost):
    """Upper bound: perfect-information gain minus cost."""
    if not decision_values:raise ValueError("empty")
    current=max(sum(v)/len(v) for v in decision_values)
    oracle=sum(max(outcomes) for outcomes in zip(*decision_values))/len(decision_values[0])
    return {"current":current,"perfect_info":oracle,"upper_bound_net_gain":oracle-current-info_cost}

def regret(chosen, best):
    return max(0.0,float(best)-float(chosen))

def saturation(gains, window=3, epsilon=1e-9):
    if len(gains)<window:return False
    return all(abs(float(x))<=epsilon for x in gains[-window:])
