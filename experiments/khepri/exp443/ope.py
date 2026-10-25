"""Exp443: offline policy evaluation with contextual logging and support checks.
Standard library only. All data are synthetic and generated in memory.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class Domain:
    name: str
    p_context_1: float
    logging_p1: tuple[float, float]
    target: tuple[int, int]
    means: tuple[tuple[float, float], tuple[float, float]]
    noise: str
    scale: float

    def true_value(self) -> float:
        return ((1-self.p_context_1)*self.means[0][self.target[0]]
                + self.p_context_1*self.means[1][self.target[1]])


SEO = Domain('seo', .5, (.9,.9), (1,0), ((.40,.75),(.25,.65)), 'bernoulli',1.0)
GOLD = Domain('gold', .5, (.9,.9), (0,1), ((1.2,.1),(-.5,-.2)), 'gaussian',1.5)


def sample(domain: Domain, n: int, rng: random.Random):
    data=[]
    for _ in range(n):
        x = int(rng.random() < domain.p_context_1)
        p1=domain.logging_p1[x]
        a=int(rng.random()<p1)
        mean=domain.means[x][a]
        if domain.noise=='bernoulli':
            r=float(rng.random()<mean)
        else:
            r=rng.gauss(mean,domain.scale)
        data.append((x,a,r,p1))
    return data


def propensity(row, target_action):
    x,a,r,p1=row
    return p1 if target_action==1 else 1-p1


def validate_support(domain: Domain):
    for x in (0,1):
        if (domain.p_context_1 if x else 1-domain.p_context_1)==0:
            continue
        p=domain.logging_p1[x] if domain.target[x] else 1-domain.logging_p1[x]
        if p <= 0:
            raise ValueError(f'positivity violated for context {x}: target action has zero support')
        if p > 1:
            raise ValueError('invalid probability')


def fit_outcomes(rows, prior=0.5, strength=3):
    sums=[[0.0,0.0],[0.0,0.0]]
    counts=[[0,0],[0,0]]
    for x,a,r,_ in rows:
        sums[x][a]+=r
        counts[x][a]+=1
    return [[(sums[x][a]+prior*strength)/(counts[x][a]+strength)
             for a in (0,1)] for x in (0,1)]


def estimate(domain: Domain, rows, *, crossfit=True, propensity_override=None):
    validate_support(domain)
    n=len(rows)
    if n < 4:
        raise ValueError('at least four observations required')
    matched=[]; weights=[]; ipsterms=[]; drterms=[]
    # Deterministic split by index, independent of rewards and actions.
    folds=(fit_outcomes(rows[1::2]),fit_outcomes(rows[::2])) if crossfit else (fit_outcomes(rows),)*2
    for i,row in enumerate(rows):
        x,a,r,p1=row
        t=domain.target[x]
        if propensity_override is not None:
            p1=propensity_override
        p=p1 if t else 1-p1
        if p<=0: raise ValueError('zero logged propensity for target action')
        w=(1/p) if a==t else 0.0
        if a==t: matched.append(r)
        weights.append(w)
        ipsterms.append(w*r)
        q=folds[i%2][x][t]
        drterms.append(q+w*(r-q))
    wsum=sum(weights)
    return {'naive':sum(matched)/len(matched) if matched else float('nan'),
            'ips':sum(ipsterms)/n,
            'snips':sum(ipsterms)/wsum if wsum else float('nan'),
            'dr':sum(drterms)/n,
            'ess':wsum**2/sum(w*w for w in weights) if wsum else 0,
            'matches':len(matched),
            'n':n}


def run_benchmark(domain: Domain, repeats=300, n=600, seed=443):
    true=domain.true_value()
    values={key:[] for key in ('naive','ips','snips','dr','ess')}
    for k in range(repeats):
        rows=sample(domain,n,random.Random(seed+100000*k))
        result=estimate(domain,rows)
        for key in values:
            values[key].append(result[key])
    summary={}
    for key,seq in values.items():
        avg=sum(seq)/len(seq)
        if key=='ess':
            summary[key]={'mean':round(avg,4)}
        else:
            summary[key]={'mean':round(avg,4),'bias':round(avg-true,4),
                          'rmse':round(math.sqrt(sum((x-true)**2 for x in seq)/len(seq)),4)}
    return {'domain':domain.name,'truth':true,'repeats':repeats,'n':n,'summary':summary}
