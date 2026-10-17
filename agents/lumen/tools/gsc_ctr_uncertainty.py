#!/usr/bin/env python3
"""Offline CTR-change uncertainty screen; never infer causality from GSC aggregates."""
import argparse
import json
import math

Z_95 = 1.959963984540054
# Keep counters exactly representable as IEEE-754 integers and avoid overflow.
MAX_COUNT = (1 << 53) - 1


def wilson_interval(clicks, impressions):
    if type(clicks) is not int or type(impressions) is not int:
        raise ValueError("counts must be integers")
    if impressions > MAX_COUNT or clicks > MAX_COUNT:
        raise ValueError("counts exceed maximum supported value")
    if impressions < 1 or clicks < 0 or clicks > impressions:
        raise ValueError("require 0 <= clicks <= impressions and impressions >= 1")
    p = clicks / impressions
    z2 = Z_95 * Z_95
    den = 1 + z2 / impressions
    center = (p + z2 / (2 * impressions)) / den
    half = Z_95 * math.sqrt(p * (1 - p) / impressions + z2 / (4 * impressions * impressions)) / den
    return max(0.0, min(p, center - half)), min(1.0, max(p, center + half))


def ctr_change_screen(clicks_a, impressions_a, clicks_b, impressions_b):
    la, ua = wilson_interval(clicks_a, impressions_a)
    lb, ub = wilson_interval(clicks_b, impressions_b)
    low, high = (la - ub) * 100, (ua - lb) * 100
    return {
        "observed_ctr_drop_pp": round(100 * (clicks_a / impressions_a - clicks_b / impressions_b), 3),
        "conservative_difference_band_pp": [round(low, 3), round(high, 3)],
        "zero_inside_band": low <= 0 <= high,
        "screen": "uncertain_direction" if low <= 0 <= high else
                  ("positive_drop_screen" if low > 0 else "negative_drop_screen"),
        "assumptions": "Marginal Wilson binomial approximation; not validated for GSC dependence or export completeness.",
        "action": "Never infer causality or make automated SEO changes from this screen.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ("clicks_a", "impressions_a", "clicks_b", "impressions_b"):
        parser.add_argument(label, type=int)
    args = parser.parse_args()
    try:
        result = ctr_change_screen(**vars(args))
    except ValueError as exc:
        parser.exit(2, f"Invalid counts: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
