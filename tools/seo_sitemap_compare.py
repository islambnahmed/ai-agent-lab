#!/usr/bin/env python3
"""Compare two offline sitemap inventory CSV exports; no network or dependencies."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import sys

COLUMNS = ['source_sitemap', 'normalized_url', 'lastmod', 'duplicate']
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_ROWS = 1_000_000


def load_inventory(path: Path) -> dict[str, Counter[tuple[str, str]]]:
    """Preserve source and lastmod multiplicity, independent of CSV row order."""
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f'inventory missing or exceeds {MAX_INPUT_BYTES} bytes: {path}')
    result: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
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
                key = (row['source_sitemap'], row['lastmod'])
                result[row['normalized_url']][key] += 1
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f'cannot parse inventory {path}: {type(exc).__name__}') from exc
    return dict(result)


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
    args = parser.parse_args(argv)
    try:
        result = compare(load_inventory(args.before), load_inventory(args.after))
    except ValueError as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if (result['summary']['added_urls'] or result['summary']['removed_urls']
                 or result['summary']['changed_existing_urls']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
