"""Synthetic falsification test: overlap inflates naive one-sided significance.

No gold/provider data are used. This is a zero-drift Gaussian log-price walk;
a constant positive log-price forecast shift cannot improve expected absolute
log error over the last-close baseline. The experiment is NOT a p-value for
Gold Lab models, and disjoint targets are not guaranteed independent in markets.
"""
from __future__ import annotations
import argparse
import json
import math
import random
from statistics import NormalDist


def t_critical_one_sided_95(df: int) -> float:
    """Cornish-Fisher approximation to Student-t 95th percentile, df >= 10."""
    if df < 10:
        raise ValueError('Need >= 11 independent windows for this approximation')
    z = NormalDist().inv_cdf(.95)
    return (z + (z**3 + z) / (4 * df)
            + (5*z**5 + 16*z**3 + 3*z) / (96*df**2)
            + (3*z**7 + 19*z**5 + 17*z**3 - 15*z) / (384*df**3))


def wins_one_sided(loss_advantage: list[float]) -> bool:
    """One-sided paired t test, deliberately valid only under independence."""
    n = len(loss_advantage)
    if n < 11:
        raise ValueError('Too few observations')
    mean = sum(loss_advantage)/n
    variance = sum((v-mean)**2 for v in loss_advantage)/(n-1)
    return variance > 0 and mean/math.sqrt(variance/n) > t_critical_one_sided_95(n-1)


def trial(rng: random.Random, n: int, h: int, daily_vol: float, shift: float):
    # h-step target return is known only after h increments; adjacent targets overlap.
    increments = [rng.gauss(0, daily_vol) for _ in range(n+h-1)]
    rolling = sum(increments[:h])
    diff = []
    for origin in range(n):
        if origin:
            rolling += increments[origin+h-1] - increments[origin-1]
        # Positive advantage means candidate beats last-close on absolute log error.
        diff.append(abs(rolling) - abs(rolling-shift))
    return wins_one_sided(diff), wins_one_sided(diff[::h])


def simulate(seed=20261015, paths=1500, origins=500, horizons=(1,7,30),
             daily_vol=.01, shift=.0001):
    if paths < 1 or origins < 11*max(horizons) or daily_vol <= 0 or shift <= 0:
        raise ValueError('Invalid simulation parameters')
    rng = random.Random(seed)
    rows=[]
    for h in horizons:
        overlapping=disjoint=0
        for _ in range(paths):
            naive, sparse=trial(rng,origins,h,daily_vol,shift)
            overlapping+=naive
            disjoint+=sparse
        rows.append({'horizon':h,'nominal_overlapping_origins':origins,
                     'phase_zero_disjoint_windows':len(range(0,origins,h)),
                     'naive_positive_discoveries':overlapping,
                     'phase_zero_positive_discoveries':disjoint,
                     'naive_positive_rate':overlapping/paths,
                     'phase_zero_positive_rate':disjoint/paths})
    return {'kind':'synthetic_zero_drift_null','seed':seed,'paths':paths,
            'daily_log_return_sd':daily_vol,'fixed_upward_log_shift':shift,
            'nominal_one_sided_alpha':.05,'rows':rows,
            'limitations':['Not empirical gold outcomes or proof of independence',
                           'Fixed positive forecast has no true absolute-error edge under symmetric zero-drift increments',
                           'Phase-zero disjoint windows only remove overlapping return increments in this synthetic null',
                           'Cornish-Fisher t quantile is approximate; small-sample rates fluctuate']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--paths',type=int,default=1500)
    parser.add_argument('--origins',type=int,default=500)
    parser.add_argument('--seed',type=int,default=20261015)
    args=parser.parse_args()
    print(json.dumps(simulate(seed=args.seed,paths=args.paths,origins=args.origins),indent=2))


if __name__=='__main__':
    main()
