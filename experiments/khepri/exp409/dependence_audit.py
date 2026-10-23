"""Research-only audit for dependence between nonoverlapping forecast evaluation windows.

No significance claim is made: HAC normal critical values are diagnostics, not
calibrated finite-sample hypothesis tests. Standard library only.
"""
import math
import statistics


def _finite(values):
    x = list(values)
    if len(x) < 3 or any(not math.isfinite(v) for v in x):
        raise ValueError('at least three finite deltas required')
    return x


def autocorrelation(values, lag=1):
    """Global-mean-centered sample autocorrelation at the requested lag."""
    x = _finite(values)
    if not isinstance(lag, int) or not 1 <= lag < len(x):
        raise ValueError('lag must be an integer in [1,n)')
    mu = statistics.mean(x)
    centered = [v - mu for v in x]
    den = sum(v * v for v in centered)
    if den == 0:
        return None
    return sum(a * b for a, b in zip(centered, centered[lag:])) / den


def lag1_correlation(values):
    return autocorrelation(values, 1)


def ar1_effective_n(n, rho):
    """AR(1) asymptotic ESS diagnostic, capped at n for conservative negatives."""
    if n < 3 or not math.isfinite(rho) or not -1 < rho < 1:
        raise ValueError('n>=3 and -1<rho<1 required')
    return max(1.0, min(float(n), n * (1.0 - rho) / (1.0 + rho)))


def exact_ar1_variance_inflation(n, phi):
    """Finite-n variance inflation for mean of unit-variance stationary AR(1)."""
    if n < 3 or not math.isfinite(phi) or not -1 < phi < 1:
        raise ValueError('invalid AR1 parameters')
    return 1.0 + 2.0 * sum((1.0 - k / n) * phi**k for k in range(1, n))


def audit_deltas(values, hac_lags=None):
    """Paired per-window MAE improvements: baseline_abs_error - candidate_abs_error."""
    x = _finite(values)
    n = len(x)
    mean = statistics.mean(x)
    c = [v - mean for v in x]
    gamma0 = sum(v * v for v in c) / n
    acf = {k: autocorrelation(x,k) for k in range(1, min(10,n-1)+1)}
    rho = acf[1]
    max_later = max((abs(v) for k,v in acf.items() if k >= 2 and v is not None), default=0.0)
    if hac_lags is None:
        hac_lags = min(10, max(1, n // 4))
    if not isinstance(hac_lags, int) or not 0 <= hac_lags < n:
        raise ValueError('HAC lag count must be in [0,n)')
    lrvar = gamma0
    for k in range(1, hac_lags + 1):
        gamma = sum(c[i] * c[i-k] for i in range(k, n)) / n
        lrvar += 2.0 * (1 - k / (hac_lags + 1)) * gamma
    # Bartlett long-run variance estimate is nonnegative in exact arithmetic.
    lrvar = max(0.0, lrvar)
    naive_se = math.sqrt(gamma0 / n)
    hac_se = math.sqrt(lrvar / n)
    return {
        'n': n,
        'mean_paired_improvement': mean,
        'lag1_autocorrelation': rho,
        'autocorrelation_lags_1_to_10': acf,
        'strong_higher_lag_structure_heuristic': max_later >= 0.5,
        'ar1_effective_n_diagnostic': ar1_effective_n(n, rho) if rho is not None and -1 < rho < 1 else None,
        'naive_se': naive_se,
        'hac_se': hac_se,
        'hac_lags': hac_lags,
        'naive_z_diagnostic': mean / naive_se if naive_se else None,
        'hac_z_diagnostic': mean / hac_se if hac_se else None,
        'warning': 'Disjoint targets do not guarantee independent errors; AR1 ESS fails for periodic/multi-lag structure; estimates are diagnostics, not validated p-values.',
    }


def audit_backtest(result):
    """Consume upstream tools.gold_walkforward.backtest result without modifying it."""
    if result.get('status') == 'insufficient_holdout':
        raise ValueError('insufficient holdout')
    records = result['results']
    return audit_deltas([r['baseline_abs_error'] - r['candidate_abs_error'] for r in records])
