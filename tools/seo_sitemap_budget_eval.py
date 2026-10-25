#!/usr/bin/env python3
"""Offline ranking-at-budget evaluation; never authenticates live SEO outcomes."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import random
import sys

MAX_BYTES = 8 * 1024 * 1024
QUEUE_COLUMNS = ('priority', 'change', 'url', 'review_action', 'evidence',
                 'rows_before', 'rows_after')
LABEL_COLUMNS = ('url', 'review_worthy', 'severity')
EVIDENCE = {'csv_only_unverified', 'local_csv_sha_checked'}
PRIORITIES = {'P1': 1, 'P2': 2, 'P3': 3}


def _csv_rows(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('missing or oversized input CSV')
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != list(columns):
            raise ValueError('unexpected CSV header')
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError('malformed CSV row')
    return rows


def _fraction(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _score(urls: list[str], labels: dict[str, tuple[str, str]], positives: int) -> dict:
    selected = [labels[url] for url in urls]
    tp = sum(worthy == 'yes' for worthy, _ in selected)
    fp = sum(worthy == 'no' for worthy, _ in selected)
    high_total = sum(worthy == 'yes' and severity == 'high'
                     for worthy, severity in labels.values())
    high_found = sum(worthy == 'yes' and severity == 'high'
                     for worthy, severity in selected)
    return {'true_positives': tp, 'false_positives': fp,
            'uncertain_reviewed': len(selected) - tp - fp,
            'recall_at_budget': _fraction(tp, positives),
            'precision_at_budget': _fraction(tp, tp + fp),
            'high_impact_misses': high_total - high_found}


def evaluate(queue: list[dict[str, str]], references: list[dict[str, str]],
             budget: int, seed: int = 0, trials: int = 100) -> dict:
    if type(budget) is not int or budget < 0 or type(seed) is not int:
        raise ValueError('budget and seed must be integers; budget >= 0')
    if type(trials) is not int or not 1 <= trials <= 1000:
        raise ValueError('trials must be between 1 and 1000')
    if not queue:
        raise ValueError('queue is empty; no changes to rank')
    seen: set[str] = set()
    evidence: set[str] = set()
    for row in queue:
        url = row['url']
        if (not url.startswith(('http://', 'https://')) or url in seen or
                row['priority'] not in PRIORITIES or row['change'] not in
                {'added', 'removed', 'changed'} or row['evidence'] not in EVIDENCE):
            raise ValueError('invalid or duplicate queue entry')
        seen.add(url)
        evidence.add(row['evidence'])
    if len(evidence) != 1:
        raise ValueError('mixed queue evidence levels')
    labels: dict[str, tuple[str, str]] = {}
    for row in references:
        url, worthy, severity = row['url'], row['review_worthy'], row['severity']
        if (url in labels or worthy not in {'yes', 'no', 'uncertain'} or
                severity not in {'high', 'normal'}):
            raise ValueError('invalid or duplicate independent reference label')
        labels[url] = (worthy, severity)
    if set(labels) != seen:
        raise ValueError('reference labels must cover exactly the queue URLs')
    if budget > len(queue):
        raise ValueError('budget exceeds queue size')
    positives = sum(worthy == 'yes' for worthy, _ in labels.values())
    uncertain = sum(worthy == 'uncertain' for worthy, _ in labels.values())
    ordered = sorted(queue, key=lambda row: (PRIORITIES[row['priority']], row['url']))
    prioritized = _score([row['url'] for row in ordered[:budget]], labels, positives)
    baseline = []
    for trial in range(trials):
        shuffled = sorted(seen)
        random.Random(seed + trial).shuffle(shuffled)
        baseline.append(_score(shuffled[:budget], labels, positives))
    recalls = [score['recall_at_budget'] for score in baseline]
    return {
        'evaluation': 'offline_priority_ordering_only_not_field_effectiveness',
        'evidence': next(iter(evidence)),
        'budget': budget, 'total_changed_urls': len(queue),
        'reference_positives': positives, 'uncertain_labels': uncertain,
        'priority_queue': prioritized,
        'no_priority_shuffle_baseline': {
            'trials': trials,
            'mean_true_positives': round(sum(s['true_positives'] for s in baseline) / trials, 6),
            'mean_recall_at_budget': (round(sum(recalls) / trials, 6)
                                      if positives else None),
            'min_true_positives': min(s['true_positives'] for s in baseline),
            'max_true_positives': max(s['true_positives'] for s in baseline),
        },
        'limitations': ('Complete queues trivially contain all changed URLs. '
                        'This measures ordering at a fixed inspection budget, '
                        'not human review speed, real-world SEO impact, or live-site truth.'),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--labels', type=Path, required=True)
    parser.add_argument('--budget', type=int, required=True)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        queue = _csv_rows(args.queue, QUEUE_COLUMNS)
        labels = _csv_rows(args.labels, LABEL_COLUMNS)
        result = evaluate(queue, labels, args.budget, seed=args.seed)
    except (OSError, UnicodeError, csv.Error):
        print('Cannot evaluate offline sitemap ranking: input read failed', file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f'Cannot evaluate offline sitemap ranking: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
