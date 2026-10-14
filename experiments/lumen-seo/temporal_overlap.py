#!/usr/bin/env python3
"""Daily GSC query-page co-visibility triage (stdlib only; no SEO-harm claims)."""
import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlsplit

HEADERS = {'date', 'query', 'page', 'clicks', 'impressions', 'position'}


def read_csv(path):
    path = Path(path)
    if path.stat().st_size > 25_000_000:
        raise ValueError('CSV too large')
    grouped = defaultdict(dict)
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not HEADERS.issubset(reader.fieldnames):
            raise ValueError('unique date,query,page,clicks,impressions,position headers required')
        for line, row in enumerate(reader, 2):
            try:
                if None in row or any(row[k] is None for k in HEADERS):
                    raise ValueError('malformed row')
                try:
                    day = date.fromisoformat(row['date'])
                except (ValueError, TypeError) as exc:
                    raise ValueError('date must be YYYY-MM-DD') from exc
                if day.isoformat() != row['date']:
                    raise ValueError('date must be YYYY-MM-DD')
                query = ' '.join(row['query'].split()).casefold()
                page = row['page'].strip()
                url = urlsplit(page)
                if not query or url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.fragment or any(c.isspace() or ord(c) < 32 for c in page):
                    raise ValueError('invalid query or page URL')
                _ = url.port
                clicks, imps, pos = (float(row[k]) for k in ('clicks', 'impressions', 'position'))
                if not all(math.isfinite(x) and x >= 0 for x in (clicks, imps, pos)) or clicks > imps or (imps > 0 and pos < 1) or (imps == 0 and pos != 0):
                    raise ValueError('inconsistent metrics')
                key = (day, page)
                if key in grouped[query]:
                    raise ValueError('duplicate date/query/page; possible double-counting')
                grouped[query][key] = imps
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError(f'row {line}: {exc}') from exc
    return grouped


def audit(grouped, min_daily_total=20, min_daily_page=5, min_daily_share=0.10, min_days=3):
    if min_daily_total < 1 or min_daily_page < 1 or not 0 < min_daily_share <= 0.5 or min_days < 2:
        raise ValueError('invalid thresholds')
    results = []
    for query, entries in grouped.items():
        by_day = defaultdict(dict)
        totals = defaultdict(float)
        for (day, page), imps in entries.items():
            if imps:
                by_day[day][page] = imps
                totals[page] += imps
        if len(totals) < 2:
            continue
        eligible = []
        for day, pages in sorted(by_day.items()):
            total = sum(pages.values())
            if total < min_daily_total:
                continue
            co_visible = sum(imps >= min_daily_page and imps / total >= min_daily_share for imps in pages.values()) >= 2
            dominant = min(pages, key=lambda p: (-pages[p], p))
            eligible.append((day, dominant, co_visible))
        if not eligible:
            continue
        overlap = sum(co for _, _, co in eligible)
        adjacent_pairs = [(a, b) for a, b in zip(eligible, eligible[1:]) if b[0] - a[0] == timedelta(days=1)]
        switches = sum(a[1] != b[1] for a, b in adjacent_pairs)
        gaps = sum(b[0] - a[0] != timedelta(days=1) for a, b in zip(eligible, eligible[1:]))
        fraction = overlap / len(eligible)
        if len(eligible) < min_days:
            category = 'insufficient_days'
        elif overlap == 0 and switches >= 2:
            category = 'repeated_dominance_reversals'
        elif overlap == 0 and switches == 1:
            category = 'sequential_handoff_possible'
        elif overlap >= 2 and fraction >= 0.5:
            category = 'persistent_co_visibility'
        else:
            category = 'mixed_or_sparse'
        results.append({'query': query, 'classification': category, 'eligible_days': len(eligible),
                        'co_visible_days': overlap, 'co_visible_day_fraction': round(fraction, 4),
                        'adjacent_dominant_page_switches': switches, 'adjacent_day_pairs': len(adjacent_pairs),
                        'eligible_day_gaps': gaps, 'total_page_impressions': sum(totals.values()),
                        'distinct_pages': len(totals)})
    results.sort(key=lambda r: (-r['total_page_impressions'], r['query']))
    return {'status': 'ok', 'queries_with_multiple_pages': len(results), 'results': results, 'caveats': [
        'GSC may omit/anonymize query-page rows; absent days are unknown, not zero.',
        'Same-day visibility does not prove simultaneous SERP ranking or SEO harm.',
        'A handoff can be intentional; inspect URLs, intent, canonicalization and changes manually.',
        'Repeated observed dominance reversals warrant review but do not prove cannibalization.',
        'Adjacent switches ignore missing days; gaps limit certainty about continuity.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_path')
    args = parser.parse_args(argv)
    try:
        result = audit(read_csv(args.csv_path))
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        print(json.dumps({'status': 'invalid_input', 'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
