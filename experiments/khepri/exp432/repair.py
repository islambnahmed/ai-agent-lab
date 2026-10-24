"""Reversible dependency-aware local repair for offline budgeted test planning.

Adds seeded starts and 1/2-drop neighborhood search to exp431's greedy planner.
No tasks are executed. Standard library only.
"""
from __future__ import annotations
from itertools import combinations
from planner import Planner, Plan


def fill(p: Planner, initial=(), *, forbidden=()) -> Plan:
    """Greedy marginal coverage from an already feasible prerequisite-closed set."""
    chosen = set(initial)
    forbidden = set(forbidden)
    if chosen & forbidden:
        raise ValueError("selected tasks cannot be forbidden")
    p.plan(chosen)  # validates dependencies and budget
    covered = set().union(*(p.tasks[n].covers for n in chosen))
    cost = sum(p.tasks[n].cost for n in chosen)
    while True:
        options = []
        for name in p.names:
            extra = p._closure[name] - chosen
            if not extra or (p._closure[name] & forbidden):
                continue
            extra_cost = sum(p.tasks[n].cost for n in extra)
            if extra_cost > p.budget - cost:
                continue
            modes = set().union(*(p.tasks[n].covers for n in extra)) - covered
            gain = sum(p.risks[m] for m in modes)
            if gain > 0:
                options.append((-gain / extra_cost, -gain, extra_cost, name, extra, modes))
        if not options:
            break
        _, _, extra_cost, _, extra, modes = min(options)
        chosen.update(extra)
        covered.update(modes)
        cost += extra_cost
    return p.plan(chosen)


def better(a: Plan, b: Plan) -> bool:
    """Lexicographic preference: higher value, then lower cost."""
    return a.value > b.value + 1e-9 or (abs(a.value-b.value) <= 1e-9 and a.cost < b.cost)


def drop_and_repair(p: Planner, plan: Plan, drop: tuple[str, ...]) -> Plan:
    """Remove dropped tasks AND every selected dependent, then refill."""
    selected = set(plan.tasks)
    dropped = set(drop)
    if not dropped <= selected:
        raise ValueError("drop must be selected tasks")
    retained = {name for name in selected if not (p._closure[name] & dropped)}
    return fill(p, retained, forbidden=dropped)


def optimize(p: Planner, *, max_drop: int = 1, seeded: bool = False,
             max_rounds: int = 20) -> Plan:
    """Monotone repair. Does not claim global optimality.

    With seeded=True, also try a feasible prerequisite bundle for every task
    as the first step. max_drop is 1 or 2, bounding neighborhood cost.
    """
    if max_drop not in (1, 2) or max_rounds < 0:
        raise ValueError("max_drop must be 1 or 2 and max_rounds nonnegative")
    best = fill(p)
    if seeded:
        for name in p.names:
            seed = p._closure[name]
            if sum(p.tasks[n].cost for n in seed) <= p.budget:
                candidate = fill(p, seed)
                if better(candidate, best):
                    best = candidate
    for _ in range(max_rounds):
        replacement = best
        for size in range(1, min(max_drop, len(best.tasks)) + 1):
            for dropped in combinations(sorted(best.tasks), size):
                candidate = drop_and_repair(p, best, dropped)
                if better(candidate, replacement):
                    replacement = candidate
        if not better(replacement, best):
            break
        best = replacement
    return best
