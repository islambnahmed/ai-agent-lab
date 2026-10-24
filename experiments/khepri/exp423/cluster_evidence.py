"""Cluster-boundary anytime-valid evidence for bounded paired gains.

A complete cluster is the unit of inference. Within-cluster observations may be
arbitrarily dependent; validity requires E[mean(cluster) | past clusters] <= 0.
Only examine evidence after a complete, predeclared cluster.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field

LAMBDAS = (0.05, 0.1, 0.2, 0.4, 0.8)


def _bounded(x):
    return type(x) in (int, float) and math.isfinite(x) and -1 <= x <= 1


@dataclass
class EProcess:
    alpha: float = 0.05
    lambdas: tuple[float, ...] = LAMBDAS
    log_wealth: list[float] = field(init=False)
    n: int = field(default=0, init=False)
    first_crossing: int | None = field(default=None, init=False)

    def __post_init__(self):
        if type(self.alpha) not in (float, int) or not math.isfinite(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError('alpha must be finite in (0,1)')
        self.lambdas = tuple(self.lambdas)
        if not self.lambdas or any(type(l) not in (float, int) or not math.isfinite(l) or not 0 <= l < 1 for l in self.lambdas):
            raise ValueError('lambdas must be finite in [0,1)')
        self.log_wealth = [0.] * len(self.lambdas)

    @property
    def log_e(self):
        m = max(self.log_wealth)
        return m + math.log(sum(math.exp(v - m) for v in self.log_wealth) / len(self.log_wealth))

    def update(self, x: float) -> float:
        if not _bounded(x):
            raise ValueError('gain must be a finite real in [-1,1] (not bool)')
        for i, lam in enumerate(self.lambdas):
            self.log_wealth[i] += math.log1p(lam * x)
        self.n += 1
        value = self.log_e
        if self.first_crossing is None and value >= -math.log(self.alpha):
            self.first_crossing = self.n
        return value


@dataclass
class ClusterAudit:
    alpha: float = 0.05
    clustered: EProcess = field(init=False)
    event_naive: EProcess = field(init=False)
    events_seen: int = field(default=0, init=False)

    def __post_init__(self):
        self.clustered = EProcess(self.alpha)
        self.event_naive = EProcess(self.alpha)

    def add_cluster(self, observations):
        """Atomic validation; no peeking at partial cluster for clustered decision."""
        xs = tuple(observations)
        if not xs or any(not _bounded(x) for x in xs):
            raise ValueError('cluster must contain bounded finite real observations')
        mean = math.fsum(xs) / len(xs)
        # Event stream deliberately violates the conditional-null assumption
        # when a persistent cluster-level shock drives correlated observations.
        for x in xs:
            self.event_naive.update(x)
        self.events_seen += len(xs)
        return self.clustered.update(mean)
