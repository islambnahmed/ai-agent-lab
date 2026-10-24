"""Offline exact budgeted test-portfolio planning under independent interval risk weights.
No tools, network, or external side effects. Python standard library only.
"""
from dataclasses import dataclass
from itertools import product
from math import isfinite
import random


@dataclass(frozen=True)
class Task:
    name: str
    cost: int
    covers: frozenset[str]
    requires: tuple[str, ...] = ()


class RobustPlanner:
    def __init__(self, tasks, intervals, budget):
        tasks = tuple(tasks)
        self.tasks = {t.name: t for t in tasks}
        if not tasks or len(self.tasks) != len(tasks) or len(tasks) > 12:
            raise ValueError('1..12 unique tasks required')
        if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
            raise ValueError('invalid budget')
        self.budget = budget
        self.intervals = dict(intervals)
        if not self.intervals:
            raise ValueError('no risks')
        for pair in self.intervals.values():
            if len(pair) != 2 or any(not isinstance(x, (int, float)) or not isfinite(x) for x in pair) or not 0 <= pair[0] <= pair[1]:
                raise ValueError('invalid interval')
        self.risks = tuple(sorted(self.intervals))
        self.names = tuple(sorted(self.tasks))
        for t in tasks:
            if not t.name or not isinstance(t.cost, int) or isinstance(t.cost, bool) or t.cost <= 0:
                raise ValueError('invalid task')
            if not t.covers <= self.intervals.keys() or any(dep not in self.tasks for dep in t.requires):
                raise ValueError('unknown risk/dependency')
        self.closure = {}
        visiting = set()
        def visit(name):
            if name in visiting:
                raise ValueError('dependency cycle')
            if name not in self.closure:
                visiting.add(name)
                s = {name}
                for d in self.tasks[name].requires:
                    s.update(visit(d))
                visiting.remove(name)
                self.closure[name] = frozenset(s)
            return self.closure[name]
        for n in self.names:
            visit(n)
        self.plans = self._enumerate()

    def _enumerate(self):
        plans = []
        for mask in range(1 << len(self.names)):
            chosen = frozenset(self.names[i] for i in range(len(self.names)) if mask & (1 << i))
            if any(not self.closure[n] <= chosen for n in chosen):
                continue
            cost = sum(self.tasks[n].cost for n in chosen)
            if cost > self.budget:
                continue
            covered = frozenset().union(*(self.tasks[n].covers for n in chosen))
            plans.append((chosen, cost, covered))
        return plans

    def utility(self, plan, weights):
        return sum(weights[r] for r in plan[2])

    def worst_regret(self, plan):
        """Exact over the Cartesian product of intervals: adversary favors competitor-only risks."""
        p = plan[2]
        return max(sum(self.intervals[r][1] for r in q[2] - p) -
                   sum(self.intervals[r][0] for r in p - q[2]) for q in self.plans)

    def choose(self, objective):
        if objective == 'nominal':
            weights = {r: sum(self.intervals[r]) / 2 for r in self.risks}
            key = lambda p: (-self.utility(p, weights), p[1], tuple(sorted(p[0])))
        elif objective == 'maximin':
            weights = {r: self.intervals[r][0] for r in self.risks}
            key = lambda p: (-self.utility(p, weights), p[1], tuple(sorted(p[0])))
        elif objective == 'minimax_regret':
            mid = {r: sum(self.intervals[r]) / 2 for r in self.risks}
            key = lambda p: (self.worst_regret(p), -self.utility(p, mid), p[1], tuple(sorted(p[0])))
        else:
            raise ValueError('unknown objective')
        return min(self.plans, key=key)


def generate(seed, domain):
    rng = random.Random(seed)
    if domain == 'seo':
        risks = ['indexing', 'canonicals', 'crawl', 'schema', 'content', 'speed', 'links', 'rendering']
    elif domain == 'gold':
        risks = ['freshness', 'parsing', 'timezone', 'fx', 'spread', 'outliers', 'duplicates', 'liquidity']
    else:
        raise ValueError('unknown domain')
    intervals = {r: (rng.randint(0, 12), 0) for r in risks}
    intervals = {r: (lo, lo + rng.randint(0, 28)) for r, (lo, _) in intervals.items()}
    tasks = []
    for i in range(9):
        covers = frozenset(rng.sample(risks, rng.randint(1, 2)))
        requires = (f't{rng.randrange(i)}',) if i > 0 and rng.random() < 0.28 else ()
        tasks.append(Task(f't{i}', rng.randint(1, 5), covers, requires))
    budget = rng.randint(5, 9)
    return RobustPlanner(tasks, intervals, budget)


def sampled_weights(planner, rng, shape):
    if shape == 'uniform':
        draw = lambda: rng.random()
    elif shape == 'low':
        draw = lambda: rng.betavariate(2, 6)
    elif shape == 'high':
        draw = lambda: rng.betavariate(6, 2)
    else:
        raise ValueError(shape)
    return {r: lo + (hi-lo) * draw() for r, (lo, hi) in planner.intervals.items()}
