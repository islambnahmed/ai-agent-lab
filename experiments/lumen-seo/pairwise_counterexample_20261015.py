#!/usr/bin/env python3
"""Lumen: aggregate SEO co-visibility can identify the wrong page pair.

Self-contained synthetic witness; Python stdlib only. No live GSC access.
"""
from collections import defaultdict
from datetime import date, timedelta
from itertools import combinations

A, B, C = ('https://example.test/' + p for p in 'abc')


def world(c_impressions):
    rows = {}
    for offset in range(3):
        day = date(2026, 9, 1) + timedelta(days=offset)
        rows[(day, A, 'usa', 'MOBILE')] = 100
        rows[(day, B, 'gbr', 'DESKTOP')] = 100
        rows[(day, C, 'usa', 'MOBILE')] = c_impressions
    return rows


def pair_evidence(rows, min_total=20, min_page=5, min_share=.10):
    daily = defaultdict(lambda: defaultdict(float))
    segmented = defaultdict(lambda: defaultdict(float))
    for (day, page, country, device), count in rows.items():
        daily[day][page] += count
        segmented[(day, country, device)][page] += count
    aggregate_pairs = set()
    shared_pairs = set()
    qualified_segmented_pairs = set()
    for day, pages in daily.items():
        total = sum(pages.values())
        if total >= min_total:
            eligible = sorted(p for p, n in pages.items()
                              if n >= min_page and n / total >= min_share)
            aggregate_pairs.update(combinations(eligible, 2))
    for key, pages in segmented.items():
        total = sum(pages.values())
        positive = sorted(p for p, n in pages.items() if n > 0)
        shared_pairs.update(combinations(positive, 2))
        if total >= min_total:
            eligible = sorted(p for p in positive
                              if pages[p] >= min_page and pages[p] / total >= min_share)
            qualified_segmented_pairs.update(combinations(eligible, 2))
    return aggregate_pairs, shared_pairs, qualified_segmented_pairs


def main():
    rich = world(20)
    agg, shared, qualified = pair_evidence(rich)
    assert (A, B) in agg and (A, B) not in shared
    assert (A, C) not in agg and (A, C) in qualified

    sparse = world(1)
    without_c = {key: n for key, n in sparse.items() if key[1] != C}
    agg_before, shared_before, _ = pair_evidence(sparse)
    agg_after, shared_after, _ = pair_evidence(without_c)
    assert agg_before == agg_after == {(A, B)}
    assert shared_before == {(A, C)} and shared_after == set()
    removed = sum(sparse.values()) - sum(without_c.values())
    assert removed == 3 and removed / sum(sparse.values()) < .01
    print('PASS: aggregate A/B pair never shares an observed stratum')
    print('PASS: segmented A/C pair can be absent from aggregate qualified pairs')
    print(f'PASS: deleting {removed}/{sum(sparse.values())} impressions '
          f'({removed / sum(sparse.values()):.3%}) erases all observed shared pairs')
    print('LIMIT: co-observation is not same-SERP placement or SEO harm')


if __name__ == '__main__':
    main()
