#!/usr/bin/env python3
"""Aggregate blinded offline sitemap-review sessions; no live SEO claims."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys

MAX_BYTES = 8 * 1024 * 1024
REF_COLS = ['pair_id', 'url_id', 'review_worthy', 'severity']
SESSION_COLS = ['pair_id', 'reviewer_id', 'arm', 'active_seconds', 'inspection_budget']
DECISION_COLS = ['pair_id', 'reviewer_id', 'arm', 'url_id', 'inspected', 'flagged']
ARMS = ('manual', 'triage')


def read_csv(path: Path, header: list[str]) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('missing or oversized CSV input')
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != header:
            raise ValueError(f'expected columns {header}')
        rows = list(reader)
    if any(None in row or any(v is None or '\x00' in v for v in row.values()) for row in rows):
        raise ValueError('malformed CSV row')
    return rows


def positive_int(value: str, name: str) -> int:
    if not value.isascii() or not value.isdecimal() or int(value) < 1:
        raise ValueError(f'{name} must be a positive integer')
    return int(value)


def nonnegative_seconds(value: str) -> float:
    # Accept only fixed-point decimal, avoiding NaN, infinities and exponents.
    if not value or not value.isascii() or value.count('.') > 1 or not value.replace('.', '').isdecimal():
        raise ValueError('active_seconds must be a nonnegative decimal')
    result = float(value)
    if not 0 <= result <= 86400:
        raise ValueError('active_seconds must be between 0 and 86400')
    return result


def ratio(a: int | float, b: int | float) -> float | None:
    return round(a / b, 6) if b else None


def score(references: list[dict[str, str]], sessions: list[dict[str, str]],
          decisions: list[dict[str, str]]) -> dict:
    labels: dict[tuple[str, str], tuple[str, str]] = {}
    per_pair: dict[str, set[str]] = defaultdict(set)
    for row in references:
        pair, url = row['pair_id'], row['url_id']
        if (not pair or not url or (pair, url) in labels or
                row['review_worthy'] not in ('yes', 'no', 'uncertain') or
                row['severity'] not in ('high', 'normal')):
            raise ValueError('invalid or duplicate reference label')
        labels[pair, url] = (row['review_worthy'], row['severity'])
        per_pair[pair].add(url)
    if not labels:
        raise ValueError('no independent reference labels')

    active: dict[tuple[str, str, str], tuple[float, int]] = {}
    pairs_by_reviewer: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in sessions:
        pair, reviewer, arm = row['pair_id'], row['reviewer_id'], row['arm']
        key = (pair, reviewer, arm)
        if not reviewer or pair not in per_pair or arm not in ARMS or key in active:
            raise ValueError('invalid or duplicate review session')
        active[key] = (nonnegative_seconds(row['active_seconds']),
                       positive_int(row['inspection_budget'], 'inspection_budget'))
        pairs_by_reviewer[pair, reviewer].add(arm)
    if not active or any(arms != set(ARMS) for arms in pairs_by_reviewer.values()):
        raise ValueError('each pair/reviewer requires both review arms')
    for pair, reviewer in pairs_by_reviewer:
        if active[pair, reviewer, 'manual'][1] != active[pair, reviewer, 'triage'][1]:
            raise ValueError('paired arms must use equal inspection budgets')

    reviewed: dict[tuple[str, str, str], dict[str, bool]] = defaultdict(dict)
    flagged: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in decisions:
        pair, reviewer, arm, url = (row[k] for k in ('pair_id', 'reviewer_id', 'arm', 'url_id'))
        key = (pair, reviewer, arm)
        if (key not in active or (pair, url) not in labels or
                row['inspected'] not in ('yes', 'no') or row['flagged'] not in ('yes', 'no') or
                url in reviewed[key]):
            raise ValueError('invalid, unpaired, or duplicate review decision')
        inspected = row['inspected'] == 'yes'
        if row['flagged'] == 'yes' and not inspected:
            raise ValueError('cannot flag an uninspected URL')
        reviewed[key][url] = inspected
        if row['flagged'] == 'yes':
            flagged[key].add(url)

    aggregates = {arm: dict(sessions=0, active_seconds=0.0, inspected=0,
                            flagged=0, tp=0, fp=0, fn=0,
                            uncertain_flagged=0, high_impact_misses=0)
                  for arm in ARMS}
    for key, (seconds, budget) in active.items():
        pair, reviewer, arm = key
        inspected = sum(reviewed[key].values())
        if inspected > budget:
            raise ValueError('session exceeds preregistered inspection budget')
        flags = flagged[key]
        a = aggregates[arm]
        a['sessions'] += 1
        a['active_seconds'] += seconds
        a['inspected'] += inspected
        a['flagged'] += len(flags)
        for url in per_pair[pair]:
            worthy, severity = labels[pair, url]
            found = url in flags
            if worthy == 'yes':
                a['tp' if found else 'fn'] += 1
                if severity == 'high' and not found:
                    a['high_impact_misses'] += 1
            elif worthy == 'no' and found:
                a['fp'] += 1
            elif worthy == 'uncertain' and found:
                a['uncertain_flagged'] += 1

    for a in aggregates.values():
        a['active_seconds'] = round(a['active_seconds'], 3)
        a['recall'] = ratio(a['tp'], a['tp'] + a['fn'])
        a['precision'] = ratio(a['tp'], a['tp'] + a['fp'])
        a['seconds_per_true_finding'] = ratio(a['active_seconds'], a['tp'])
    return {
        'kind': 'offline_sitemap_review_session_aggregate',
        'paired_sessions': len(pairs_by_reviewer),
        'reference_pairs': len(per_pair),
        'arms': aggregates,
        'limitations': ('Aggregate review-session accounting only; inputs require independently '
                        'adjudicated complete reference sets and prospectively fixed budgets. '
                        'This does not validate sitemap capture, reviewer blinding, '
                        'counterbalancing, causality, or SEO outcomes.'),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references', required=True, type=Path)
    parser.add_argument('--sessions', required=True, type=Path)
    parser.add_argument('--decisions', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = score(read_csv(args.references, REF_COLS),
                       read_csv(args.sessions, SESSION_COLS),
                       read_csv(args.decisions, DECISION_COLS))
    except (ValueError, OSError, UnicodeError, csv.Error, OverflowError) as exc:
        print(f'Cannot score offline sitemap review: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
