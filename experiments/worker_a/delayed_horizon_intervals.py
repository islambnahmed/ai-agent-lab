#!/usr/bin/env python3
"""Synthetic h=7/30 interval calibration with label maturity. No market data."""
import argparse
import json
import math
import random
import statistics
import unittest

def rank_quantile(values, level=0.8):
    if not values or not 0 < level < 1:
        raise ValueError('invalid calibration inputs')
    xs = sorted(abs(x) for x in values)
    return xs[min(len(xs), math.ceil((len(xs) + 1) * level)) - 1]

def eligible_residual_indices(issue_t, horizon):
    """A residual issued at i is usable only when i+h < issue_t."""
    if horizon < 1:
        raise ValueError('horizon must be positive')
    return range(max(0, issue_t - horizon))

def band_at(errors, issue_t, horizon, method, window=80, fixed_n=200):
    if issue_t <= fixed_n + horizon or window < 1:
        raise ValueError('insufficient historical calibration')
    if method == 'fixed':
        eligible = errors[:fixed_n]
    elif method == 'causal_rolling':
        stop = issue_t - horizon  # last eligible index: t-h-1
        eligible = errors[max(0, stop-window):stop]
    elif method == 'leaky_rolling':
        # Deliberately invalid comparator: sees labels not yet mature.
        eligible = errors[issue_t-window:issue_t]
    else:
        raise ValueError('unknown method')
    if len(eligible) < window and method != 'fixed':
        raise ValueError('insufficient rolling history')
    return rank_quantile(eligible)

def synthetic_errors(seed, horizon, rho=0, n=720, shift_at=400):
    """Overlapping h-day forecast errors; volatility triples in future shocks."""
    rng = random.Random(seed)
    shocks = []
    state = 0.0
    for j in range(n + horizon + 1):
        sigma = 1.0 if shift_at is None or j < shift_at else 3.0
        state = rho*state + math.sqrt(1-rho*rho)*rng.gauss(0, 1)
        shocks.append(sigma*state)
    return [sum(shocks[t+1:t+horizon+1])/math.sqrt(horizon) for t in range(n)]

def trial(seed, horizon, rho, shift_at):
    errors = synthetic_errors(seed, horizon, rho, shift_at=shift_at)
    phases = {'pre':(280,370),'early':(400,480),'late':(550,680)}
    output = {}
    for phase,(start,end) in phases.items():
        for method in ('fixed','causal_rolling','leaky_rolling'):
            widths = [band_at(errors,t,horizon,method) for t in range(start,end)]
            output[f'{phase}_{method}'] = (sum(abs(errors[t]) <= widths[t-start] for t in range(start,end))/(end-start),statistics.mean(widths))
    return output

def run(reps=100):
    if reps < 2:
        raise ValueError('reps must be >= 2')
    result = {'experiment':'synthetic delayed-label h=7/30 interval audit',
              'note':'NO real gold data; leaky_rolling is intentionally invalid',
              'reps':reps,'n':720,'shift_shock_index':400,
              'label_rule':'only residuals with issue_index+horizon < current_issue_index',
              'methods':['fixed','causal_rolling','leaky_rolling'], 'cases':{}}
    for h in (7,30):
        for rho in (0,0.6):
            for shifted in (False,True):
                runs = [trial(13000+i,h,rho,400 if shifted else None) for i in range(reps)]
                row = {}
                for key in runs[0]:
                    coverage = [r[key][0] for r in runs]
                    widths = [r[key][1] for r in runs]
                    row[key] = {'coverage':round(statistics.mean(coverage),4),
                                'mean_half_width':round(statistics.mean(widths),4),
                                'coverage_se':round(statistics.stdev(coverage)/math.sqrt(reps),4)}
                result['cases'][f'h{h}_rho{rho}_{"shift" if shifted else "stationary"}']=row
    return result

class TestMaturity(unittest.TestCase):
    def test_maturity_strict(self):
        self.assertEqual(list(eligible_residual_indices(100,7))[-1],92)
        self.assertEqual(list(eligible_residual_indices(100,30))[-1],69)
    def test_future_labels_do_not_change_causal_band(self):
        for h in (7,30):
            errors = [0.2]*720
            t=420
            old = band_at(errors,t,h,'causal_rolling')
            errors[t-h:t] = [999]*h
            self.assertEqual(old,band_at(errors,t,h,'causal_rolling'))
            if h == 30:  # 30/80 contaminated labels cross the 80th percentile
                self.assertNotEqual(old,band_at(errors,t,h,'leaky_rolling'))
    def test_mature_label_can_change_band(self):
        errors = [0.2]*720
        t=420; h=30
        errors[t-h-80:t-h] = [3]*80
        self.assertEqual(band_at(errors,t,h,'causal_rolling'),3)
    def test_determinism(self):
        self.assertEqual(trial(12,7,0.6,400),trial(12,7,0.6,400))
    def test_no_insufficient_history(self):
        with self.assertRaises(ValueError): band_at([0]*720,230,30,'causal_rolling')
    def test_no_bad_horizon(self):
        with self.assertRaises(ValueError): eligible_residual_indices(100,0)
    def test_non_leak_fixed_calibration(self):
        errors=[1]*720
        errors[200:]=[100]*520
        self.assertEqual(band_at(errors,400,30,'fixed'),1)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--reps',type=int,default=100)
    a=p.parse_args()
    if a.test: unittest.main(argv=['delayed_horizon_intervals.py'])
    else: print(json.dumps(run(a.reps),indent=2))
