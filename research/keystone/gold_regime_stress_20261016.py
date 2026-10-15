"""Reproducible synthetic stress test for the AI Agent Lab gold walk-forward evaluator.

No historical market data or live predictions are used. Stdlib only.
Run from repository root: python research/keystone/gold_regime_stress_20261016.py
"""
import datetime as dt
import json
import math
import random
import statistics
from tools.gold_walkforward import backtest

SEED = 20261016
TRIALS = 300
LENGTH = 500
VOL = 0.012
HORIZON = 7
TRAIN_MIN = 120


def synthetic_prices(rng, regime):
    price = 2000.0
    day = dt.date(2024, 1, 1)
    rows = [(day, price)]
    for t in range(1, LENGTH):
        if regime == 'zero_drift':
            mu = 0.0
        elif regime == 'persistent_positive_drift':
            mu = 0.0015
        elif regime == 'trend_reversal':
            mu = 0.0015 if t < 250 else -0.0015
        else:
            raise ValueError(regime)
        price *= math.exp(rng.gauss(mu, VOL))
        rows.append((day + dt.timedelta(days=t), price))
    return rows


def bootstrap_mean_interval(vals, seed, reps=2000):
    rng = random.Random(seed)
    n = len(vals)
    means = [statistics.mean(vals[rng.randrange(n)] for _ in range(n)) for _ in range(reps)]
    means.sort()
    return [round(means[int(.025 * reps)], 4), round(means[int(.975 * reps)], 4)]


def run():
    rng = random.Random(SEED)
    results = {'method': 'synthetic seeded geometric random walks, not real gold prices',
               'seed': SEED, 'trials_per_regime': TRIALS, 'prices_per_trial': LENGTH,
               'log_return_daily_volatility': VOL, 'horizon_sessions': HORIZON,
               'train_min': TRAIN_MIN, 'regimes': {}}
    for index, regime in enumerate(('zero_drift', 'persistent_positive_drift', 'trend_reversal')):
        improvements = []
        win_count = 0
        windows = None
        for _ in range(TRIALS):
            rows = synthetic_prices(rng, regime)
            score = backtest(rows, horizon=HORIZON, train_min=TRAIN_MIN)
            windows = score['nonoverlapping_windows']
            pct = score['mae_improvement_pct']
            improvements.append(pct)
            win_count += pct > 0
        results['regimes'][regime] = {
            'mean_mae_improvement_pct': round(statistics.mean(improvements), 4),
            'median_mae_improvement_pct': round(statistics.median(improvements), 4),
            'mean_improvement_95pct_bootstrap_ci': bootstrap_mean_interval(improvements, SEED+index),
            'candidate_wins_of_300': win_count,
            'nonoverlapping_windows_per_trial': windows,
        }
    return results


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
