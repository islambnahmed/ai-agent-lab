#!/usr/bin/env python3
"""Offline retirement-URL coverage check for a proposed SEO redirect map."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from seo_redirect_map_audit import MAX_BYTES, MAX_ROWS, audit, canonical_key, read_rows

BLOCKING_MAP_ISSUES = frozenset({
    'invalid_url', 'malformed_row', 'conflicting_duplicate_source',
    'self_redirect', 'redirect_cycle',
})


def read_retiring(path: Path) -> list[tuple[int, str]]:
    """Return (physical CSV start line, canonical URL); never print raw URLs."""
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('retirement inventory is missing or oversized')
    result = []
    with path.open('r', newline='', encoding='utf-8-sig') as handle:
        reader = csv.reader(handle, strict=True)
        if next(reader, None) != ['url']:
            raise ValueError('retirement inventory requires a single url header')
        while True:
            line = reader.line_num + 1
            try:
                fields = next(reader)
            except StopIteration:
                break
            if not fields:
                continue
            if len(result) >= MAX_ROWS:
                raise ValueError('retirement inventory exceeds row limit')
            if len(fields) != 1:
                raise ValueError(f'malformed retirement record at line {line}')
            try:
                key = canonical_key(fields[0])
            except ValueError:
                raise ValueError(f'invalid retirement URL at line {line}') from None
            result.append((line, key))
    return result


def coverage(retiring: list[tuple[int, str]], map_rows: list[dict],
             map_lines: list[int]) -> dict:
    """Report line-only coverage gaps; input URLs never enter the result."""
    if len(map_rows) != len(map_lines):
        raise ValueError('map line-number count mismatch')
    map_report = audit(map_rows, line_numbers=map_lines)
    blocked = sorted(BLOCKING_MAP_ISSUES.intersection(map_report['issue_counts']))
    if blocked:
        # Coverage cannot be certified if graph semantics are ambiguous or broken.
        return {
            'kind': 'offline_redirect_retirement_coverage',
            'status': 'blocked',
            'blocking_map_issue_types': blocked,
            'map_issue_counts': map_report['issue_counts'],
            'limitations': 'Repair map errors and rerun; no coverage conclusion was made.',
        }

    sources = {}
    for line, row in zip(map_lines, map_rows):
        source = canonical_key(row['source_url'])
        sources.setdefault(source, line)

    seen = {}
    issues = []
    for line, key in retiring:
        key = canonical_key(key)
        if key in seen:
            issues.append({'row': line, 'type': 'duplicate_retiring_url',
                           'first_row': seen[key]})
        else:
            seen[key] = line
            if key not in sources:
                issues.append({'row': line, 'type': 'unmapped_retiring_url'})

    for source, line in sources.items():
        if source not in seen:
            issues.append({'row': line, 'type': 'unlisted_redirect_source'})

    issues.sort(key=lambda i: (i['type'], i['row']))
    return {
        'kind': 'offline_redirect_retirement_coverage',
        'status': 'complete',
        'retiring_rows': len(retiring),
        'unique_retiring_urls': len(seen),
        'unique_redirect_sources': len(sources),
        'issue_counts': dict(sorted(Counter(i['type'] for i in issues).items())),
        'map_issue_counts': map_report['issue_counts'],
        'issues': issues,
        'limitations': ('Only checks membership in supplied offline CSV files. '
                        'An unlisted source may be legitimate. Does not prove '
                        'correct destinations, deployed HTTP redirects, coverage '
                        'of all retiring URLs, indexing, or SEO outcomes.'),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retiring', type=Path, required=True,
                        help='CSV with one url column: URLs explicitly slated for retirement')
    parser.add_argument('--map', type=Path, required=True,
                        help='CSV with source_url,target_url columns')
    args = parser.parse_args(argv)
    try:
        retiring = read_retiring(args.retiring)
        rows, lines = read_rows(args.map)
        report = coverage(retiring, rows, lines)
    except (OSError, ValueError, UnicodeError, csv.Error):
        # Avoid echoing input paths, URL content, or parser snippets to stderr.
        print('Cannot audit retirement coverage: invalid or unreadable input', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report['status'] == 'blocked' else (1 if report['issues'] else 0)


if __name__ == '__main__':
    raise SystemExit(main())
