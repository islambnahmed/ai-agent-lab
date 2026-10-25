"""Leakage-resistant, expanding-window backtest for a single price series.

CSV columns: date,close (ISO date, positive finite close). Standard library only.
Usage: python tools/gold_walkforward.py prices.csv --horizon 7 --train-min 120
This is evaluation infrastructure, not a trading recommendation.
"""
import argparse
import csv
import datetime as dt
import json
import math
import statistics
from pathlib import Path


def validate_rows(rows):
    """Enforce the same chronological/finite contract for CSV and direct callers."""
    if len(rows) < 3:
        raise ValueError("Need at least 3 price rows")
    previous = None
    for day, price in rows:
        if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
            raise ValueError("Dates must be date objects")
        if not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
            raise ValueError("Prices must be positive and finite")
        if previous is not None and day <= previous:
            raise ValueError("Need strictly increasing unique dates")
        previous = day
    return rows


def load_prices(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            day = dt.date.fromisoformat(row["date"])
            price = float(row["close"])
            rows.append((day, price))
    return validate_rows(rows)


def predict_drift(train, horizon):
    """Fit mean one-step log-return ONLY on observed training prices."""
    if len(train) < 2:
        raise ValueError("Insufficient training prices")
    if horizon < 1 or any(not math.isfinite(p) or p <= 0 for p in train):
        raise ValueError("Horizon and training prices must be positive and finite")
    # Endpoint log differences lose tiny but representable changes at large
    # price scales (e.g. adjacent floats around 1e300). Use log1p near unity,
    # and endpoint logs when a ratio/difference could overflow or underflow.
    first, last = train[0], train[-1]
    if first == last:
        return last
    relative_change = (last - first) / first
    if math.isfinite(relative_change) and abs(relative_change) <= 0.5:
        total_log_return = math.log1p(relative_change)
    else:
        total_log_return = math.log(last) - math.log(first)
    log_growth = horizon * total_log_return / (len(train) - 1)
    try:
        # Multiply near unity to preserve the significant bits of last.
        # For large growth use log space: exp(growth) alone may overflow even
        # when the final forecast (starting from a tiny price) is finite.
        forecast = (last * math.exp(log_growth) if abs(log_growth) <= 1
                    else math.exp(math.log(last) + log_growth))
    except OverflowError as exc:
        raise ValueError("Drift forecast is outside the finite positive range") from exc
    if not math.isfinite(forecast) or forecast <= 0:
        raise ValueError("Drift forecast is outside the finite positive range")
    return forecast


def backtest(rows, horizon=7, train_min=120, stride=None):
    if horizon < 1 or train_min < 2:
        raise ValueError("Invalid horizon or train_min")
    if stride is None:
        stride = horizon  # non-overlapping target intervals, not independent predictions
    if stride < horizon:
        raise ValueError("stride must be >= horizon for non-overlapping target windows")
    validate_rows(rows)
    prices = [p for _, p in rows]
    results = []
    for origin in range(train_min - 1, len(rows) - horizon, stride):
        train = prices[:origin + 1]
        actual = prices[origin + horizon]
        candidate = predict_drift(train, horizon)
        results.append({
            "origin_date": rows[origin][0].isoformat(),
            "target_date": rows[origin + horizon][0].isoformat(),
            "baseline": train[-1],
            "candidate": candidate,
            "actual": actual,
            "baseline_abs_error": abs(train[-1] - actual),
            "candidate_abs_error": abs(candidate - actual),
            "baseline_direction_correct": False,  # flat forecast has no direction
            "candidate_direction_correct": (
                (candidate > train[-1] and actual > train[-1])
                or (candidate < train[-1] and actual < train[-1])
            ),
        })
    if not results:
        return {"status": "insufficient_holdout", "independent_windows": 0, "results": []}
    base = statistics.mean(x["baseline_abs_error"] for x in results)
    cand = statistics.mean(x["candidate_abs_error"] for x in results)
    errors = [x["candidate_abs_error"] for x in results]
    max_error = max(errors)
    # Scale before squaring: raw squares can overflow or underflow for finite errors.
    rmse = (max_error * math.sqrt(statistics.mean((e / max_error) ** 2 for e in errors))
            if max_error else 0.0)
    improvement = (base - cand) / base * 100 if base else None
    if improvement is not None and not math.isfinite(improvement):
        improvement = None  # unrepresentable percentage; never emit JSON Infinity
    return {
        "status": "descriptive_only" if len(results) < 20 else "evaluation_ready",
        "horizon_sessions": horizon,
        "independent_windows": len(results),
        "baseline_mae": base,
        "candidate_mae": cand,
        "mae_improvement_pct": improvement,
        "candidate_rmse": rmse,
        "candidate_direction_accuracy": statistics.mean(x["candidate_direction_correct"] for x in results),
        "warning": "Non-overlapping target windows are not statistically independent. Model choice must not be tuned on these test windows; validate on a later untouched period.",
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--train-min", type=int, default=120)
    parser.add_argument("--stride", type=int)
    args = parser.parse_args()
    print(json.dumps(backtest(load_prices(args.csv_path), args.horizon, args.train_min, args.stride), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
