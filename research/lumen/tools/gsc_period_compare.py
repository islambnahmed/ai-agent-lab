#!/usr/bin/env python3
"""Offline comparison of two GSC Pages CSV exports (no API or network).

Identifies *observed* changes, not causes or predicted recoverable clicks.
Each file must contain one row per page for the whole comparison period.
Use identical GSC filters (property, search type, country, device, etc.) for both.
"""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

MAX_BYTES = 30_000_000
MAX_ROWS = 250_000
REQUIRED = ('Top pages', 'Clicks', 'Impressions', 'CTR', 'Position')


def decimal_value(raw, label):
    value = str(raw or '').strip()
    if not value or ',' in value:
        raise ValueError(f'{label}: missing or ambiguous number')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f'{label}: invalid number') from exc
    if not result.is_finite():
        raise ValueError(f'{label}: nonfinite number')
    return result


def read_pages(filename):
    path = Path(filename)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('CSV missing or larger than 30 MB')
    pages = {}
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('missing or duplicate CSV header')
        if not all(col in reader.fieldnames for col in REQUIRED):
            raise ValueError('required Pages CSV columns missing')
        if any(col in reader.fieldnames for col in ('Query', 'Top queries', 'Date')):
            raise ValueError('query/date dimensions unsupported; export aggregated Pages only')
        for row_no, row in enumerate(reader, 1):
            if row_no > MAX_ROWS:
                raise ValueError('CSV row limit exceeded')
            if None in row:
                raise ValueError(f'row {row_no}: extra CSV cells')
            url = str(row['Top pages'] or '').strip()
            try:
                parsed = urlsplit(url)
                if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError('invalid URL or embedded credentials')
                if url in pages:
                    raise ValueError('duplicate page (possible double count)')
                clicks = decimal_value(row['Clicks'], 'Clicks')
                impressions = decimal_value(row['Impressions'], 'Impressions')
                pos = decimal_value(row['Position'], 'Position')
                ctr_raw = str(row['CTR'] or '').strip()
                ctr = decimal_value(ctr_raw[:-1], 'CTR') / 100 if ctr_raw.endswith('%') else decimal_value(ctr_raw, 'CTR')
                if clicks < 0 or impressions < 0 or clicks != int(clicks) or impressions != int(impressions):
                    raise ValueError('clicks/impressions must be nonnegative integers')
                if clicks > impressions or pos < 1 or not 0 <= ctr <= 1:
                    raise ValueError('invalid clicks, impressions, position or CTR')
                if impressions == 0:
                    if clicks or ctr:
                        raise ValueError('zero impressions require zero clicks and CTR')
                elif abs(clicks / impressions - ctr) > Decimal('0.0006'):
                    raise ValueError('CTR inconsistent with clicks/impressions')
                pages[url] = (int(clicks), int(impressions), clicks / impressions if impressions else Decimal(0), pos)
            except ValueError as exc:
                raise ValueError(f'row {row_no}: {exc}') from exc
    if not pages:
        raise ValueError('no Pages data rows')
    return pages


def period(start, end):
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError) as exc:
        raise ValueError('dates must be valid YYYY-MM-DD') from exc
    if first.isoformat() != start or last.isoformat() != end or first > last:
        raise ValueError('invalid or noncanonical period')
    return first, last


def compare(a, b, a_start, a_end, b_start, b_end, min_impressions=100, min_ctr_drop_pp=1, max_position_shift=1):
    a_first, a_last = period(a_start, a_end)
    b_first, b_last = period(b_start, b_end)
    if not a_last < b_first:
        raise ValueError('periods must not overlap and B must follow A')
    if (a_last - a_first).days != (b_last - b_first).days:
        raise ValueError('periods must have the same number of calendar days')
    if (min_impressions < 1 or not Decimal(str(min_ctr_drop_pp)).is_finite()
            or not Decimal(str(max_position_shift)).is_finite()
            or min_ctr_drop_pp <= 0 or max_position_shift < 0):
        raise ValueError('invalid comparison thresholds')
    left, right = read_pages(a), read_pages(b)
    common = left.keys() & right.keys()
    findings = []
    for url in common:
        clicks_a, imp_a, ctr_a, pos_a = left[url]
        clicks_b, imp_b, ctr_b, pos_b = right[url]
        if min(imp_a, imp_b) < min_impressions:
            continue
        ctr_change_pp = (ctr_b - ctr_a) * 100
        pos_change = pos_b - pos_a
        if ctr_change_pp > -Decimal(str(min_ctr_drop_pp)) or abs(pos_change) > Decimal(str(max_position_shift)):
            continue
        findings.append({
            'page': url,
            'clicks_a': clicks_a, 'clicks_b': clicks_b,
            'impressions_a': imp_a, 'impressions_b': imp_b,
            'ctr_a_pct': round(float(ctr_a * 100), 3),
            'ctr_b_pct': round(float(ctr_b * 100), 3),
            'ctr_change_pp': round(float(ctr_change_pp), 3),
            'position_a': round(float(pos_a), 3),
            'position_b': round(float(pos_b), 3),
            'position_change': round(float(pos_change), 3),
            'hypothetical_click_difference_at_b_impressions': round(float((ctr_a - ctr_b) * imp_b), 2),
        })
    findings.sort(key=lambda x: (-x['hypothetical_click_difference_at_b_impressions'], x['page']))
    return {
        'method': 'offline_gsc_two_period_comparison_v1',
        'period_a': [a_start, a_end], 'period_b': [b_start, b_end],
        'pages_a': len(left), 'pages_b': len(right),
        'overlapping_pages': len(common),
        'pages_only_in_a': len(left.keys() - right.keys()),
        'pages_only_in_b': len(right.keys() - left.keys()),
        'candidate_count': len(findings), 'candidates': findings,
        'limitations': [
            'Same property/search-type/country/device/filters must be verified manually; CSV does not prove filter equivalence.',
            'GSC Pages exports may be truncated, filtered, anonymized or incomplete; missing pages are NOT zero traffic.',
            'Stable average position does not prove stable queries, impressions, intent or SERP appearance.',
            'CTR differences and hypothetical click differences are descriptive, not causal or recoverable click estimates.',
            'No statistical significance or expected business impact is claimed.',
        ],
    }


def private_json(path, report):
    destination = Path(path)
    if not destination.parent.is_dir() or destination.is_symlink():
        raise ValueError('output directory missing or output is a symlink')
    fd, temporary = tempfile.mkstemp(prefix='.gsc-compare-', dir=destination.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pages_a')
    parser.add_argument('pages_b')
    parser.add_argument('--a-start', required=True)
    parser.add_argument('--a-end', required=True)
    parser.add_argument('--b-start', required=True)
    parser.add_argument('--b-end', required=True)
    parser.add_argument('--min-impressions', type=int, default=100)
    parser.add_argument('--min-ctr-drop-pp', type=float, default=1)
    parser.add_argument('--max-position-shift', type=float, default=1)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        report = compare(args.pages_a, args.pages_b, args.a_start, args.a_end,
                         args.b_start, args.b_end, args.min_impressions,
                         args.min_ctr_drop_pp, args.max_position_shift)
        private_json(args.output, report)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(f"Compared {report['overlapping_pages']} shared pages; {report['candidate_count']} candidates. Private report saved.")


if __name__ == '__main__':
    main()
