#!/usr/bin/env python3
"""Prequential 80% absolute-error intervals under synthetic volatility shifts.

No market data; the forecast is the zero-error persistence comparator. Each band
uses only errors observed strictly before the scored outcome. Python stdlib only.
"""
import argparse
import json
import math
import random
import statistics

CAL = 300
EVAL = 200
WINDOW = 100
ALPHA = 0.10
COVERAGE = 0.80


def quantile(scores, target=COVERAGE):
    if not scores:
        raise ValueError('no calibration scores')
    if not all(math.isfinite(x) and x >= 0 for x in scores):
        raise ValueError('scores must be finite and nonnegative')
    s = sorted(scores)
    # Finite-order empirical upper quantile; no distribution-free guarantee
    # for dependent or non-exchangeable sequences.
    k = min(len(s), max(1, math.ceil((len(s) + 1) * target)))
    return s[k - 1]


def forecast_bands(cal_errors, eval_errors, window=WINDOW, alpha=ALPHA):
    """Yield (fixed, rolling, EWMA-standardized) band before each eval error.

    Evaluated errors are revealed only *after* their corresponding bands are
    computed; no future residual enters any calibration/scale estimate.
    """
    if len(cal_errors) < window:
        raise ValueError('insufficient calibration history')
    if not 0 < alpha < 1:
        raise ValueError('invalid EWMA smoothing')
    fixed = quantile([abs(x) for x in cal_errors])
    abs_history = []
    scaled_history = []
    scale2 = sum(x*x for x in cal_errors[:window]) / window
    scale2 = max(scale2, 1e-12)
    for x in cal_errors:
        scale = math.sqrt(scale2)
        abs_history.append(abs(x))
        scaled_history.append(abs(x) / scale)
        scale2 = (1-alpha)*scale2 + alpha*x*x
    for error in eval_errors:
        rolling = quantile(abs_history[-window:])
        scaled = quantile(scaled_history[-window:]) * math.sqrt(scale2)
        yield (fixed, rolling, scaled)
        # Causal update, strictly after this target's score.
        scale = math.sqrt(scale2)
        abs_history.append(abs(error))
        scaled_history.append(abs(error) / scale)
        scale2 = (1-alpha)*scale2 + alpha*error*error


def one_trial(seed, post_sigma):
    rng = random.Random(seed)
    cal = [rng.gauss(0, 1.0) for _ in range(CAL)]
    future = [rng.gauss(0, post_sigma) for _ in range(EVAL)]
    bands = list(forecast_bands(cal, future))
    out = {}
    for j, name in enumerate(('fixed', 'rolling100', 'ewma100')):
        out[name] = {}
        for label, span in (('early20', range(20)), ('late100', range(100, EVAL)), ('all200', range(EVAL))):
            hits = [abs(future[i]) <= bands[i][j] for i in span]
            widths = [2*bands[i][j] for i in span]
            out[name][label] = (sum(hits)/len(hits), sum(widths)/len(widths))
    return out


def aggregate(trials=400):
    result = {'experiment': 'cycle185_volatility_shift', 'synthetic_only': True,
              'trials_per_scenario': trials, 'calibration_points': CAL,
              'evaluation_points': EVAL, 'target_coverage': COVERAGE,
              'window': WINDOW, 'ewma_alpha': ALPHA, 'scenarios': {}}
    for s_idx, (scenario, post_sigma) in enumerate((('stationary', 1.0), ('volatility_triples', 3.0), ('volatility_thirds', 1/3))):
        trials_data = [one_trial(185000 + s_idx*100000 + i, post_sigma) for i in range(trials)]
        summary = {}
        for method in ('fixed', 'rolling100', 'ewma100'):
            summary[method] = {}
            for period in ('early20', 'late100', 'all200'):
                cover = [row[method][period][0] for row in trials_data]
                width = [row[method][period][1] for row in trials_data]
                avg = statistics.mean(cover)
                se = statistics.stdev(cover)/math.sqrt(trials) if trials > 1 else 0
                summary[method][period] = {
                    'coverage': round(avg, 4),
                    'coverage_ci95_across_trials': [round(avg-1.96*se, 4), round(avg+1.96*se, 4)],
                    'mean_full_width': round(statistics.mean(width), 4)
                }
        result['scenarios'][scenario] = {'post_sigma': post_sigma, 'methods': summary}
    return result


def self_test():
    assert quantile([1,2,3,4]) == 4  # ceil((4+1)*.8)=4
    assert quantile([1,2,3,4,5]) == 5
    assert quantile([0]*30) == 0
    try:
        quantile([1, float('nan')])
        raise AssertionError('nan accepted')
    except ValueError:
        pass
    cal = [1.0, -2.0, 3.0]*40
    fut = [0.5]*10
    bands = list(forecast_bands(cal, fut))
    tampered = fut[:5] + [1e9]*5
    altered = list(forecast_bands(cal, tampered))
    assert bands[:6] == altered[:6], 'future target leaked into its own or prior band'
    assert len(bands) == 10
    assert all(all(math.isfinite(v) and v >= 0 for v in b) for b in bands)
    assert one_trial(42, 3) == one_trial(42, 3)
    print('SELF_TESTS_PASSED=7')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=400)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        if args.trials < 2:
            parser.error('--trials must be >= 2')
        print(json.dumps(aggregate(args.trials), indent=2))
