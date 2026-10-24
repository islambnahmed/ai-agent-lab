"""Anytime-valid familywise gate for bounded predeclared complete-cluster gains.

Requires E[X_j,t | all completed prior rounds] <= 0 under each null.
Each candidate has a mixture e-process; thresholds alpha*weight_j
control FWER even with arbitrary same-round dependence across agents.
Selective logging, backfill, and persistent conditional-null violations
are outside the guarantee.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math

LAMBDAS = (0.05, 0.1, 0.2, 0.4, 0.8)

def _number(x):
    return type(x) in (int, float) and math.isfinite(x)

@dataclass
class _Mixture:
    lambdas: tuple[float, ...]
    log_components: list[float] = field(init=False)
    n: int = 0

    def __post_init__(self):
        self.log_components = [0.] * len(self.lambdas)

    @property
    def log_e(self):
        m = max(self.log_components)
        return m + math.log(math.fsum(math.exp(z-m) for z in self.log_components)/len(self.log_components))

    def update(self, x):
        for i, lam in enumerate(self.lambdas):
            self.log_components[i] += math.log1p(lam*x)
        self.n += 1

class FamilywiseGate:
    def __init__(self, alpha=.05, *, mode='fixed', slots=None, lambdas=LAMBDAS):
        if not _number(alpha) or not 0 < alpha < 1:
            raise ValueError('alpha must be finite in (0,1)')
        if mode not in ('fixed', 'online'):
            raise ValueError('mode must be fixed or online')
        if mode == 'fixed' and (type(slots) is not int or slots < 1):
            raise ValueError('fixed mode requires positive integer slots')
        if mode == 'online' and slots is not None:
            raise ValueError('online mode must not specify slots')
        self.lambdas = tuple(lambdas)
        if not self.lambdas or any(not _number(x) or not 0 <= x < 1 for x in self.lambdas):
            raise ValueError('lambdas must be finite in [0,1)')
        self.alpha = float(alpha)
        self.mode = mode
        self.slots = slots
        self.models = {}
        self.weights = {}
        self.crossings = {}
        self.last_round = 0

    def register(self, candidate):
        if type(candidate) is not str or not candidate or candidate in self.models:
            raise ValueError('candidate must be a new nonempty string')
        index = len(self.models)
        if self.mode == 'fixed' and index >= self.slots:
            raise ValueError('candidate slots exhausted')
        weight = 1/self.slots if self.mode == 'fixed' else 2.**(-index-1)
        if weight == 0.:
            raise ValueError('online weight underflow')
        self.models[candidate] = _Mixture(self.lambdas)
        self.weights[candidate] = weight
        return weight

    def observe(self, round_number, gains):
        """Atomic validation. One completed cluster score per candidate/round."""
        if type(round_number) is not int or round_number <= self.last_round:
            raise ValueError('round_number must strictly increase')
        if type(gains) is not dict:
            raise ValueError('gains must be a dict')
        for name, x in gains.items():
            if name not in self.models or not _number(x) or not -1 <= x <= 1:
                raise ValueError('unknown candidate or invalid bounded gain')
        self.last_round = round_number
        for name, x in gains.items():
            model = self.models[name]
            model.update(x)
            threshold = -math.log(self.alpha*self.weights[name])
            if name not in self.crossings and model.log_e >= threshold:
                self.crossings[name] = round_number
        return tuple(sorted(self.crossings))

    def snapshot(self):
        return {name: {'weight': self.weights[name], 'n': model.n,
                       'log_e': model.log_e,
                       'first_crossing_round': self.crossings.get(name)}
                for name, model in self.models.items()}
