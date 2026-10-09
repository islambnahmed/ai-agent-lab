"""O(number_of_bets) per-step anytime binary Markov e-process.

Algebraically equivalent to weighted restart mixture, with O(B+S) stored
state for B bets and S scheduled restarts. Intervals must be externally
calibrated; this code does NOT validate their statistical coverage.
"""
from bisect import bisect_right
from dataclasses import dataclass
from math import exp, fsum, isfinite, log, log1p
from sys import float_info

NEG_INF = float("-inf")
MAX_LOG = log(float_info.max)

@dataclass(frozen=True)
class Bet:
    row: int
    direction: str
    alternative: float
    weight: float

def logaddexp(a, b):
    if a == NEG_INF:
        return b
    if b == NEG_INF:
        return a
    m = max(a, b)
    return m + log1p(exp(min(a, b) - m))

class AggregatedLogTransitionMonitor:
    """Weighted restart e-process with one aggregate account per bet."""
    def __init__(self, intervals, bets, start_steps, horizon, alpha=0.04, initial_state=0):
        if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
            raise ValueError("horizon must be positive integer")
        if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or not isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("invalid alpha")
        if initial_state not in (0, 1) or isinstance(initial_state, bool):
            raise ValueError("invalid initial state")
        if len(intervals) != 2 or any(len(row) != 2 for row in intervals):
            raise ValueError("two binary row intervals required")
        self.intervals = tuple(tuple(float(x) for x in row) for row in intervals)
        if any(not (isfinite(lo) and isfinite(hi) and 0 <= lo <= hi <= 1) for lo, hi in self.intervals):
            raise ValueError("invalid intervals")
        self.bets = tuple(bets)
        if not self.bets:
            raise ValueError("at least one bet required")
        for b in self.bets:
            if (b.row not in (0, 1) or isinstance(b.row, bool)
                or b.direction not in ("up", "down")
                or not isfinite(b.alternative) or not 0 <= b.alternative <= 1
                or not isfinite(b.weight) or b.weight < 0):
                raise ValueError("invalid bet")
        total = fsum(b.weight for b in self.bets)
        if abs(total - 1) > 1e-10:
            raise ValueError("bet weights must sum to one")
        starts = tuple(start_steps)
        if (not starts or len(set(starts)) != len(starts)
            or any(not isinstance(s, int) or isinstance(s, bool) or s < 1 or s > horizon for s in starts)):
            raise ValueError("invalid restart schedule")
        self.starts = tuple(sorted(starts))
        self.start_set = set(starts)
        self.log_stakes = tuple(log(b.weight) - log(total) - log(len(starts)) if b.weight else NEG_INF for b in self.bets)
        self.log_active = [NEG_INF] * len(self.bets)
        self.log_threshold = -log(alpha)
        self.horizon = horizon
        self.last_state = initial_state
        self.t = 0
        self.log_e_value = 0.0
        self.first_alarm = None

    def step_log(self, previous, current):
        if (previous not in (0, 1) or current not in (0, 1)
            or isinstance(previous, bool) or isinstance(current, bool)):
            raise ValueError("transitions must be binary")
        if previous != self.last_state:
            raise ValueError("previous state does not match stream")
        if self.t >= self.horizon:
            raise ValueError("horizon exceeded")
        self.t += 1
        is_restart = self.t in self.start_set
        for i, b in enumerate(self.bets):
            lo, hi = self.intervals[b.row]
            boundary = hi if b.direction == "up" else lo
            q = max(boundary, b.alternative) if b.direction == "up" else min(boundary, b.alternative)
            if previous != b.row or q == boundary or boundary in (0, 1):
                factor = 0.0
            elif current == 1:
                factor = log(q) - log(boundary) if q > 0 else NEG_INF
            else:
                factor = log1p(-q) - log1p(-boundary) if q < 1 else NEG_INF
            if is_restart:
                self.log_active[i] = logaddexp(self.log_active[i], self.log_stakes[i])
            self.log_active[i] += factor
        future = len(self.starts) - bisect_right(self.starts, self.t)
        score = log(future / len(self.starts)) if future else NEG_INF
        for v in self.log_active:
            score = logaddexp(score, v)
        self.log_e_value = score
        self.last_state = current
        if self.first_alarm is None and score >= self.log_threshold:
            self.first_alarm = self.t
        return score, self.first_alarm is not None

    def step(self, previous, current):
        score, alarm = self.step_log(previous, current)
        return (exp(score) if score <= MAX_LOG else float("inf")), alarm
