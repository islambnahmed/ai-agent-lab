"""Joint-failure-domain planner via a two-regime common shock.

The shock is latent; conditional on it, failure domains are independent.
This generalizes exp403's independent-domain model, not observed field data.
No network calls, execution of tools, or external side effects.
"""
from dataclasses import dataclass
from math import isfinite
from random import Random
from planner import Tool, Plan, exact_success, fixed_cost, validate


@dataclass(frozen=True)
class ShockModel:
    probability: float
    calm: dict[str, float]
    shocked: dict[str, float]


def validate_shock(model: ShockModel) -> None:
    if not isfinite(model.probability) or not 0 <= model.probability <= 1:
        raise ValueError('invalid shock probability')
    if not model.calm or model.calm.keys() != model.shocked.keys():
        raise ValueError('regimes must contain the same nonempty domains')
    for regime in (model.calm, model.shocked):
        if any(not isfinite(v) or not 0 <= v <= 1 for v in regime.values()):
            raise ValueError('invalid conditional outage probability')


def marginals(model: ShockModel) -> dict[str, float]:
    validate_shock(model)
    return {d: (1 - model.probability) * model.calm[d] + model.probability * model.shocked[d]
            for d in model.calm}


def joint_success(tools: dict[str, Tool], model: ShockModel, plan: Plan) -> float:
    validate_shock(model)
    p = model.probability
    return (1-p) * exact_success(tools, model.calm, plan) + p * exact_success(tools, model.shocked, plan)


def independent_success(tools: dict[str, Tool], model: ShockModel, plan: Plan) -> float:
    return exact_success(tools, marginals(model), plan)


def select(tools: dict[str, Tool], model: ShockModel, plans: tuple[Plan, ...], reward: float, method='joint'):
    if not plans or len(set(p.name for p in plans)) != len(plans):
        raise ValueError('empty plans or duplicate names')
    if not isfinite(reward) or reward < 0 or method not in ('joint', 'independent'):
        raise ValueError('invalid reward or method')
    scorer = joint_success if method == 'joint' else independent_success
    scores = {p.name: reward * scorer(tools, model, p) - fixed_cost(tools, p) for p in plans}
    return max(scores, key=scores.get), scores


def monte_carlo_joint(tools: dict[str, Tool], model: ShockModel, plan: Plan, n: int, seed: int) -> float:
    validate_shock(model)
    validate(tools, model.calm, plan)
    if not isinstance(n, int) or n < 1:
        raise ValueError('invalid simulation count')
    rng = Random(seed)
    domains = sorted({tools[name].domain for stage in plan.stages for name in stage})
    success = 0
    for _ in range(n):
        regime = model.shocked if rng.random() < model.probability else model.calm
        states = {d: rng.random() < regime[d] for d in domains}
        stages_succeeded = []
        for stage in plan.stages:
            outcomes = [rng.random() < (tools[name].outage if states[tools[name].domain] else tools[name].healthy)
                        for name in stage]
            stages_succeeded.append(any(outcomes))
        success += all(stages_succeeded)
    return success / n
