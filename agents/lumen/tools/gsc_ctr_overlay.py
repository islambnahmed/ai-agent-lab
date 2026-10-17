#!/usr/bin/env python3
"""Add an advisory CTR screen to a GSC handoff JSON report (stdin -> stdout).

Never changes original priorities; does not establish significance or causality.
Usage: python gsc_ctr_overlay.py < original_report.json > separate_overlay.json
"""
import copy
import json
import sys
from gsc_ctr_uncertainty import ctr_change_screen, MAX_COUNT

LIMIT = 8 * 1024 * 1024


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('invalid JSON constant: ' + value)


def overlay(report):
    if not isinstance(report, dict) or report.get('method') != 'gsc_query_page_handoff_v1':
        raise ValueError('unsupported report method')
    if 'ctr_uncertainty_overlay' in report:
        raise ValueError('already annotated')
    results = report.get('results')
    if not isinstance(results, dict) or not isinstance(results.get('signals'), list):
        raise ValueError('missing signals')
    output = copy.deepcopy(report)
    counts = {'positive_drop_screen': 0, 'negative_drop_screen': 0,
              'uncertain_direction': 0, 'not_screenable': 0}
    for row in output['results']['signals']:
        if not isinstance(row, dict) or 'ctr_uncertainty' in row:
            raise ValueError('invalid or already annotated signal')
        values = [row.get(k) for k in ('clicks_a', 'impressions_a', 'clicks_b', 'impressions_b')]
        if any(type(v) is not int for v in values):
            raise ValueError('counts must be integers')
        ca, ia, cb, ib = values
        if min(values) < 0 or max(values) > MAX_COUNT or ca > ia or cb > ib:
            raise ValueError('invalid click/impression counts')
        screen = (ctr_change_screen(*values) if ia and ib else
                  {'screen': 'not_screenable', 'reason': 'zero impressions'})
        row['ctr_uncertainty'] = screen
        counts[screen['screen']] += 1
    output['ctr_uncertainty_overlay'] = {
        'method': 'marginal_wilson_difference_screen_v1',
        'counts': counts,
        'original_priorities_preserved': True,
        'source_report_not_authenticated': True,
        'limitations': [
            'Descriptive heuristic only, not a validated significance test for GSC aggregates.',
            'Dependence, export truncation, SERP changes and filters can invalidate the screen.',
            'No automated SEO changes or causal conclusions follow from this overlay.'
        ]
    }
    return output


def main():
    try:
        raw = sys.stdin.buffer.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('report exceeds 8 MiB')
        report = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_keys,
                            parse_constant=reject_constant)
        print(json.dumps(overlay(report), ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        print('Invalid report: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
