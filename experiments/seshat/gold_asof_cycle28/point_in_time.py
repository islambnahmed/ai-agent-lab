"""Publication-aware gold monthly benchmark. Historical release timestamps are assumptions."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from math import exp, log, sqrt
from statistics import mean

DATA = Path(__file__).with_name("gold_monthly_2024_08_to_2026_09.csv")

@dataclass(frozen=True)
class Observation:
    month: date
    price: float
    published_at: datetime

def next_month(d: date) -> date:
    return date(d.year + (d.month == 12), (d.month % 12) + 1, 1)

def load_observations(delay_months: int = 0, publication_day: int = 2) -> list[Observation]:
    """Assume M average published on day publication_day of M+1+delay_months."""
    if delay_months < 0 or publication_day not in range(1, 29):
        raise ValueError("Invalid publication scenario")
    rows = list(csv.DictReader(DATA.open(encoding="utf-8", newline="")))
    observations = []
    for row in rows:
        month = date.fromisoformat(row["date"])
        if month.day != 1:
            raise ValueError("Month must be first day")
        published = next_month(month)
        for _ in range(delay_months):
            published = next_month(published)
        published_at = datetime(published.year, published.month, publication_day, tzinfo=timezone.utc)
        observations.append(Observation(month, float(row["close"]), published_at))
    if len(observations) != 26 or any(next_month(a.month) != b.month for a, b in zip(observations, observations[1:])):
        raise ValueError("Expected 26 consecutive monthly observations")
    return observations

def information_set(observations: list[Observation], as_of: datetime) -> list[Observation]:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    eligible = [o for o in observations if o.published_at <= as_of]
    return sorted(eligible, key=lambda o: o.month)

def drift(prices: list[float]) -> float:
    if len(prices) < 2 or min(prices) <= 0:
        raise ValueError("Need two positive prices")
    return prices[-1] * exp(log(prices[-1] / prices[0]) / (len(prices) - 1))

def predict(observations: list[Observation], as_of: datetime) -> dict:
    available = information_set(observations, as_of)
    if len(available) < 2:
        raise ValueError("Insufficient history")
    prices = [x.price for x in available]
    return {"as_of": as_of.isoformat(), "latest_known_month": available[-1].month.isoformat(),
            "training_observations": len(available), "no_change": prices[-1], "endpoint_drift": drift(prices)}

def benchmark(observations: list[Observation], issue_day: int) -> dict:
    if issue_day not in range(1, 29):
        raise ValueError("Invalid issue day")
    outputs = []
    for target in observations[12:]:
        issue_at = datetime(target.month.year, target.month.month, issue_day, tzinfo=timezone.utc)
        known = [o for o in observations if o.month < target.month]
        p = predict(known, issue_at)
        outputs.append({"target_month": target.month.isoformat()[:7],
                        "latest_known_month": p["latest_known_month"][:7],
                        "actual": target.price, "baseline": p["no_change"],
                        "candidate": p["endpoint_drift"],
                        "baseline_error": abs(target.price - p["no_change"]),
                        "candidate_error": abs(target.price - p["endpoint_drift"])})
    b = [x["baseline_error"] for x in outputs]
    c = [x["candidate_error"] for x in outputs]
    return {"issue_day": issue_day, "evaluated_months": len(outputs),
            "baseline_mae": round(mean(b), 3), "candidate_mae": round(mean(c), 3),
            "candidate_relative_to_baseline_pct": round((mean(c) / mean(b) - 1) * 100, 3),
            "baseline_rmse": round(sqrt(mean(x*x for x in b)), 3),
            "candidate_rmse": round(sqrt(mean(x*x for x in c)), 3),
            "candidate_wins": sum(x["candidate_error"] < x["baseline_error"] for x in outputs),
            "predictions": outputs}

if __name__ == "__main__":
    for name, obs, day in [
        ("day3", load_observations(), 3),
        ("day1", load_observations(), 1),
        ("extra_lag", load_observations(delay_months=1), 3),
    ]:
        r = benchmark(obs, day)
        print(name, {k: r[k] for k in ["baseline_mae", "candidate_mae", "candidate_relative_to_baseline_pct", "candidate_wins"]})
