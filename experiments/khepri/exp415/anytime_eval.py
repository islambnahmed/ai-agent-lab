"""Anytime-valid paired comparison for bounded gains in [-1,1].

Under H0 E[X_t | history] <= 0 and a predeclared predictable policy,
E_t(lambda) = product_{s<=t}(1 + lambda * X_s) is a nonnegative
supermartingale. Mixtures over fixed lambdas remain e-processes.
No independence assumption is required, but conditional validity is.
"""
from __future__ import annotations
import math
from typing import Iterable

LAMBDAS = (0.05, 0.1, 0.2, 0.4, 0.8)


def _logmeanexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(x - maximum) for x in values) / len(values))


def trajectory(gains: Iterable[float], lambdas=LAMBDAS) -> list[float]:
    """Return log e-values after each observation (log for stability)."""
    lambdas = tuple(lambdas)
    if not lambdas or any(not math.isfinite(l) or not 0 <= l < 1 for l in lambdas):
        raise ValueError('lambdas must be finite in [0,1)')
    logs = [0.0] * len(lambdas)
    out = []
    for gain in gains:
        if isinstance(gain, bool) or not isinstance(gain, (int, float)) or not math.isfinite(gain) or not -1 <= gain <= 1:
            raise ValueError('gains must be finite numbers in [-1,1]')
        for j, l in enumerate(lambdas):
            logs[j] += math.log1p(l * gain)
        out.append(_logmeanexp(logs))
    return out


def first_crossing(gains: Iterable[float], alpha=0.05, lambdas=LAMBDAS):
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be in (0,1)')
    threshold = -math.log(alpha)
    for index, log_e in enumerate(trajectory(gains, lambdas), 1):
        if log_e >= threshold:
            return index
    return None


def naive_first_crossing(gains: Iterable[float], alpha=0.05, min_n=20, step=5):
    """One-sided normal approximation assuming unit null variance.

    Deliberately invalid under repeated unadjusted peeking. Suitable for
    Rademacher ±1 synthetic experiment, NOT generic paired outcomes.
    """
    if not 0 < alpha < 1 or min_n < 1 or step < 1:
        raise ValueError('invalid testing options')
    total = 0.0
    for n, x in enumerate(gains, 1):
        total += x
        if n >= min_n and (n - min_n) % step == 0:
            p = math.erfc(total / math.sqrt(n * 2)) / 2
            if p <= alpha:
                return n
    return None
