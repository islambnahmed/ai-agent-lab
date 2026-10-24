"""Budgeted refresh scheduling for independent change hazards (research prototype).

The expected one-step reward is impact * P(at least one change since last check).
Optimality applies to this *one-step additive objective*, not to multi-day utility.
"""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Item:
    id: str
    cost: int
    impact: float
    rate: float  # Poisson changes/day, estimated externally
    age: float  # days since last successful check, at decision instant


def validate(items: list[Item], budget: int) -> list[Item]:
    if isinstance(budget, bool) or not isinstance(budget, int) or not 0 <= budget <= 10000:
        raise ValueError('budget must be an integer between 0 and 10000')
    if len(items) > 1000:
        raise ValueError('too many items')
    seen = set()
    for x in items:
        if not isinstance(x.id, str) or not x.id or x.id in seen:
            raise ValueError('duplicate or invalid id')
        seen.add(x.id)
        if isinstance(x.cost, bool) or not isinstance(x.cost, int) or x.cost <= 0:
            raise ValueError('cost must be a positive integer')
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0
               for v in (x.impact, x.rate, x.age)):
            raise ValueError('impact, rate, and age must be finite and nonnegative')
    return sorted(items, key=lambda x: x.id)


def value(item: Item) -> float:
    # expm1 is accurate for very small rate * age; avoids overflow in product
    p = -math.expm1(-item.rate * item.age)
    return item.impact * p


def choose(items: list[Item], budget: int, policy: str = 'dp') -> tuple[str, ...]:
    rows = validate(items, budget)
    if policy == 'dp':
        # dp[c] = (reward, tuple(ids)) for exactly c units spent.
        dp: list[tuple[float, tuple[str, ...]] | None] = [None] * (budget + 1)
        dp[0] = (0., ())
        for x in rows:
            if x.cost > budget or value(x) <= 0:
                continue
            reward = value(x)
            for c in range(budget, x.cost - 1, -1):
                prev = dp[c - x.cost]
                if prev is None:
                    continue
                candidate = (prev[0] + reward, prev[1] + (x.id,))
                old = dp[c]
                if old is None or candidate[0] > old[0] or (candidate[0] == old[0] and candidate[1] < old[1]):
                    dp[c] = candidate
        best = (0., 0, ())
        for cost, state in enumerate(dp):
            if state is not None and (state[0] > best[0] or
                (state[0] == best[0] and (cost, state[1]) < (best[1], best[2]))):
                best = (state[0], cost, state[1])
        return best[2]
    if policy == 'ratio':
        ordered = sorted(rows, key=lambda x: (-value(x) / x.cost, x.id))
    elif policy == 'oldest':
        ordered = sorted(rows, key=lambda x: (-x.age, x.id))
    else:
        raise ValueError('unknown policy')
    selected, remaining = [], budget
    for x in ordered:
        if x.cost <= remaining and value(x) > 0:
            selected.append(x.id)
            remaining -= x.cost
    return tuple(sorted(selected))


def expected_reward(items: list[Item], selected: tuple[str, ...]) -> float:
    ids = set(selected)
    return sum(value(x) for x in items if x.id in ids)
