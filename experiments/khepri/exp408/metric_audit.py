"""Research-only scale-safe forecast evaluation primitives (no production changes)."""
import math


def direction_correct(baseline, candidate, actual):
    """Strict direction agreement, without multiplying floating-point differences."""
    if not all(math.isfinite(v) for v in (baseline, candidate, actual)):
        raise ValueError('direction values must be finite')
    return ((candidate > baseline and actual > baseline)
            or (candidate < baseline and actual < baseline))


def stable_mae(residuals):
    """Mean absolute error, avoiding overflow of an intermediate sum."""
    values = list(residuals)
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError('nonempty finite residuals required')
    scale = max(map(abs, values))
    return 0.0 if scale == 0 else scale * (math.fsum(abs(v) / scale for v in values) / len(values))


def stable_rmse(residuals):
    """Root mean square error, avoiding intermediate square under/overflow."""
    values = list(residuals)
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError('nonempty finite residuals required')
    scale = max(map(abs, values))
    return 0.0 if scale == 0 else scale * math.sqrt(math.fsum((v / scale) ** 2 for v in values) / len(values))


def summarize(records):
    """Each record is (baseline, candidate, actual), all positive finite.

    Pure evaluation prototype. Explicitly declines non-representable residuals.
    """
    records = list(records)
    if not records:
        raise ValueError('at least one record required')
    if any(len(r) != 3 or any(not math.isfinite(v) or v <= 0 for v in r) for r in records):
        raise ValueError('positive finite baseline, candidate, actual required')
    b_errors = [b - a for b, c, a in records]
    c_errors = [c - a for b, c, a in records]
    if any(not math.isfinite(v) for v in b_errors + c_errors):
        raise ValueError('residual outside finite float range')
    base = stable_mae(b_errors)
    cand = stable_mae(c_errors)
    improvement = None
    if base > 0:
        ratio = cand / base
        if math.isfinite(ratio) and math.isfinite((1.0 - ratio) * 100.0):
            improvement = (1.0 - ratio) * 100.0
    return {
        'n': len(records),
        'baseline_mae': base,
        'candidate_mae': cand,
        'candidate_rmse': stable_rmse(c_errors),
        'candidate_direction_accuracy': sum(direction_correct(*r) for r in records) / len(records),
        'mae_improvement_pct': improvement,
    }
