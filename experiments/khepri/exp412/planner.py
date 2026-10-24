"""Exact finite-horizon expected-change-detection planner (research only).

Assumes independent stationary Poisson changes and a check which clears all pending
changes. No external calls. The ages, not observed outcomes, determine future
expected rewards. Optimality holds ONLY under this finite-horizon objective/model.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
import math

@dataclass(frozen=True)
class Item:
    id: str
    cost: int
    impact: float
    rate: float


def _validate(items, budget, horizon, initial_ages):
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0 or budget > 100:
        raise ValueError('invalid budget')
    if isinstance(horizon, bool) or not isinstance(horizon, int) or not 0 <= horizon <= 7:
        raise ValueError('horizon must be 0..7')
    if len(items) > 6:
        raise ValueError('exact search limited to <=6 items')
    if len({x.id for x in items}) != len(items):
        raise ValueError('duplicate ids')
    for x in items:
        if not isinstance(x.id, str) or not x.id or isinstance(x.cost, bool) or not isinstance(x.cost,int) or x.cost <= 0:
            raise ValueError('invalid id or cost')
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in (x.impact,x.rate)):
            raise ValueError('invalid impact or rate')
    if initial_ages is None:
        initial_ages=(0,)*len(items)
    if len(initial_ages)!=len(items) or any(isinstance(a,bool) or not isinstance(a,int) or a<0 for a in initial_ages):
        raise ValueError('invalid initial ages')
    return tuple(initial_ages)


def _reward(x,age):
    return x.impact * -math.expm1(-x.rate * (age+1))


def _options(items,budget):
    return tuple(s for r in range(len(items)+1) for s in combinations(range(len(items)),r)
                 if sum(items[i].cost for i in s)<=budget)


def _advance(ages,selected):
    ss=set(selected)
    return tuple(0 if i in ss else age+1 for i,age in enumerate(ages))


def plan(items:list[Item],budget:int,horizon:int,method:str='optimal',initial_ages=None):
    ages=_validate(items,budget,horizon,initial_ages)
    if method not in ('optimal','myopic'):
        raise ValueError('unknown method')
    # Sort IDs to make selection invariant to caller input order.
    rows=sorted(zip(items,ages),key=lambda p:p[0].id)
    items=tuple(x for x,_ in rows)
    ages=tuple(a for _,a in rows)
    options=_options(items,budget)
    if method=='myopic':
        seq=[]
        for _ in range(horizon):
            chosen=max(options,key=lambda s:(sum(_reward(items[i],ages[i]) for i in s),
                                            -sum(items[i].cost for i in s),tuple(-i for i in s)))
            seq.append(chosen)
            ages=_advance(ages,chosen)
        return tuple(tuple(items[i].id for i in s) for s in seq)
    @lru_cache(None)
    def solve(days,ages):
        if days==0:
            return 0.0,()
        best=(-1.0,())
        for s in options:
            gain=sum(_reward(items[i],ages[i]) for i in s)
            future,tail=solve(days-1,_advance(ages,s))
            candidate=(gain+future,(s,)+tail)
            if candidate[0]>best[0]+1e-12 or (abs(candidate[0]-best[0])<=1e-12 and candidate[1]<best[1]):
                best=candidate
        return best
    seq=solve(horizon,ages)[1]
    return tuple(tuple(items[i].id for i in s) for s in seq)


def evaluate(items:list[Item],budget:int,actions,initial_ages=None):
    ages=_validate(items,budget,len(actions),initial_ages)
    by_id={x.id:(i,x) for i,x in enumerate(items)}
    total=0.0
    for day in actions:
        if len(set(day))!=len(day) or any(i not in by_id for i in day):
            raise ValueError('invalid action')
        if sum(by_id[i][1].cost for i in day)>budget:
            raise ValueError('over budget')
        ids=set(day)
        total+=sum(_reward(x,ages[i]) for i,x in enumerate(items) if x.id in ids)
        ages=tuple(0 if x.id in ids else ages[i]+1 for i,x in enumerate(items))
    return total
