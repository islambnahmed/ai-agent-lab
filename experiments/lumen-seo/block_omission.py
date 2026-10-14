#!/usr/bin/env python3
"""Structured omission sensitivity for daily GSC query/page labels.

Offline, standard-library-only; observational labels are NOT proof of SEO harm.
Requires temporal_overlap.py from this directory.
"""
import argparse
from collections import defaultdict
from datetime import timedelta
import json
import sys
from temporal_overlap import audit, read_csv


def label(entries, query):
    found = audit({query: entries})['results']
    return found[0]['classification'] if found else 'not_detected'


def evaluate(grouped, *, window_days=3, max_probes_per_query=500, max_probes_total=5000):
    if not isinstance(window_days, int) or window_days < 2:
        raise ValueError('window_days must be an integer >= 2')
    if not isinstance(max_probes_per_query, int) or max_probes_per_query < 1:
        raise ValueError('max_probes_per_query must be a positive integer')
    if not isinstance(max_probes_total, int) or max_probes_total < 1:
        raise ValueError('max_probes_total must be a positive integer')
    budget = max_probes_total
    result = []
    for query in sorted(grouped):
        entries = grouped[query]
        baseline = label(entries, query)
        positives = {(day, page): n for (day, page), n in entries.items() if n > 0}
        days = sorted({d for d, _ in positives})
        pages = sorted({p for _, p in positives})
        # Calendar windows include gaps; they are not N consecutive observed rows.
        scenarios = {
            'one_page': [(f'page:{p}', {key for key in positives if key[1] == p}) for p in pages],
            'one_date': [(f'date:{d.isoformat()}', {key for key in positives if key[0] == d}) for d in days],
            'calendar_window': [(f'window:{d.isoformat()}',
                                 {key for key in positives if d <= key[0] < d + timedelta(days=window_days)})
                                for d in days],
        }
        cost = sum(len(cases) for cases in scenarios.values())
        item = {'query': query, 'baseline': baseline, 'positive_rows': len(positives),
                'candidate_probes': cost}
        if cost > max_probes_per_query or cost > budget:
            item['status'] = 'not_assessed_budget'
            item['probes_run'] = 0
            result.append(item)
            continue
        if not positives:
            item['status'] = 'not_assessed_no_positive_rows'
            item['probes_run'] = 0
            result.append(item)
            continue
        item['status'] = 'assessed'
        item['probes_run'] = cost
        item['blocks'] = {}
        for mode, cases in scenarios.items():
            changed = 0
            outcomes = defaultdict(int)
            examples = []
            for identifier, dropped in cases:
                reduced = {k: v for k, v in entries.items() if k not in dropped}
                after = label(reduced, query)
                outcomes[after] += 1
                if after != baseline:
                    changed += 1
                    if len(examples) < 3:
                        examples.append({'block': identifier, 'removed_rows': len(dropped), 'new_label': after})
            item['blocks'][mode] = {'probes': len(cases), 'changed': changed,
                                    'stable_under_all': changed == 0,
                                    'outcomes': dict(sorted(outcomes.items())),
                                    'examples': examples}
        budget -= cost
        result.append(item)
    return {'schema_version': 1, 'status': 'ok', 'window_days': window_days,
            'max_probes_per_query': max_probes_per_query, 'max_probes_total': max_probes_total,
            'assessed_queries': sum(x['status'] == 'assessed' for x in result),
            'unassessed_queries': sum(x['status'] != 'assessed' for x in result),
            'queries': result, 'limitations': [
                'Dropping all rows for one page is deliberately severe and can erase any multi-page signal.',
                'These are hypothetical omissions, not estimated probabilities or evidence that GSC omitted those rows.',
                'A stable label does not establish complete GSC data, simultaneous ranking, or SEO harm.',
                'Only positive-impression rows are used to define blocks; zero rows are retained but inert.',
                'Not-assessed queries must never be described as stable.']}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv_path')
    p.add_argument('--window-days', type=int, default=3)
    p.add_argument('--max-probes-per-query', type=int, default=500)
    p.add_argument('--max-probes-total', type=int, default=5000)
    args = p.parse_args(argv)
    try:
        result = evaluate(read_csv(args.csv_path), window_days=args.window_days,
                          max_probes_per_query=args.max_probes_per_query,
                          max_probes_total=args.max_probes_total)
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({'status': 'invalid_input', 'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
