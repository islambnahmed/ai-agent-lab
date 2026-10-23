"""Maximin tool planning with a fixed but unknown shared-failure model.

Research-only, standard library, read-only decisions. Models are a finite
uncertainty set; the adversary chooses ONE model for the whole policy.
"""
from dataclasses import dataclass
from itertools import combinations, product
from math import isfinite


@dataclass(frozen=True)
class Tool:
    name: str
    domain: str
    healthy: float
    outage: float
    cost: float


@dataclass(frozen=True)
class Model:
    shock: float
    calm: dict
    shocked: dict


def _prob(x):
    return isinstance(x, (float, int)) and not isinstance(x, bool) and isfinite(x) and 0 <= x <= 1


def validate(tools, models, reward, deadline):
    if not (1 <= len(tools) <= 12 and 1 <= len(models) <= 16 and isfinite(reward) and reward >= 0 and _prob(deadline)):
        raise ValueError('invalid inputs')
    if any(n != t.name or not _prob(t.healthy) or not _prob(t.outage) or not isfinite(t.cost) or t.cost < 0 for n,t in tools.items()):
        raise ValueError('invalid tools')
    domains = {t.domain for t in tools.values()}
    for m in models:
        if not _prob(m.shock) or set(m.calm) != domains or set(m.shocked) != domains:
            raise ValueError('invalid model domains')
        if any(not _prob(q) for rates in (m.calm, m.shocked) for q in rates.values()):
            raise ValueError('invalid model probabilities')


def worlds(model):
    domains = tuple(sorted(model.calm))
    for mass, rates in ((1-model.shock, model.calm), (model.shock, model.shocked)):
        for state in product((False, True), repeat=len(domains)):
            w = mass
            for d, outage in zip(domains, state):
                w *= rates[d] if outage else 1-rates[d]
            if w:
                yield w, dict(zip(domains, state))


def pair_stats(tools, model, a, b):
    """P(A success), P(A fail and B success), P(A failure)."""
    pa, pfbs = 0., 0.
    for w, state in worlds(model):
        ta, tb = tools[a], tools[b]
        sa = ta.outage if state[ta.domain] else ta.healthy
        sb = tb.outage if state[tb.domain] else tb.healthy
        pa += w*sa
        pfbs += w*(1-sa)*sb
    return pa, pfbs, 1-pa


def policies(tools):
    names = sorted(tools)
    out = [('skip',)]
    out += [('single', a) for a in names]
    out += [('parallel', a, b) for a,b in combinations(names, 2)]
    out += [('adaptive', a, b) for a in names for b in names if a != b]
    return out


def utility(tools, model, reward, deadline, policy):
    kind = policy[0]
    if kind == 'skip':
        return 0.
    if kind == 'single':
        a = policy[1]
        p = sum(w*(tools[a].outage if s[tools[a].domain] else tools[a].healthy) for w,s in worlds(model))
        return reward*p - tools[a].cost
    a,b = policy[1:]
    pa,pfbs,pfail = pair_stats(tools, model, a, b)
    if kind == 'parallel':
        return reward*(pa+pfbs)-tools[a].cost-tools[b].cost
    if kind == 'adaptive':
        return reward*(pa+deadline*pfbs)-tools[a].cost-pfail*tools[b].cost
    raise ValueError('invalid policy')


def choose(tools, models, reward, deadline, nominal_index=0):
    validate(tools, models, reward, deadline)
    if not (0 <= nominal_index < len(models)):
        raise ValueError('invalid nominal index')
    scored = [(p, tuple(utility(tools,m,reward,deadline,p) for m in models)) for p in policies(tools)]
    # Stable deterministic tie-breaking by policy order.
    nominal = max(scored, key=lambda x: x[1][nominal_index])
    robust = max(scored, key=lambda x: min(x[1]))
    oracle = tuple(max(vals[i] for _,vals in scored) for i in range(len(models)))
    return {'nominal':nominal[0], 'robust':robust[0],
            'nominal_values':nominal[1], 'robust_values':robust[1],
            'nominal_worst':min(nominal[1]), 'robust_worst':min(robust[1]),
            'oracle':oracle, 'policy_count':len(scored)}
