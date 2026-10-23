"""One-fallback adaptive planner with correlated failure domains.

Pure standard-library research implementation. No network calls or side effects.
Worlds enumerate a latent common shock and shared domain outages; endpoints
are conditionally independent *given* both. This does not infer real outages.
"""
from dataclasses import dataclass
from itertools import product
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
    calm: dict[str, float]
    shocked: dict[str, float]


def _prob(x):
    return isinstance(x, (int, float)) and isfinite(x) and 0 <= x <= 1


def validate(tools: dict[str, Tool], model: Model, reward: float, deadline: float = 1.0):
    if not tools or len(tools) > 12 or not _prob(model.shock) or not _prob(deadline):
        raise ValueError('invalid tool count, shock, or deadline')
    if not isfinite(reward) or reward < 0:
        raise ValueError('invalid reward')
    if not model.calm or model.calm.keys() != model.shocked.keys():
        raise ValueError('invalid domain sets')
    if any(not _prob(q) for rates in (model.calm, model.shocked) for q in rates.values()):
        raise ValueError('invalid domain rate')
    for name, t in tools.items():
        if name != t.name or t.domain not in model.calm or not _prob(t.healthy) or not _prob(t.outage) or not isfinite(t.cost) or t.cost < 0:
            raise ValueError('invalid tool')


def worlds(model: Model):
    domains = tuple(sorted(model.calm))
    for shock, mass, rates in ((False, 1-model.shock, model.calm), (True, model.shock, model.shocked)):
        if mass == 0:
            continue
        for state in product((False, True), repeat=len(domains)):
            weight = mass
            for d, out in zip(domains, state):
                weight *= rates[d] if out else 1-rates[d]
            if weight:
                yield weight, dict(zip(domains, state))


def conditional_tool_probability(t: Tool, domain_states: dict[str, bool]):
    return t.outage if domain_states[t.domain] else t.healthy


def pair_stats(tools: dict[str, Tool], model: Model, first: str, second: str):
    """P(A success), P(A fail and B success) and P(B success).

    Correctly integrates a shared domain outage; not P(A fail)*P(B success).
    """
    if first == second or first not in tools or second not in tools:
        raise ValueError('distinct known tools required')
    pa, fail_b, pb = 0., 0., 0.
    for weight, state in worlds(model):
        a = conditional_tool_probability(tools[first], state)
        b = conditional_tool_probability(tools[second], state)
        pa += weight*a
        fail_b += weight*(1-a)*b
        pb += weight*b
    return pa, fail_b, pb


def static_utility(tools, model, reward, selected: tuple[str, ...]):
    if not selected or len(selected) > 2 or len(set(selected)) != len(selected) or any(n not in tools for n in selected):
        raise ValueError('select one or two distinct tools')
    if len(selected) == 1:
        t = tools[selected[0]]
        p = sum(w*conditional_tool_probability(t, s) for w,s in worlds(model))
    else:
        pa, fail_b, _ = pair_stats(tools, model, *selected)
        p = pa + fail_b
    return reward*p - sum(tools[n].cost for n in selected)


def adaptive_policy(tools, model, reward, first, deadline=1.):
    """Choose fallback after observing first-tool failure; max one fallback.

    Deadline is probability that a sequential fallback result is still useful.
    Cost is incurred whenever fallback is called, even if it misses deadline.
    """
    validate(tools, model, reward, deadline)
    if first not in tools:
        raise ValueError('unknown first tool')
    p_a = sum(w*conditional_tool_probability(tools[first], s) for w,s in worlds(model))
    p_fail = max(0., 1-p_a)
    options = {}
    for second in sorted(tools):
        if second == first:
            continue
        _, p_fail_and_b, _ = pair_stats(tools, model, first, second)
        # conditional gain per failure; avoid division if failure is impossible
        options[second] = (reward*deadline*p_fail_and_b/p_fail - tools[second].cost) if p_fail > 1e-12 else -tools[second].cost
    second = max(options, key=options.get) if options else None
    if second is not None and options[second] <= 0:
        second = None
    utility = reward*p_a - tools[first].cost + (p_fail*options[second] if second else 0.)
    return {'first':first,'fallback':second,'utility':utility,'p_first_success':p_a,
            'p_fallback_invoked':p_fail if second else 0., 'conditional_gains':options}


def optimize(tools, model, reward, deadline=1.):
    validate(tools, model, reward, deadline)
    static = [(static_utility(tools,model,reward,(a,)),(a,)) for a in tools]
    names = sorted(tools)
    static += [(static_utility(tools,model,reward,(a,b)),(a,b)) for i,a in enumerate(names) for b in names[i+1:]]
    static_best = max(static, key=lambda item:item[0])
    adaptive = max((adaptive_policy(tools,model,reward,a,deadline) for a in names),key=lambda x:x['utility'])
    return {'static':{'utility':static_best[0],'tools':static_best[1]}, 'adaptive':adaptive,
            'gain':adaptive['utility']-static_best[0]}
