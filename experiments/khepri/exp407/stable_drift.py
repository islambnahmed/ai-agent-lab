"""Stable expanding-window geometric-drift forecast; no third-party dependencies.

Research prototype only; no production changes.
"""
import math


class ForecastRangeError(ValueError):
    """The mathematically valid forecast cannot be represented as positive finite float."""


def predict_drift_stable(train, horizon):
    """Forecast using endpoint telescoping in log space.

    sum(log(p[i+1]/p[i])) = log(last/first).
    """
    if len(train) < 2 or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("At least two prices and a positive integer horizon required")
    if any(not math.isfinite(p) or p <= 0 for p in train):
        raise ValueError("Training prices must be positive and finite")
    first, last = train[0], train[-1]
    ratio = last / first
    if 0.5 <= ratio <= 2.0:
        log_change = math.log1p((last - first) / first)
    else:
        log_change = math.log(last) - math.log(first)
    log_forecast = math.log(last) + (horizon / (len(train) - 1)) * log_change
    try:
        forecast = math.exp(log_forecast)
    except OverflowError as exc:
        raise ForecastRangeError("Forecast exceeds floating-point range") from exc
    if not math.isfinite(forecast) or forecast <= 0:
        raise ForecastRangeError("Forecast underflows positive floating-point range")
    return forecast


def stable_rmse(errors):
    """RMSE without squaring unscaled large finite errors."""
    values = list(errors)
    if not values:
        raise ValueError("At least one residual required")
    if any(not math.isfinite(e) for e in values):
        raise ValueError("Residuals must be finite")
    scale = max(map(abs, values))
    if scale == 0:
        return 0.0
    return scale * math.sqrt(math.fsum((e / scale) ** 2 for e in values) / len(values))
