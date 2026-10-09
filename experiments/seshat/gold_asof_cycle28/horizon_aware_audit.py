"""Audit endpoint-drift forecast horizon for the Seshat gold monthly benchmark.

No historical publication dates are verified: all publication timestamps in the
upstream dataset are explicit scenarios. This code does not modify the Oct 2026
nowcast or claim genuine out-of-sample forecasting skill.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from math import exp, isfinite, log
from statistics import mean

from point_in_time import information_set, load_observations


def month_gap(earlier: date, later: date) -> int:
    if earlier.day != 1 or later.day != 1:
        raise ValueError('Expected first-of-month dates')
    gap = (later.year - earlier.year) * 12 + later.month - earlier.month
    if gap < 1:
        raise ValueError('Target must follow latest observation')
    return gap


def endpoint_drift_horizon(prices: list[float], horizon: int) -> float:
    if len(prices) < 2 or not all(isfinite(x) and x > 0 for x in prices):
        raise ValueError('Need at least two finite positive prices')
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError('Horizon must be a positive integer')
    return prices[-1] * exp(horizon * log(prices[-1] / prices[0]) / (len(prices) - 1))


def evaluate(observations, issue_day: int) -> dict:
    if issue_day not in range(1, 29):
        raise ValueError('Invalid issue day')
    rows = []
    for target in observations[12:]:
        issued_at = datetime(target.month.year, target.month.month, issue_day, tzinfo=timezone.utc)
        available = information_set(observations, issued_at)
        # Explicitly prevent accidentally using the target or future months.
        available = [o for o in available if o.month < target.month]
        if len(available) < 2:
            raise ValueError('Insufficient historical information')
        prices = [o.price for o in available]
        h = month_gap(available[-1].month, target.month)
        original_one_step = endpoint_drift_horizon(prices, 1)
        corrected = endpoint_drift_horizon(prices, h)
        baseline = prices[-1]
        rows.append({
            'target_month': target.month.isoformat()[:7],
            'latest_known_month': available[-1].month.isoformat()[:7],
            'horizon_months': h,
            'actual': target.price,
            'baseline_error': abs(target.price - baseline),
            'one_step_error': abs(target.price - original_one_step),
            'horizon_corrected_error': abs(target.price - corrected),
        })
    summary = {
        'n': len(rows),
        'issue_day': issue_day,
        'horizons': sorted(set(r['horizon_months'] for r in rows)),
        'baseline_mae': round(mean(r['baseline_error'] for r in rows), 3),
        'one_step_mae': round(mean(r['one_step_error'] for r in rows), 3),
        'horizon_corrected_mae': round(mean(r['horizon_corrected_error'] for r in rows), 3),
        'corrected_minus_baseline_mae': round(mean(r['horizon_corrected_error'] - r['baseline_error'] for r in rows), 3),
        'corrected_minus_one_step_mae': round(mean(r['horizon_corrected_error'] - r['one_step_error'] for r in rows), 3),
        'rows': rows,
        'caveat': 'Historical release dates are assumed; 26 rounded monthly values, only 14 targets; exploratory, not investment guidance.',
    }
    return summary


def scenarios():
    return {
        'day3_release_day2': evaluate(load_observations(), 3),
        'day1_release_day2': evaluate(load_observations(), 1),
        'day3_one_extra_month_lag': evaluate(load_observations(delay_months=1), 3),
    }


if __name__ == '__main__':
    import json
    print(json.dumps(scenarios(), indent=2))
