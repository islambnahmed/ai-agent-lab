"""Offline CSV import + human-label evaluation for C330 robots inventory audit.

No network requests. Labels are analyst-provided hypotheses, never inferred from robots.txt.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import re

from offline_robots_inventory_audit import MAX_URLS, MAX_CLICKS, _origin, audit

MAX_CSV_BYTES = 10 * 1024 * 1024
LABELS = frozenset({'intentional', 'accidental', 'unknown'})
_GSC_COLUMNS = frozenset({'Top pages', 'Clicks', 'Impressions', 'CTR', 'Position', 'segment', 'intent_label'})
_MANUAL_COLUMNS = frozenset({'url', 'organic_clicks_30d', 'segment', 'intent_label'})


def _dates(start: str, end: str) -> dict:
    try:
        s, e = date.fromisoformat(start), date.fromisoformat(end)
    except (ValueError, TypeError) as exc:
        raise ValueError('period dates must be ISO YYYY-MM-DD') from exc
    if e - s != timedelta(days=29):
        raise ValueError('period must be exactly 30 calendar days, inclusive; never relabel other windows as 30d')
    return {'start': s.isoformat(), 'end': e.isoformat(), 'days_inclusive': 30}


def _clicks(raw: str, line: int) -> int:
    if not re.fullmatch(r'[0-9]+', raw or ''):
        raise ValueError(f'CSV row {line}: clicks must be an ASCII nonnegative integer')
    val = int(raw)
    if val > MAX_CLICKS:
        raise ValueError(f'CSV row {line}: clicks exceed limit')
    return val


def import_inventory(csv_path: Path, *, period_start: str, period_end: str):
    """Return (inventory, human labels, provenance). Reject ambiguous and conflicting rows."""
    period = _dates(period_start, period_end)
    raw = csv_path.read_bytes()
    if len(raw) > MAX_CSV_BYTES:
        raise ValueError('CSV exceeds 10 MiB')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('CSV must be UTF-8') from exc
    reader = csv.DictReader(text.splitlines(keepends=True), strict=True)
    headers = reader.fieldnames
    if not headers or len(set(headers)) != len(headers) or any(not h for h in headers):
        raise ValueError('CSV requires unique, nonempty headers')
    if {'Top pages', 'Clicks'} <= set(headers) and set(headers) <= _GSC_COLUMNS:
        source, url_col, click_col = 'gsc_pages_export', 'Top pages', 'Clicks'
    elif {'url', 'organic_clicks_30d'} <= set(headers) and set(headers) <= _MANUAL_COLUMNS:
        source, url_col, click_col = 'manual_inventory', 'url', 'organic_clicks_30d'
    else:
        raise ValueError('unsupported/ambiguous CSV headers: use Top pages,Clicks or url,organic_clicks_30d')
    items, labels, seen = [], {}, {}
    for n, row in enumerate(reader, 2):
        if len(items) >= MAX_URLS:
            raise ValueError('CSV exceeds 50000 data rows')
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f'CSV row {n}: wrong column count')
        url = row[url_col]
        segment = row.get('segment', '') or 'unassigned'
        label = row.get('intent_label', '') or 'unknown'
        if label not in LABELS:
            raise ValueError(f'CSV row {n}: intent_label must be intentional, accidental, or unknown')
        if not 1 <= len(segment) <= 80:
            raise ValueError(f'CSV row {n}: invalid segment')
        clicks = _clicks(row[click_col], n)
        signature = (clicks, segment, label)
        if url in seen:
            if seen[url] != signature:
                raise ValueError(f'CSV row {n}: conflicting duplicate URL; fix source before auditing')
            raise ValueError(f'CSV row {n}: duplicate URL; deduplicate at source before auditing')
        seen[url] = signature
        items.append({'url': url, 'segment': segment, 'organic_clicks_30d': clicks})
        labels[url] = label
    if not items:
        raise ValueError('CSV contains no data rows')
    return items, labels, {'source_format': source, 'period': period, 'input_file_bytes': len(raw),
                           'row_count': len(items), 'origin_and_dates_user_supplied': True,
                           'source_not_independently_verified': True}


def evaluate_intent(report: dict, labels: dict[str, str]) -> dict:
    """Precision among *labeled blocked* rows only; abstain on unknown intent."""
    blocked = [r for r in report['rows'] if r['status'] == 'disallowed']
    accidental = [r for r in blocked if labels.get(r['url']) == 'accidental']
    intentional = [r for r in blocked if labels.get(r['url']) == 'intentional']
    known = len(accidental) + len(intentional)
    return {
        'disallowed_total': len(blocked), 'disallowed_with_known_intent': known,
        'disallowed_unlabeled': len(blocked) - known,
        'labeled_accidental': len(accidental), 'labeled_intentional': len(intentional),
        'labeled_review_precision': round(len(accidental) / known, 6) if known else None,
        'known_intent_coverage': round(known / len(blocked), 6) if blocked else None,
        'analyst_labeled_accidental_urls': [r['url'] for r in accidental],
        'interpretation': ('Precision uses only manually labeled disallowed URLs; unlabeled, unknown, '
                           'and out-of-scope rows are not negatives. No claim about recall, '
                           'indexability, actual Googlebot behavior, or lost traffic.'),
    }


def run(*, csv_path: Path, origin: str, user_agent: str, robots_path: Path,
        period_start: str, period_end: str) -> dict:
    inventory, labels, provenance = import_inventory(csv_path, period_start=period_start, period_end=period_end)
    # Origin must be explicitly provided; provenance does not authenticate the GSC property.
    normalized = _origin(origin)
    raw_robots = robots_path.read_bytes()
    try:
        robots = raw_robots.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('robots file must be UTF-8') from exc
    result = audit(robots, origin, user_agent, inventory)
    result['provenance'] = {**provenance, 'declared_property_origin':
                            f'{normalized[0]}://{normalized[1]}:{normalized[2]}',
                            'robots_file_source': 'local_file_unverified',
                            'human_intent_labels': 'provided_in_csv_not_verified'}
    result['intent_evaluation'] = evaluate_intent(result, labels)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--origin', required=True)
    ap.add_argument('--user-agent', required=True)
    ap.add_argument('--robots-file', type=Path, required=True)
    ap.add_argument('--csv', type=Path, required=True)
    ap.add_argument('--period-start', required=True, help='YYYY-MM-DD, inclusive')
    ap.add_argument('--period-end', required=True, help='YYYY-MM-DD, inclusive; exactly 30 days')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        result = run(csv_path=args.csv, origin=args.origin, user_agent=args.user_agent,
                     robots_path=args.robots_file, period_start=args.period_start, period_end=args.period_end)
    except (ValueError, OSError, csv.Error) as exc:
        ap.error(str(exc))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': result['summary'], 'intent_evaluation': result['intent_evaluation']}, sort_keys=True))


if __name__ == '__main__':
    main()
