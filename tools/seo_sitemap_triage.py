#!/usr/bin/env python3
"""Convert an offline sitemap diff JSON into a conservative SEO review queue CSV.

This does not check live URLs, indexation, redirects, or rankings.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys

MAX_INPUT_BYTES = 8 * 1024 * 1024
COLUMNS = ['priority', 'change', 'url', 'review_action', 'evidence',
           'rows_before', 'rows_after']
STATUSES = {'csv_only_unverified', 'complete_audit_csv_sha256_checked'}


def _urls(items: object, name: str) -> list[str]:
    if not isinstance(items, list) or any(not isinstance(x, str) or
            not x.startswith(('https://', 'http://')) for x in items):
        raise ValueError(f'invalid {name} URL list')
    if len(items) != len(set(items)):
        raise ValueError(f'duplicate URLs in {name}')
    return items


def _rows(details: object) -> tuple[int, Counter[str], set[str]]:
    if not isinstance(details, list):
        raise ValueError('invalid changed URL details')
    total, sources, lastmods = 0, Counter(), set()
    for entry in details:
        if (not isinstance(entry, dict) or
                not isinstance(entry.get('source_sitemap'), str) or
                not isinstance(entry.get('lastmod'), str) or
                type(entry.get('count')) is not int or entry['count'] < 1):
            raise ValueError('invalid changed URL detail row')
        total += entry['count']
        sources[entry['source_sitemap']] += entry['count']
        lastmods.add(entry['lastmod'])
    if total < 1:
        raise ValueError('empty changed URL detail rows')
    return total, sources, lastmods


def build_queue(diff: object) -> list[list[str | int]]:
    if (not isinstance(diff, dict) or diff.get('schema_version') != 1 or
            diff.get('kind') != 'offline_sitemap_inventory_diff'):
        raise ValueError('unsupported sitemap diff format')
    verification = diff.get('verification')
    status = verification.get('status') if isinstance(verification, dict) else None
    if status not in STATUSES:
        raise ValueError('missing or unsupported diff evidence status')
    evidence = ('local_csv_sha_checked' if status == 'complete_audit_csv_sha256_checked'
                else 'csv_only_unverified')
    added = _urls(diff.get('added_urls'), 'added')
    removed = _urls(diff.get('removed_urls'), 'removed')
    changed = diff.get('changed_existing_urls')
    if not isinstance(changed, list):
        raise ValueError('invalid changed URL list')
    summary = diff.get('summary')
    if (not isinstance(summary, dict) or
            any(type(summary.get(k)) is not int or summary[k] < 0 for k in
                ('added_urls', 'removed_urls', 'changed_existing_urls')) or
            (len(added), len(removed), len(changed)) !=
            (summary['added_urls'], summary['removed_urls'], summary['changed_existing_urls'])):
        raise ValueError('diff summary counts do not match entries')
    seen = set(added) | set(removed)
    if len(seen) != len(added) + len(removed):
        raise ValueError('URL appears in added and removed lists')
    queue: list[list[str | int]] = []
    for url in removed:
        queue.append(['P1', 'removed', url, 'Review intentional removal and redirects', evidence, '', 0])
    for entry in changed:
        if not isinstance(entry, dict):
            raise ValueError('invalid changed URL entry')
        url = entry.get('url')
        if not isinstance(url, str) or not url.startswith(('http://', 'https://')) or url in seen:
            raise ValueError('invalid or repeated changed URL')
        seen.add(url)
        before_n, before_sources, before_dates = _rows(entry.get('before'))
        after_n, after_sources, after_dates = _rows(entry.get('after'))
        if before_n != after_n:
            priority, action = 'P2', 'Review changed sitemap duplicate count'
        elif before_sources != after_sources:
            priority, action = 'P2', 'Review sitemap placement change'
        elif before_dates != after_dates:
            priority, action = 'P3', 'Validate claimed lastmod change'
        else:
            priority, action = 'P3', 'Review sitemap metadata distribution'
        queue.append([priority, 'changed', url, action, evidence, before_n, after_n])
    for url in added:
        queue.append(['P3', 'added', url, 'Review intended sitemap discovery', evidence, 0, ''])
    queue.sort(key=lambda row: (row[0], row[1], row[2]))
    return queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diff', required=True, type=Path, help='JSON from seo_sitemap_compare.py')
    args = parser.parse_args(argv)
    try:
        if not args.diff.is_file() or args.diff.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError('diff missing or too large')
        diff = json.loads(args.diff.read_text(encoding='utf-8'))
        queue = build_queue(diff)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f'Cannot triage sitemap diff: {exc}', file=sys.stderr)
        return 2
    writer = csv.writer(sys.stdout, lineterminator='\n')
    writer.writerow(COLUMNS)
    writer.writerows(queue)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
