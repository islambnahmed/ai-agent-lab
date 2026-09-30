"""Repeated-evaluation gate for noisy failure predicates."""
from __future__ import annotations

def run(case, trial, attempts=7, threshold=0.8):
    if attempts<1: raise ValueError("attempts must be positive")
    outcomes=[bool(trial(case)) for _ in range(attempts)]
    rate=sum(outcomes)/attempts
    return {"attempts":attempts,"failures":sum(outcomes),"failure_rate":rate,
            "reproduced":rate>=threshold,"outcomes":outcomes}
