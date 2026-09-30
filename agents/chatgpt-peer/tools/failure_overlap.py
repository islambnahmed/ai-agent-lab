"""Analyze overlap between binary failure histories.

This does not infer causality or independence. It exposes when two apparently
separate methods fail on the same cases more often than their marginals suggest.
"""
from __future__ import annotations
import math

def run(a,b):
    if len(a)!=len(b) or len(a)<4: raise ValueError("equal histories of length >=4 required")
    A=[bool(x) for x in a]; B=[bool(x) for x in b]; n=len(A)
    n11=sum(x and y for x,y in zip(A,B))
    n10=sum(x and not y for x,y in zip(A,B))
    n01=sum((not x) and y for x,y in zip(A,B))
    n00=n-n11-n10-n01
    pa=(n11+n10)/n; pb=(n11+n01)/n; joint=n11/n
    expected=pa*pb
    denom=math.sqrt(pa*(1-pa)*pb*(1-pb))
    phi=(joint-expected)/denom if denom else None
    lift=joint/expected if expected else None
    return {"n":n,"table":{"both_fail":n11,"a_only":n10,"b_only":n01,"neither":n00},
            "p_fail_a":pa,"p_fail_b":pb,"observed_joint_failure":joint,
            "independence_expected_joint":expected,"failure_lift":lift,"phi":phi}
