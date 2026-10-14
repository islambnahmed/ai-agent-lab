#!/usr/bin/env python3
"""Sensitivity audit for daily GSC classifications under ONE omitted observed row.

Deterministic stress test, not a probability estimate or a claim about real GSC omissions.
"""
import argparse
import csv
import json
import sys
from temporal_overlap import audit, read_csv


def label(entries, query):
    rows = audit({query: entries})['results']
    return rows[0]['classification'] if rows else 'not_detected'


def probe(grouped, max_rows_per_query=250, max_rows_total=3000):
    if max_rows_per_query < 1 or max_rows_total < 1:
        raise ValueError('budgets must be positive integers')
    report = []
    budget = max_rows_total
    for query in sorted(grouped):
        entries = grouped[query]
        baseline = label(entries, query)
        # Zero-impression rows do not affect the classifier and are excluded from probes.
        keys = sorted((key for key, imps in entries.items() if imps > 0),
                      key=lambda x: (x[0], x[1]))
        item = {'query': query, 'baseline': baseline, 'observed_positive_rows': len(keys)}
        if len(keys) > max_rows_per_query or len(keys) > budget:
            item.update(status='not_assessed_budget', probes_run=0,
                        caveat='No stability inference: query exceeded assessment budget.')
        elif not keys:
            item.update(status='not_assessed_no_positive_rows', probes_run=0)
        else:
            counts = {}
            examples = []
            for key in keys:
                reduced = dict(entries)
                del reduced[key]
                changed = label(reduced, query)
                counts[changed] = counts.get(changed, 0) + 1
                if changed != baseline and len(examples) < 3:
                    examples.append({'omitted_date': key[0].isoformat(),
                                     'omitted_page': key[1], 'result': changed})
            changed_count = len(keys) - counts.get(baseline, 0)
            item.update(status='assessed', probes_run=len(keys),
                        different_labels=changed_count,
                        changed_fraction_of_probes=round(changed_count / len(keys), 6),
                        stable_under_any_single_row_omission=(changed_count == 0),
                        outcomes=dict(sorted(counts.items())),
                        example_changes=examples)
            budget -= len(keys)
        report.append(item)
    return {'status': 'ok', 'method': 'exhaustive_leave_one_positive_row_out',
            'max_rows_per_query': max_rows_per_query, 'max_rows_total': max_rows_total,
            'queries': report, 'assessed_queries': sum(x['status'] == 'assessed' for x in report),
            'unassessed_queries': sum(x['status'] != 'assessed' for x in report),
            'caveats': [
                'The fraction is a fraction of hypothetical single-row removals, NOT a probability of a bad classification.',
                'This stress test cannot model missing entire dates, multi-row omissions, anonymization, or systematic GSC sampling.',
                'Stability of observational labels does NOT establish keyword cannibalization or SEO harm.',
                'Query-page daily data is incomplete by design; a robust label may still be wrong about search intent.',
                'Unassessed queries are explicitly marked; never treat them as robust.'
            ]}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv_path')
    p.add_argument('--max-rows-per-query', type=int, default=250)
    p.add_argument('--max-rows-total', type=int, default=3000)
    args = p.parse_args(argv)
    try:
        result = probe(read_csv(args.csv_path), args.max_rows_per_query, args.max_rows_total)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        print(json.dumps({'status': 'invalid_input', 'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
