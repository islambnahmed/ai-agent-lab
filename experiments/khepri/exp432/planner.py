"""Budgeted risk-coverage planning with prerequisite closures; standard library only.

This is an offline *planning* model. It does not execute tool calls.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Iterable

MAX_EXACT_TASKS = 18

@dataclass(frozen=True)
class Task:
    name: str
    cost: int
    covers: frozenset[str]
    requires: tuple[str, ...] = ()

@dataclass(frozen=True)
class Plan:
    tasks: tuple[str, ...]  # topologically sorted
    cost: int
    value: float
    covered: frozenset[str]

class Planner:
    def __init__(self, tasks: Iterable[Task], risks: Mapping[str, float], budget: int):
        items = tuple(tasks)
        self.tasks = {t.name: t for t in items}
        if not self.tasks or len(self.tasks) != len(items):
            raise ValueError("tasks must be nonempty with unique names")
        self.risks = dict(risks)
        self.budget = budget
        if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
            raise ValueError("budget must be nonnegative integer")
        if not self.risks or any(not isinstance(v, (int, float)) or not isfinite(v) or v < 0 for v in self.risks.values()):
            raise ValueError("risks must be finite nonnegative weights")
        for name, task in self.tasks.items():
            if not name or not isinstance(name, str):
                raise ValueError("invalid task name")
            if not isinstance(task.cost, int) or isinstance(task.cost, bool) or task.cost <= 0:
                raise ValueError("cost must be positive integer")
            if not task.covers <= self.risks.keys():
                raise ValueError("task covers unknown risk")
            if name in task.requires or any(r not in self.tasks for r in task.requires):
                raise ValueError("self/unknown prerequisite")
        self.names = tuple(sorted(self.tasks))
        self._closure = {}
        visiting = set()
        def visit(name):
            if name in visiting:
                raise ValueError("cyclic prerequisites")
            if name not in self._closure:
                visiting.add(name)
                out = {name}
                for r in self.tasks[name].requires:
                    out.update(visit(r))
                visiting.remove(name)
                self._closure[name] = frozenset(out)
            return self._closure[name]
        for name in self.names:
            visit(name)

    def plan(self, selected: Iterable[str]) -> Plan:
        chosen = set(selected)
        if not chosen <= self.tasks.keys():
            raise ValueError("unknown task")
        if any(not self._closure[n] <= chosen for n in chosen):
            raise ValueError("prerequisites missing")
        cost = sum(self.tasks[n].cost for n in chosen)
        if cost > self.budget:
            raise ValueError("selected tasks exceed budget")
        covered = frozenset().union(*(self.tasks[n].covers for n in chosen))
        value = float(sum(self.risks[m] for m in covered))
        order = []
        visited = set()
        def emit(n):
            if n in visited:
                return
            for r in sorted(self.tasks[n].requires):
                emit(r)
            visited.add(n)
            order.append(n)
        for n in sorted(chosen):
            emit(n)
        return Plan(tuple(order), cost, value, covered)

    def greedy(self, *, marginal: bool) -> Plan:
        """Select prerequisite bundles by value/cost. marginal=False is naive control."""
        chosen = set()
        covered = set()
        while True:
            options = []
            for name in self.names:
                bundle = self._closure[name] - chosen
                if not bundle:
                    continue
                extra_cost = sum(self.tasks[n].cost for n in bundle)
                if extra_cost > self.budget - sum(self.tasks[n].cost for n in chosen):
                    continue
                if marginal:
                    new_modes = set().union(*(self.tasks[n].covers for n in bundle)) - covered
                    gain = sum(self.risks[m] for m in new_modes)
                else:
                    # Deliberately wrong: counts already covered risks and overlap within a bundle.
                    gain = sum(sum(self.risks[m] for m in self.tasks[n].covers) for n in bundle)
                if gain > 0:
                    options.append((gain / extra_cost, gain, -extra_cost, name, bundle))
            if not options:
                break
            # deterministic, stable alphabetical tie-break
            best = sorted(options, key=lambda x: (-x[0], -x[1], -x[2], x[3]))[0]
            chosen.update(best[4])
            covered.update(set().union(*(self.tasks[n].covers for n in best[4])))
        return self.plan(chosen)

    def exact(self) -> Plan:
        """Exhaustive oracle for small instances. Raises for >MAX_EXACT_TASKS."""
        if len(self.names) > MAX_EXACT_TASKS:
            raise ValueError("instance too large for exact search")
        n = len(self.names)
        costs = [self.tasks[x].cost for x in self.names]
        deps = [sum(1 << self.names.index(r) for r in self._closure[x]) for x in self.names]
        cover = [self.tasks[x].covers for x in self.names]
        best = self.plan(())
        for mask in range(1, 1 << n):
            cost = 0
            valid = True
            modes = set()
            for i in range(n):
                if mask & (1 << i):
                    cost += costs[i]
                    if cost > self.budget or (mask & deps[i]) != deps[i]:
                        valid = False
                        break
                    modes.update(cover[i])
            if not valid:
                continue
            value = sum(self.risks[m] for m in modes)
            if value > best.value + 1e-9 or (abs(value - best.value) <= 1e-9 and cost < best.cost):
                best = self.plan(self.names[i] for i in range(n) if mask & (1 << i))
        return best
