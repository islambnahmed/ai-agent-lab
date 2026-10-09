"""Exploratory paired-loss audit for the gold benchmark.

Small-sample diagnostics are descriptive, not a claim of statistical significance.
The historical release schedule in point_in_time.py remains a scenario assumption.
"""
from __future__ import annotations

from itertools import product
from statistics import mean, median
from point_in_time import benchmark, load_observations


def paired_audit(rows: list[dict]) -> dict:
    """Positive loss difference means the candidate is worse than no-change."""
    if len(rows) < 3:
        raise ValueError("At least three paired months required")
    if len({r['target_month'] for r in rows}) != len(rows):
        raise ValueError("Duplicate target months")
    diffs = [float(r['candidate_error']) - float(r['baseline_error']) for r in rows]
    n = len(diffs)
    full = mean(diffs)
    loo = [(rows[i]['target_month'], mean(diffs[:i] + diffs[i + 1:])) for i in range(n)]
    # Exhaustive sign-flip reference (2**14 = 16,384 scenarios).
    # Serial dependence may invalidate exchangeability; this is sensitivity only.
    if n > 18:
        p = None
    else:
        abs_obs = abs(sum(diffs))
        extremes = 0
        for signs in product((-1, 1), repeat=n):
            if abs(sum(s * d for s, d in zip(signs, diffs))) >= abs_obs - 1e-10:
                extremes += 1
        p = extremes / (2 ** n)
    return {
        'n': n,
        'candidate_minus_baseline_mae_usd': round(full, 3),
        'candidate_minus_baseline_median_monthly_abs_error_usd': round(median(diffs), 3),
        'candidate_wins': sum(d < 0 for d in diffs),
        'candidate_losses': sum(d > 0 for d in diffs),
        'ties': sum(d == 0 for d in diffs),
        'leave_one_out_sign_flips': sum((v < 0) != (full < 0) for _, v in loo),
        'leave_one_out_range_usd': [round(min(v for _, v in loo), 3), round(max(v for _, v in loo), 3)],
        'most_influential_removed_month': max(loo, key=lambda kv: abs(kv[1] - full))[0],
        'first_half_mean_diff_usd': round(mean(diffs[:n // 2]), 3),
        'second_half_mean_diff_usd': round(mean(diffs[n // 2:]), 3),
        'exploratory_sign_flip_p_two_sided': round(p, 5) if p is not None else None,
        'caveat': 'Sign-flip reference is not a valid financial time-series p-value without exchangeability; historical release times are assumed.',
    }


def run_scenarios() -> dict:
    return {
        'issue_day_3_release_day_2': paired_audit(benchmark(load_observations(), 3)['predictions']),
        'issue_day_1_release_day_2': paired_audit(benchmark(load_observations(), 1)['predictions']),
        'issue_day_3_extra_month_delay': paired_audit(benchmark(load_observations(delay_months=1), 3)['predictions']),
    }


if __name__ == '__main__':
    import json
    print(json.dumps(run_scenarios(), indent=2, ensure_ascii=False))
