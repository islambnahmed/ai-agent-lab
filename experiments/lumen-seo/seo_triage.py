#!/usr/bin/env python3
"""Offline, read-only SEO review queue from a daily GSC query/page CSV.

Uses temporal_overlap.py and omission_robustness.py. Python standard library only.
Never equates page overlap with SEO harm; human review is required.
"""
import argparse
from collections import defaultdict
from html import escape
import json
from pathlib import Path
import sys

from temporal_overlap import read_csv, audit
from omission_robustness import probe

LABELS = {
    'persistent_co_visibility': ('Review shared intent', 'Compare SERP intent, canonical targets, on-page differentiation and internal links. Do not consolidate solely from this signal.'),
    'repeated_dominance_reversals': ('Investigate switching', 'Review indexing/canonical history and page-level ranking changes; alternating visibility alone is not harm.'),
    'sequential_handoff_possible': ('Check handoff', 'Check publication, redirects, migration and content update dates before interpreting the transition.'),
    'mixed_or_sparse': ('Monitor / sample manually', 'Insufficient or mixed evidence: inspect actual query and URLs before changes.'),
    'insufficient_days': ('Collect more observations', 'Avoid ranking conclusions from fewer than three eligible days.'),
}


def build_queue(grouped, *, max_rows_per_query=250, max_rows_total=3000):
    observations = audit(grouped)
    # Spend finite sensitivity-test budget on highest-exposure multi-page queries first.
    # Single-page queries are not actionable overlap candidates and must not exhaust it.
    stress_by_query = {}
    remaining = max_rows_total
    for observed in observations['results']:
        q = observed['query']
        result = (probe({q: grouped[q]}, max_rows_per_query, remaining)['queries'][0]
                  if remaining > 0 else {'query': q, 'status': 'not_assessed_budget', 'probes_run': 0})
        stress_by_query[q] = result
        remaining -= result['probes_run']
    queue = []
    for row in observations['results']:
        query = row['query']
        by_page = defaultdict(lambda: {'impressions': 0, 'days': set()})
        by_day = defaultdict(list)
        for (day, page), imps in grouped[query].items():
            if imps <= 0:
                continue
            by_page[page]['impressions'] += imps
            by_page[page]['days'].add(day)
            by_day[day].append((page, imps))
        total = sum(v['impressions'] for v in by_page.values())
        pages = sorted(({'url': url, 'impressions': val['impressions'],
                         'share_pct': round(100 * val['impressions'] / total, 2),
                         'observed_days': len(val['days'])}
                        for url, val in by_page.items()),
                       key=lambda x: (-x['impressions'], x['url']))
        # Co-visible days here mirror the classifier's explicit thresholds.
        co_days = []
        for day, day_pages in sorted(by_day.items()):
            day_total = sum(imps for _, imps in day_pages)
            if day_total >= 20 and sum(imps >= 5 and imps/day_total >= 0.10 for _, imps in day_pages) >= 2:
                co_days.append(day.isoformat())
        s = stress_by_query[query]
        assessed = s['status'] == 'assessed'
        stable = assessed and s['stable_under_any_single_row_omission']
        category = row['classification']
        signal = category in ('persistent_co_visibility', 'repeated_dominance_reversals')
        # This is a triage ordering, NOT a probability or harm estimate.
        tier = ('review' if signal and stable and total >= 100 else
                'caution' if signal else 'monitor')
        queue.append({**row, 'priority_tier': tier, 'stability_status':
                      'single_row_stable' if stable else ('single_row_sensitive' if assessed else 'not_assessed'),
                      'omission_probes': s.get('probes_run', 0),
                      'omission_changes': s.get('different_labels'),
                      'suggested_review': LABELS[category][0],
                      'review_notes': LABELS[category][1],
                      'pages': pages, 'co_visible_dates': co_days[:20],
                      'co_visible_dates_truncated': len(co_days) > 20})
    order = {'review': 0, 'caution': 1, 'monitor': 2}
    queue.sort(key=lambda x: (order[x['priority_tier']], -x['total_page_impressions'], x['query']))
    return {'schema_version': 1, 'status': 'ok', 'method': 'observational_gsc_daily_query_page_triage',
            'queries_reviewed': len(queue), 'queue': queue,
            'limitations': ['No access to live SERPs, search intent, site content or canonical tags.',
                            'GSC omits some queries/rows and is not an exhaustive daily ranking ledger.',
                            'Co-visibility does not establish simultaneous SERP ranking or cannibalization harm.',
                            'Single-row stability is a stress test, not a probability or data completeness guarantee.',
                            'Priority tiers are heuristic and do not estimate SEO benefit.']}


def html_report(report):
    rows = []
    for item in report['queue']:
        pages = '<br>'.join(f'<code>{escape(p["url"], quote=True)}</code> — {p["share_pct"]:.2f}% ({p["impressions"]:g} impressions)'
                            for p in item['pages'][:3])
        dates = ', '.join(item['co_visible_dates']) or 'none at configured thresholds'
        rows.append('<tr>' + ''.join(f'<td>{escape(str(x), quote=True)}</td>' for x in
            [item['priority_tier'], item['query'], item['classification'], item['stability_status'],
             item['total_page_impressions'], item['co_visible_days'], item['eligible_days']]) +
            '<td>' + pages + '</td><td>' + escape(dates) + '</td><td>' +
            escape(item['review_notes']) + '</td></tr>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO Query Overlap — Human Review Queue</title><style>body{font:15px/1.5 system-ui,sans-serif;max-width:1300px;margin:2rem auto;padding:0 1rem;color:#1d2735}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d3dae3;padding:.6rem;text-align:left;vertical-align:top}th{background:#f0f4f8}tr:nth-child(even){background:#f8fafc}code{overflow-wrap:anywhere}aside{background:#fff4d8;padding:1rem;border-left:4px solid #c98d0e}div.scroll{overflow-x:auto}</style>
<h1>SEO query overlap — human review queue</h1><aside><strong>Not a cannibalization diagnosis.</strong> Overlap and switching are observations, not proof of ranking harm. The input can omit query-page rows. Do not merge, redirect or canonicalize pages automatically.</aside>
<p>Queries with multiple observed pages: ''' + str(report['queries_reviewed']) + '''. Tier “review” requires a repeated overlap/switch signal, >=100 observed impressions and stability under deleting any one positive row. It is a sorting heuristic, not a benefit estimate.</p>
<div class="scroll"><table><thead><tr><th>Tier</th><th>Query</th><th>Observation</th><th>Stress test</th><th>Impressions</th><th>Co-visible days</th><th>Eligible days</th><th>Top pages (share)</th><th>Example co-visible dates</th><th>Human next step</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div><h2>Limitations</h2><ul>''' + ''.join('<li>' + escape(x) + '</li>' for x in report['limitations']) + '''</ul></html>'''


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv_path', help='Daily GSC export with date,query,page,clicks,impressions,position')
    p.add_argument('--out', required=True, help='Directory to write report.html and report.json')
    p.add_argument('--max-rows-per-query', type=int, default=250)
    p.add_argument('--max-rows-total', type=int, default=3000)
    args = p.parse_args(argv)
    try:
        if args.max_rows_per_query < 1 or args.max_rows_total < 1:
            raise ValueError('probe budgets must be positive')
        report = build_queue(read_csv(args.csv_path), max_rows_per_query=args.max_rows_per_query,
                             max_rows_total=args.max_rows_total)
        output = Path(args.out)
        output.mkdir(parents=True, exist_ok=True)
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (output/'report.html').write_text(html_report(report), encoding='utf-8')
    except (ValueError, OSError, UnicodeError) as exc:
        print(f'Cannot create report: {exc}', file=sys.stderr)
        return 2
    print(f'Wrote {output / "report.html"} and {output / "report.json"}; {report["queries_reviewed"]} queries')
    return 0


if __name__ == '__main__':
    sys.exit(main())
