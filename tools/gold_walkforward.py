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


def load_prices(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            day = dt.date.fromisoformat(row["date"])
            price = float(row["close"])
            if not math.isfinite(price) or price <= 0:
                raise ValueError("Prices must be positive and finite")
            rows.append((day, price))
    if len(rows) < 3 or any(a[0] >= b[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("Need strictly increasing unique dates and at least 3 rows")
    return rows


def predict_drift(train, horizon):
    """Fit mean one-step log-return ONLY on observed training prices."""
    if len(train) < 2:
        raise ValueError("Insufficient training prices")
    returns = [math.log(b / a) for a, b in zip(train, train[1:])]
    return train[-1] * math.exp(horizon * statistics.mean(returns))


def backtest(rows, horizon=7, train_min=120, stride=None):
    if horizon < 1 or train_min < 2:
        raise ValueError("Invalid horizon or train_min")
    if stride is None:
        stride = horizon  # disjoint target intervals, avoids overlap inflation
    if stride < horizon:
        raise ValueError("stride must be >= horizon for independent target windows")
    prices = [p for _, p in rows]
    results = []
    for origin in range(train_min - 1, len(rows) - horizon, stride):
        train = prices[:origin + 1]
        actual = prices[origin + horizon]
        results.append({
            "origin_date": rows[origin][0].isoformat(),
            "target_date": rows[origin + horizon][0].isoformat(),
            "baseline": train[-1],
            "candidate": predict_drift(train, horizon),
            "actual": actual,
            "baseline_abs_error": abs(train[-1] - actual),
            "candidate_abs_error": abs(predict_drift(train, horizon) - actual),
            "baseline_direction_correct": False,  # flat forecast has no direction
            "candidate_direction_correct": (predict_drift(train, horizon) - train[-1]) * (actual - train[-1]) > 0,
        })
    if not results:
        return {"status": "insufficient_holdout", "independent_windows": 0, "results": []}
    base = statistics.mean(x["baseline_abs_error"] for x in results)
    cand = statistics.mean(x["candidate_abs_error"] for x in results)
    return {
        "status": "descriptive_only" if len(results) < 20 else "evaluation_ready",
        "horizon_sessions": horizon,
        "independent_windows": len(results),
        "baseline_mae": base,
        "candidate_mae": cand,
        "mae_improvement_pct": (base - cand) / base * 100 if base else None,
        "candidate_rmse": math.sqrt(statistics.mean((x["candidate"] - x["actual"]) ** 2 for x in results)),
        "candidate_direction_accuracy": statistics.mean(x["candidate_direction_correct"] for x in results),
        "warning": "Model choice must not be tuned on these test windows; validate on a later untouched period.",
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--train-min", type=int, default=120)
    parser.add_argument("--stride", type=int)
    args = parser.parse_args()
    print(json.dumps(backtest(load_prices(args.csv_path), args.horizon, args.train_min, args.stride), indent=2))


if __name__ == "__main__":
    main()
