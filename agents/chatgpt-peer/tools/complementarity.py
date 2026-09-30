"""Estimate whether two binary success/failure histories complement each other."""
from __future__ import annotations

def run(a,b):
    if len(a)!=len(b) or not a: raise ValueError("equal non-empty histories required")
    A=[bool(x) for x in a]; B=[bool(x) for x in b]; n=len(A)
    sa=sum(A)/n; sb=sum(B)/n
    oracle=sum(x or y for x,y in zip(A,B))/n
    both=sum(x and y for x,y in zip(A,B))/n
    return {"n":n,"success_a":sa,"success_b":sb,"best_single":max(sa,sb),
            "oracle_union":oracle,"complementarity_gain":oracle-max(sa,sb),
            "both_succeed":both}
