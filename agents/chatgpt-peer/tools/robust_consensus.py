"""Robust consensus from repeated numeric measurements.

Goal: estimate a stable center when a minority of measurements can be extreme.
No third-party dependencies.
"""
from __future__ import annotations
import math, statistics

def median_absolute_deviation(values):
    xs=[float(x) for x in values]
    if not xs: raise ValueError("values must not be empty")
    m=statistics.median(xs)
    return statistics.median(abs(x-m) for x in xs)

def run(values, z=3.5):
    xs=[float(x) for x in values]
    if len(xs)<3: raise ValueError("need at least 3 measurements")
    if not all(math.isfinite(x) for x in xs): raise ValueError("measurements must be finite")
    med=statistics.median(xs)
    mad=median_absolute_deviation(xs)
    if mad==0:
        kept=[x for x in xs if x==med]
        # If a strict majority agrees exactly, treat other values as outliers.
        if len(kept)<=len(xs)//2:
            kept=xs
    else:
        kept=[x for x in xs if abs(0.6744897501960817*(x-med)/mad)<=z]
    if not kept: kept=xs
    return {
        "estimate": statistics.median(kept),
        "median_raw": med,
        "mad": mad,
        "kept": kept,
        "rejected": [x for x in xs if x not in kept],
        "n": len(xs),
        "n_kept": len(kept),
    }
