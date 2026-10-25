#!/usr/bin/env python3
"""Compare two offline sitemap inventory CSV exports; no network or dependencies."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

COLUMNS = ['source_sitemap', 'normalized_url', 'lastmod', 'duplicate']
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_ROWS = 1_000_000
MAX_REPORT_BYTES = 8 * 1024 * 1024


def load_inventory(path: Path) -> dict[str, Counter[tuple[str, str]]]:
    """Preserve source and lastmod multiplicity, independent of CSV row order."""
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f'inventory missing or exceeds {MAX_INPUT_BYTES} bytes: {path}')
    result: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    first_markers: Counter[str] = Counter()
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames != COLUMNS:
                raise ValueError(f'invalid inventory columns: {path}; expected {COLUMNS}')
            for number, row in enumerate(reader, start=2):
                if number > MAX_ROWS + 1:
                    raise ValueError(f'inventory row limit exceeded: {path}')
                if None in row or any(row[col] is None for col in COLUMNS):
                    raise ValueError(f'malformed CSV row {number}: {path}')
                if not row['normalized_url'].startswith(('http://', 'https://')) or not row['source_sitemap']:
                    raise ValueError(f'invalid inventory URL/source at row {number}: {path}')
                if row['duplicate'] not in ('true', 'false'):
                    raise ValueError(f'invalid duplicate marker at row {number}: {path}')
                if row['duplicate'] == 'false':
                    first_markers[row['normalized_url']] += 1
                key = (row['source_sitemap'], row['lastmod'])
                result[row['normalized_url']][key] += 1
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f'cannot parse inventory {path}: {type(exc).__name__}') from exc
    # The exporter marks exactly one occurrence of each URL as non-duplicate.
    # Do not require that marker to appear first: snapshots may be row-reordered.
    for url in result:
        if first_markers[url] != 1:
            raise ValueError(f'inconsistent duplicate markers for URL {url!r}: {path}')
    return dict(result)



def verify_audit_report(path: Path, csv_path: Path, inventory: dict) -> dict:
    """Check a clean audit report and its SHA-256 binding to the exact CSV bytes.

    This detects accidental file swaps and partial audits, not forged reports.
    """
    if not path.is_file() or path.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError(f'audit report missing or exceeds {MAX_REPORT_BYTES} bytes: {path}')
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'cannot parse audit report {path}: {type(exc).__name__}') from exc
    if not isinstance(report, dict) or report.get('schema_version') != 1 or report.get('kind') != 'offline_sitemap_inventory':
        raise ValueError(f'unsupported audit report: {path}')
    summary, exported = report.get('summary'), report.get('csv_export')
    if not isinstance(summary, dict) or not isinstance(exported, dict):
        raise ValueError(f'audit report missing CSV export metadata: {path}')
    # Duplicates and lastmod/origin warnings do not omit CSV rows.
    # All unknown or structural issues fail closed, because they may hide URLs.
    non_omitting_codes = {'duplicate_url', 'future_lastmod', 'invalid_lastmod',
                          'off_host_url', 'off_origin_url'}
    issues = report.get('issues')
    if (not isinstance(issues, list) or summary.get('issues') != len(issues)
            or any(not isinstance(issue, dict)
                   or issue.get('code') not in non_omitting_codes for issue in issues)):
        raise ValueError(f'audit has incomplete or unmapped sitemap entries: {path}')
    rows = sum(sum(counts.values()) for counts in inventory.values())
    if (summary.get('urls') != rows or summary.get('unique_urls') != len(inventory)
            or exported.get('rows') != rows or exported.get('bytes') != csv_path.stat().st_size):
        raise ValueError(f'CSV inventory counts differ from audit report: {path}')
    if any(type(summary.get(field)) is not int or summary[field] < 1
           for field in ('sitemaps', 'urlsets')):
        raise ValueError(f'audit has no valid complete URL set counts: {path}')
    with csv_path.open('rb') as stream:
        actual_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if exported.get('sha256') != actual_digest:
        raise ValueError(f'CSV SHA-256 differs from audit report: {path}')
    base_url, as_of = report.get('base_url'), report.get('as_of')
    start_sitemap = report.get('start_sitemap')
    if not isinstance(start_sitemap, str) or not start_sitemap or start_sitemap.startswith('/'):
        raise ValueError(f'audit report missing valid start sitemap scope: {path}')
    if not isinstance(base_url, str) or not base_url.startswith(('http://', 'https://')):
        raise ValueError(f'invalid audit origin: {path}')
    try:
        day = dt.date.fromisoformat(as_of)
        if day.isoformat() != as_of:
            raise ValueError('noncanonical date')
    except (TypeError, ValueError) as exc:
        raise ValueError(f'invalid audit as_of date: {path}') from exc
    return {'base_url': base_url, 'as_of': as_of, 'start_sitemap': start_sitemap}


def _details(counts: Counter[tuple[str, str]]) -> list[dict]:
    return [{'source_sitemap': source, 'lastmod': lastmod, 'count': count}
            for (source, lastmod), count in sorted(counts.items())]


def compare(before: dict, after: dict) -> dict:
    old, new = set(before), set(after)
    added = sorted(new - old)
    removed = sorted(old - new)
    modified = sorted(url for url in old & new if before[url] != after[url])
    return {
        'schema_version': 1,
        'kind': 'offline_sitemap_inventory_diff',
        'summary': {
            'before_urls': len(old), 'after_urls': len(new),
            'before_rows': sum(sum(v.values()) for v in before.values()),
            'after_rows': sum(sum(v.values()) for v in after.values()),
            'added_urls': len(added), 'removed_urls': len(removed),
            'changed_existing_urls': len(modified),
        },
        'added_urls': added,
        'removed_urls': removed,
        'changed_existing_urls': [
            {'url': url, 'before': _details(before[url]), 'after': _details(after[url])}
            for url in modified
        ],
        'limitations': [
            'This compares offline CSV exports, not live pages or Google indexation',
            'Changes in lastmod are claims in the sitemap, not verified page updates',
            'URL matching uses the exact normalized_url strings supplied by the exporter',
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', required=True, type=Path)
    parser.add_argument('--after', required=True, type=Path)
    parser.add_argument('--before-report', type=Path, help='Optional paired JSON audit report for verified comparison')
    parser.add_argument('--after-report', type=Path, help='Optional paired JSON audit report for verified comparison')
    args = parser.parse_args(argv)
    try:
        if (args.before_report is None) != (args.after_report is None):
            raise ValueError('both --before-report and --after-report are required together')
        before = load_inventory(args.before)
        after = load_inventory(args.after)
        if args.before_report is not None:
            previous = verify_audit_report(args.before_report, args.before, before)
            current = verify_audit_report(args.after_report, args.after, after)
            if previous['base_url'] != current['base_url']:
                raise ValueError('audit origins differ; snapshots cannot be compared as one site')
            if previous['start_sitemap'] != current['start_sitemap']:
                raise ValueError('audit start sitemap entrypoints differ; snapshot scope is not comparable')
            if previous['as_of'] > current['as_of']:
                raise ValueError('before audit date is after the after audit date')
            verification = {'status': 'complete_audit_csv_sha256_checked',
                            'base_url': previous['base_url'],
                            'start_sitemap': previous['start_sitemap'],
                            'before_as_of': previous['as_of'],
                            'after_as_of': current['as_of'],
                            'limitation': 'Local JSON reports are not authenticated; this does not prove capture time or live-site completeness'}
        else:
            verification = {'status': 'csv_only_unverified',
                            'limitation': 'Without paired clean audit reports, apparent removals may reflect incomplete sitemap exports'}
        result = compare(before, after)
        result['verification'] = verification
    except ValueError as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if (result['summary']['added_urls'] or result['summary']['removed_urls']
                 or result['summary']['changed_existing_urls']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
