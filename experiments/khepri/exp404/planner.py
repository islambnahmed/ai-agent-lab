"""Research-only reliability planner for parallel redundant read-only tools.

Model: each failure domain has one Bernoulli outage per run. Conditional on
those outages, every tool invocation succeeds independently. A stage succeeds
if any of its parallel tools succeeds; a plan succeeds if every stage succeeds.
All scheduled invocations incur fixed cost, even if an earlier stage fails.
No external tools are invoked by this module.
"""
from dataclasses import dataclass
from itertools import product
from math import prod
import random


@dataclass(frozen=True)
class Tool:
    name: str
    domain: str
    healthy: float
    outage: float
    cost: float


@dataclass(frozen=True)
class Plan:
    name: str
    stages: tuple[tuple[str, ...], ...]


def validate(tools: dict[str, Tool], outages: dict[str, float], plan: Plan) -> None:
    if not plan.stages or len(outages) > 16:
        raise ValueError('empty plan or too many failure domains')
    for q in outages.values():
        if not 0 <= q <= 1:
            raise ValueError('outage probability outside [0,1]')
    seen = set()
    for stage in plan.stages:
        if not stage:
            raise ValueError('empty stage')
        for name in stage:
            if name not in tools or name in seen:
                raise ValueError('unknown or repeated tool invocation')
            seen.add(name)
            t = tools[name]
            if t.domain not in outages or not (0 <= t.healthy <= 1 and 0 <= t.outage <= 1 and t.cost >= 0):
                raise ValueError('invalid tool parameters')


def fixed_cost(tools: dict[str, Tool], plan: Plan) -> float:
    return sum(tools[name].cost for stage in plan.stages for name in stage)


def exact_success(tools: dict[str, Tool], outages: dict[str, float], plan: Plan) -> float:
    validate(tools, outages, plan)
    domains = sorted({tools[name].domain for stage in plan.stages for name in stage})
    total = 0.0
    for bits in product((False, True), repeat=len(domains)):
        states = dict(zip(domains, bits))
        weight = prod(outages[d] if states[d] else 1 - outages[d] for d in domains)
        stage_probs = []
        for stage in plan.stages:
            stage_probs.append(1 - prod(1 - (tools[n].outage if states[tools[n].domain] else tools[n].healthy) for n in stage))
        total += weight * prod(stage_probs)
    return total


def naive_success(tools: dict[str, Tool], outages: dict[str, float], plan: Plan) -> float:
    """Incorrect baseline: treats every invocation as marginally independent."""
    validate(tools, outages, plan)
    marginal = {n: (1 - outages[t.domain]) * t.healthy + outages[t.domain] * t.outage for n, t in tools.items()}
    return prod(1 - prod(1 - marginal[n] for n in stage) for stage in plan.stages)


def monte_carlo(tools: dict[str, Tool], outages: dict[str, float], plan: Plan, n: int, seed: int) -> float:
    validate(tools, outages, plan)
    if n <= 0:
        raise ValueError('n must be positive')
    rng = random.Random(seed)
    domains = sorted({tools[name].domain for stage in plan.stages for name in stage})
    successes = 0
    for _ in range(n):
        state = {d: rng.random() < outages[d] for d in domains}
        if all(any(rng.random() < (tools[name].outage if state[tools[name].domain] else tools[name].healthy) for name in stage) for stage in plan.stages):
            successes += 1
    return successes / n


def select(tools: dict[str, Tool], outages: dict[str, float], plans: tuple[Plan, ...], reward: float, method: str = 'exact'):
    if not plans or reward < 0:
        raise ValueError('invalid reward or plans')
    if method not in ('exact', 'naive'):
        raise ValueError('unknown method')
    scorer = exact_success if method == 'exact' else naive_success
    scores = {p.name: reward * scorer(tools, outages, p) - fixed_cost(tools, p) for p in plans}
    if len(scores) != len(plans):
        raise ValueError('duplicate plan name')
    return max(scores, key=scores.get), scores
