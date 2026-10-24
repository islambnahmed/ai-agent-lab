"""Fixed-roster, complete-opportunity e-process gate (research prototype).

A round exists independently of its outcome. For each registered candidate j,
there is a bounded potential score X[j,t] in [-1,1] with
E[X[j,t] | full prior history] <= 0 under its null.

If a score is missing (even missing-not-at-random), replace it with -1:
Y[j,t] = X[j,t] if observed, otherwise -1 <= X[j,t].
Consequently E[Y[j,t] | prior] <= 0. This preserves validity of the
betting e-process; power can be much worse. It cannot guarantee that
opportunity rounds were honestly enumerated or that the underlying
potential score exists and satisfies the conditional-null assumption.
"""
from __future__ import annotations
import math

DEFAULT_LAMBDAS = (.05, .1, .2, .4, .8)


def _finite_number(value):
    return type(value) in (float, int) and math.isfinite(value)


class OpportunityGate:
    """A pre-registered roster, one sealed update per opportunity round."""
    def __init__(self, candidates, alpha=.05, lambdas=DEFAULT_LAMBDAS):
        names = tuple(candidates)
        if not names or any(type(n) is not str or not n for n in names) or len(set(names)) != len(names):
            raise ValueError('candidates must be unique nonempty strings')
        if not _finite_number(alpha) or not 0 < alpha < 1:
            raise ValueError('alpha must be in (0,1)')
        ls = tuple(lambdas)
        if not ls or any(not _finite_number(x) or not 0 <= x < 1 for x in ls):
            raise ValueError('lambdas must be in [0,1)')
        self.candidates = names
        self.alpha = float(alpha)
        self.lambdas = ls
        self.round = 0
        self._components = {n: [0.] * len(ls) for n in names}
        self.crossings = {}
        self.missing_counts = {n: 0 for n in names}

    def observe(self, round_number, scores):
        """Absent keys and explicit None both count as a missing score (-1)."""
        if type(round_number) is not int or round_number != self.round + 1:
            raise ValueError('round must advance by exactly one')
        if type(scores) is not dict or set(scores) - set(self.candidates):
            raise ValueError('scores must be a dict with only roster names')
        for score in scores.values():
            if score is not None and (not _finite_number(score) or not -1 <= score <= 1):
                raise ValueError('invalid score')
        # Atomic validation above; no partial mutation if input invalid.
        self.round = round_number
        for name in self.candidates:
            x = scores.get(name)
            if x is None:
                x = -1.
                self.missing_counts[name] += 1
            logs = self._components[name]
            for i, lam in enumerate(self.lambdas):
                logs[i] += math.log1p(lam*x)
            if name not in self.crossings and self.log_e(name) >= -math.log(self.alpha/len(self.candidates)):
                self.crossings[name] = self.round
        return tuple(sorted(self.crossings))

    def log_e(self, name):
        logs = self._components[name]
        maximum = max(logs)
        return maximum + math.log(math.fsum(math.exp(x-maximum) for x in logs)/len(logs))

    def snapshot(self):
        return {name: {'log_e': self.log_e(name), 'missing': self.missing_counts[name],
                       'first_crossing': self.crossings.get(name)} for name in self.candidates}
