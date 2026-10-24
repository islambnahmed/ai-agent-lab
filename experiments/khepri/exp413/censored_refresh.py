"""Binary interval-censored Poisson rate inference and adaptive refresh. Research only."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Observation:
    exposure: int
    changed: bool

def _validate(observations, shape, prior_rate):
    if not (math.isfinite(shape) and shape > 1 and math.isfinite(prior_rate) and prior_rate > 0):
        raise ValueError('Gamma prior requires shape>1 and prior_rate>0')
    for o in observations:
        if isinstance(o.exposure, bool) or not isinstance(o.exposure, int) or o.exposure <= 0 or not isinstance(o.changed, bool):
            raise ValueError('exposure must be positive integer and changed must be boolean')

def _positive_score(exposure, lam):
    x = exposure * lam
    if x > 45:
        return exposure * math.exp(-x) / (1.0 - math.exp(-x)) if x < 700 else 0.0
    return exposure / math.expm1(x)

def censored_map(observations, shape=1.5, prior_rate=1.0):
    """Posterior mode from P(observed change) = 1-exp(-rate*exposure)."""
    observations = tuple(observations)
    _validate(observations, shape, prior_rate)
    negatives = sum(o.exposure for o in observations if not o.changed)
    positives = tuple(o.exposure for o in observations if o.changed)
    def score(lam):
        return (shape-1.0)/lam - prior_rate - negatives + sum(_positive_score(t,lam) for t in positives)
    lo = 0.0
    hi = max(1.0,(shape-1.0+len(positives))/prior_rate)
    while score(hi)>0:
        hi *= 2
        if not math.isfinite(hi):
            raise ArithmeticError('failed to bracket posterior mode')
    for _ in range(64):
        mid=(lo+hi)/2
        if score(mid)>0:lo=mid
        else:hi=mid
    return (lo+hi)/2

def naive_count_rate(observations, pseudo_events=0.5, pseudo_days=1.0):
    """Misspecified baseline: each positive interval counted as one event."""
    observations=tuple(observations)
    _validate(observations,1.5,1.0)
    return (pseudo_events+sum(o.changed for o in observations))/(pseudo_days+sum(o.exposure for o in observations))

def probability(rate,days):
    if not (math.isfinite(rate) and rate>=0 and isinstance(days,int) and not isinstance(days,bool) and days>0):
        raise ValueError('invalid rate/days')
    return -math.expm1(-rate*days)

def choose_refresh(impacts,ages,rates,budget):
    if not (len(impacts)==len(ages)==len(rates) and 0<=budget<=len(impacts)):
        raise ValueError('invalid selection inputs')
    values=[impacts[i]*probability(rates[i],ages[i]+1) for i in range(len(impacts))]
    return tuple(sorted(sorted(range(len(impacts)),key=lambda i:(-values[i],i))[:budget]))

def run_policy(impacts,true_rates,latent,method,budget=2):
    """Evaluate policy on shared pre-generated daily latent event flags."""
    n=len(impacts);days=len(latent[0])
    if len(true_rates)!=n or len(latent)!=n or any(len(x)!=days for x in latent):
        raise ValueError('invalid latent event matrix')
    if method not in ('censored','naive','oracle'):
        raise ValueError('unknown method')
    history=[[] for _ in range(n)];last=[-1]*n;total=0.0;checks=[0]*n
    for day in range(days):
        ages=[day-1-last[i] for i in range(n)]
        if method=='oracle':rates=true_rates
        elif method=='censored':rates=[censored_map(history[i]) for i in range(n)]
        else:rates=[naive_count_rate(history[i]) for i in range(n)]
        selected=choose_refresh(impacts,ages,rates,budget)
        for i in selected:
            changed=any(latent[i][t] for t in range(last[i]+1,day+1))
            total+=impacts[i]*changed
            history[i].append(Observation(day-last[i],changed))
            last[i]=day;checks[i]+=1
    return total,tuple(checks)
