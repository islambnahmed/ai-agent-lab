#!/usr/bin/env python3
"""Offline, privacy-preserving URL redirect-map graph audit (no network access)."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
import sys
from urllib.parse import urlsplit

COLUMNS = ['source_url', 'target_url']
MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 50000


def canonical_key(value: str) -> str:
    """Conservative URL equality: normalize scheme/host/default port only."""
    if not value or any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise ValueError('URL contains whitespace/control characters or is empty')
    if re.search(r'%(?![0-9A-Fa-f]{2})', value):
        raise ValueError('URL contains malformed percent escape')
    # Even an empty fragment marker changes the literal input; reject it rather
    # than silently collapsing distinct map entries into a false self-redirect.
    if '#' in value:
        raise ValueError('URL fragments are not allowed')
    has_query_marker = '?' in value
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in ('http', 'https') or not parts.netloc:
            raise ValueError('URL must be absolute HTTP(S)')
        if parts.username is not None or parts.password is not None:
            raise ValueError('userinfo and fragments are not allowed')
        # urlsplit treats an explicit empty port (host:) like no port, which
        # could hide malformed mappings as duplicates or self redirects.
        if parts.netloc.endswith(':'):
            raise ValueError('empty port delimiter is not allowed')
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise ValueError('invalid URL structure') from exc
    if not host or not host.isascii() or any(c in host for c in '/\\@'):
        raise ValueError('invalid or non-ASCII hostname (use punycode)')
    if port is not None and not 1 <= port <= 65535:
        raise ValueError('invalid port')
    scheme = parts.scheme.lower()
    # Default ports do not change the endpoint. Preserve nondefault ports.
    if port in (80 if scheme == 'http' else 443, None):
        port = None
    normalized_host = host.lower()
    if ':' in normalized_host:
        normalized_host = f'[{normalized_host}]'
    authority = normalized_host + (f':{port}' if port else '')
    return f'{scheme}://{authority}{parts.path or "/"}' + (f'?{parts.query}' if has_query_marker else '')


def audit(rows: list[dict[str, str]], *, line_numbers: list[int] | None = None) -> dict:
    """Return aggregate counts and CSV physical line numbers; never emit URL strings.

    Direct in-memory callers without line_numbers retain record-ordinal numbering.
    """
    if line_numbers is not None and len(line_numbers) != len(rows):
        raise ValueError('line_numbers must match rows length')
    issues: list[dict] = []
    sources: dict[str, tuple[int, str]] = {}
    valid_rows = 0
    for index, row in enumerate(rows):
        number = line_numbers[index] if line_numbers is not None else index + 2
        if set(row) != set(COLUMNS) or any(row.get(c) is None for c in COLUMNS):
            issues.append({'row': number, 'type': 'malformed_row'})
            continue
        try:
            src, dst = (canonical_key(row[c]) for c in COLUMNS)
        except ValueError:
            issues.append({'row': number, 'type': 'invalid_url'})
            continue
        valid_rows += 1
        if src in sources:
            first_row, first_target = sources[src]
            # Conflicting destinations are more dangerous than repeated identical rows.
            # Keep first-wins graph semantics so duplicate input cannot hide a cycle.
            issue_type = ('duplicate_source' if dst == first_target
                          else 'conflicting_duplicate_source')
            issues.append({'row': number, 'type': issue_type,
                           'first_row': first_row})
            continue
        sources[src] = (number, dst)
        if src == dst:
            issues.append({'row': number, 'type': 'self_redirect'})

    # Each source has at most one outgoing edge; chains and cycles are linear to detect.
    next_source = {src: dst for src, (_, dst) in sources.items() if dst in sources}
    for src, dst in next_source.items():
        if src != dst:
            issues.append({'row': sources[src][0], 'type': 'redirect_chain',
                           'target_row': sources[dst][0]})

    visited = set()
    for start in sources:
        if start in visited:
            continue
        path, positions = [], {}
        node = start
        while node in next_source and node not in visited and node not in positions:
            positions[node] = len(path)
            path.append(node)
            node = next_source[node]
        if node in positions and len(path) - positions[node] > 1:
            for cyc in path[positions[node]:]:
                issues.append({'row': sources[cyc][0], 'type': 'redirect_cycle'})
        visited.update(path)

    issues.sort(key=lambda issue: (issue['row'], issue['type']))
    return {'kind': 'offline_redirect_map_audit', 'rows': len(rows),
            'valid_rows': valid_rows, 'unique_sources': len(sources),
            'issue_counts': dict(sorted(Counter(i['type'] for i in issues).items())),
            'issues': issues,
            'limitations': ('Only checks supplied redirect mappings, not HTTP status, '
                            'server configuration, canonical tags, live behavior, '
                            'or whether cross-domain redirects are intentional. '
                            'Conservative URL equivalence; no path or query rewriting.')}


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[int]]:
    """Parse records with their physical start lines, including after blank lines."""
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('missing or oversized CSV')
    with path.open('r', newline='', encoding='utf-8-sig') as handle:
        reader = csv.reader(handle, strict=True)
        if next(reader, None) != COLUMNS:
            raise ValueError(f'expected header: {COLUMNS}')
        rows: list[dict[str, str]] = []
        line_numbers: list[int] = []
        while True:
            start_line = reader.line_num + 1
            try:
                fields = next(reader)
            except StopIteration:
                break
            # Unlike DictReader, csv.reader exposes empty records, so the
            # physical start line stays accurate after skipped blank lines.
            if not fields:
                continue
            if len(rows) >= MAX_ROWS:
                raise ValueError('too many rows')
            row = dict(zip(COLUMNS, fields))
            if len(fields) < len(COLUMNS):
                for column in COLUMNS[len(fields):]:
                    row[column] = None
            if len(fields) > len(COLUMNS):
                row[None] = fields[len(COLUMNS):]
            rows.append(row)
            line_numbers.append(start_line)
    return rows, line_numbers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map', required=True, type=Path, help='CSV source_url,target_url')
    args = parser.parse_args(argv)
    try:
        rows, line_numbers = read_rows(args.map)
        result = audit(rows, line_numbers=line_numbers)
    except (OSError, ValueError, UnicodeError, csv.Error):
        # OSError messages can contain private local paths. Avoid echoing any
        # caller-supplied filename, URL, or parser excerpt on input failure.
        print('Cannot audit redirect map: invalid or unreadable input', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
