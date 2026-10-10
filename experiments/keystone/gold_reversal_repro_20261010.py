"""Frozen gold monthly trend audit; retrospective, not prospective."""
from math import exp, log
from statistics import mean

# 2025-03 to 2026-03: prior IndexMundi/World Bank extract.
# 2026-04..06: World Bank Pink Sheet 2026-07-02, page 2.
# 2026-07..09: World Bank Pink Sheet 2026-10-02, page 2.
prices = [
    2983.25, 3217.64, 3309.49, 3352.66, 3340.15, 3368.03,
    3667.68, 4058.33, 4087.19, 4309.23, 4752.75, 5019.97,
    4855.54, 4721, 4587, 4228, 4073, 4411, 4319,
]


def evaluate():
    """Hold fixed: embargo=2 months, lookback=12 observations."""
    results = []
    for target in range(13, 19):  # April-September 2026
        origin = target - 2
        base = prices[origin]
        trend = base * exp(2 * log(base / prices[origin - 11]) / 11)
        actual = prices[target]
        results.append((abs(actual - base), abs(actual - trend)))
    baseline = mean(x[0] for x in results)
    candidate = mean(x[1] for x in results)
    return baseline, candidate, 100 * (baseline - candidate) / baseline


if __name__ == "__main__":
    b, c, pct = evaluate()
    assert abs(b - 333.9183333333) < 1e-6
    assert abs(c - 523.1384948100) < 1e-6
    assert abs(pct - (-56.6665985625)) < 1e-6
    print(f"6-month baseline MAE={b:.2f}, trend MAE={c:.2f}, improvement={pct:.2f}%")
