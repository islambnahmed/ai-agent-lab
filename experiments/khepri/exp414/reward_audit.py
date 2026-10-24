"""Synthetic refresh-policy evaluation under competing reward definitions.
Reproduces exp413 censored estimator and scheduler decisions; latent Poisson
counts are hidden from policies and used only in objective evaluation.
Standard library only. Research only; no external actions.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Observation:
    exposure: int
    changed: bool

def _score_positive(exposure, rate):
    x = exposure * rate
    if x >= 700: return 0.0
    return exposure / math.expm1(x)

def censored_map(history, shape=1.5, prior_rate=1.0):
    neg = sum(x.exposure for x in history if not x.changed)
    pos = [x.exposure for x in history if x.changed]
    def score(r):
        return (shape-1)/r - prior_rate - neg + sum(_score_positive(t,r) for t in pos)
    lo, hi = 0., max(1.,(shape-1+len(pos))/prior_rate)
    for _ in range(64):
        mid=(lo+hi)/2
        if score(mid)>0: lo=mid
        else: hi=mid
    return (lo+hi)/2

def naive_rate(history):
    return (.5+sum(x.changed for x in history))/(1+sum(x.exposure for x in history))

def probability(rate, days):
    return -math.expm1(-rate*days)

def select(impacts, ages, rates, budget):
    scores=[impacts[i]*probability(rates[i],ages[i]+1) for i in range(len(impacts))]
    return tuple(sorted(sorted(range(len(impacts)),key=lambda i:(-scores[i],i))[:budget]))

def make_schedule(impacts, true_rates, counts, policy, budget):
    """Decisions use only binary observations, never hidden event counts."""
    n=len(impacts)
    if (not n or len(true_rates)!=n or len(counts)!=n or
        not all(math.isfinite(x) and x>=0 for x in impacts) or
        not all(math.isfinite(x) and x>=0 for x in true_rates) or
        not isinstance(budget,int) or isinstance(budget,bool) or
        not 0<=budget<=n or not counts[0] or
        any(len(row)!=len(counts[0]) or any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in row) for row in counts)):
        raise ValueError('invalid policy inputs')
    days=len(counts[0]); last=[-1]*n
    hist=[[] for _ in range(n)];checks=[]
    for day in range(days):
        ages=[day-1-last[i] for i in range(n)]
        if policy=='oracle':rates=true_rates
        elif policy=='censored':rates=[censored_map(x) for x in hist]
        elif policy=='naive':rates=[naive_rate(x) for x in hist]
        elif policy=='round_robin':
            chosen=tuple((day*budget+j)%n for j in range(budget))
            checks.append(chosen)
            for i in chosen:
                changed=any(counts[i][t]>0 for t in range(last[i]+1,day+1))
                hist[i].append(Observation(day-last[i],changed));last[i]=day
            continue
        elif policy=='freshness_oracle':
            # One-day staleness-risk proxy: prioritize sources likely to change today.
            rates=true_rates
            scores=[impacts[i]*probability(rates[i],1) for i in range(n)]
            chosen=tuple(sorted(sorted(range(n),key=lambda i:(-scores[i],i))[:budget]))
            checks.append(chosen)
            for i in chosen:
                changed=any(counts[i][t]>0 for t in range(last[i]+1,day+1))
                hist[i].append(Observation(day-last[i],changed));last[i]=day
            continue
        else: raise ValueError(policy)
        chosen=select(impacts,ages,rates,budget)
        checks.append(chosen)
        for i in chosen:
            changed=any(counts[i][t]>0 for t in range(last[i]+1,day+1))
            hist[i].append(Observation(day-last[i],changed));last[i]=day
    return checks

def replay(impacts, counts, schedule, tau=1.5):
    """Binary hits, delay-discounted events, and before/after-check stale days."""
    n=len(impacts);days=len(schedule);last=[-1]*n
    if (not n or len(counts)!=n or
        any(len(row)!=days for row in counts) or
        not math.isfinite(tau) or tau<=0 or
        any(len(set(row))!=len(row) or any(not isinstance(i,int) or isinstance(i,bool) or not 0<=i<n for i in row) for row in schedule)):
        raise ValueError('invalid replay inputs')
    binary_hits=0.;timely_events=0.;stale_days=0.;stale_days_after=0.;events_total=0
    for day in range(days):
        chosen=set(schedule[day]);assert len(chosen)==len(schedule[day])
        for i in range(n):
            events_total+=counts[i][day]
            if any(counts[i][t]>0 for t in range(last[i]+1,day+1)):
                stale_days+=impacts[i]
            if i in chosen:
                if any(counts[i][t]>0 for t in range(last[i]+1,day+1)):
                    binary_hits+=impacts[i]
                timely_events+=impacts[i]*sum(counts[i][t]*math.exp(-(day-t)/tau)
                                               for t in range(last[i]+1,day+1))
                last[i]=day
            if any(counts[i][t]>0 for t in range(last[i]+1,day+1)):
                stale_days_after+=impacts[i]
    return {'binary_hits':binary_hits,'timely_events':timely_events,
            'stale_days':stale_days,'stale_days_after':stale_days_after,
            'events_total':events_total}

def poisson(lam,rng):
    target=math.exp(-lam);p=1.;n=0
    while p>target:
        n+=1;p*=rng.random()
    return n-1

def sample_counts(rates,days,rng):
    return [[poisson(rate,rng) for _ in range(days)] for rate in rates]
