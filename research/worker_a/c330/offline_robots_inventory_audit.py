"""Offline, origin-bound robots.txt audit of a URL inventory.

No HTTP, DNS, or crawler requests. A robots rule is not an indexability verdict.
Run with PYTHONPATH=research/worker_a/c318 python research/worker_a/c330/offline_robots_inventory_audit.py ...
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from robots_gate import MAX_BYTES, decide

MAX_URLS = 50000
MAX_CLICKS = 10**9
_HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
_BAD_CHARS = frozenset('\\')


def _clean_url(raw: str):
    if not isinstance(raw, str) or not raw or any(ord(c) <= 32 or ord(c) == 127 or c in _BAD_CHARS for c in raw):
        raise ValueError('empty URL or raw whitespace/control/backslash')
    try:
        parsed = urlsplit(raw)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError(f'bad URL: {exc}') from exc
    return parsed


def _origin(raw: str):
    p = _clean_url(raw)
    if (p.scheme.lower() not in ('http', 'https') or not p.netloc or not p.hostname
            or p.username is not None or p.password is not None or p.path not in ('', '/')
            or p.query or p.fragment):
        raise ValueError('origin must be http(s) scheme + host + optional port, without credentials, query or fragment')
    host = p.hostname.lower()
    if len(host) > 253 or any(not _HOST_LABEL.fullmatch(label) for label in host.split('.')):
        raise ValueError('origin must use a valid ASCII hostname')
    port = p.port if p.port is not None else (443 if p.scheme.lower() == 'https' else 80)
    if port == 0:
        raise ValueError('origin port must be nonzero')
    return (p.scheme.lower(), host, port)


def _inventory_target(raw: str, origin: tuple[str, str, int]):
    """Return normalized origin-relative target or a reason for abstention."""
    try:
        p = _clean_url(raw)
        if p.scheme or p.netloc:
            if p.scheme.lower() not in ('http', 'https') or not p.hostname or p.username is not None or p.password is not None:
                raise ValueError('unsupported absolute URL')
            item_origin = (p.scheme.lower(), p.hostname.lower(), p.port if p.port is not None else (443 if p.scheme.lower() == 'https' else 80))
            if item_origin[2] == 0:
                raise ValueError('URL port must be nonzero')
            if item_origin != origin:
                raise ValueError('URL belongs to a different origin')
        elif not raw.startswith('/') or raw.startswith('//'):
            raise ValueError('relative inventory item must start with one slash')
        if p.fragment or '#' in raw:
            raise ValueError('fragment not supported in inventory URL')
        target = (p.path or '/') + (('?' + p.query) if p.query else '')
        if not target.startswith('/') or len(target) > 8192:
            raise ValueError('invalid or oversized URL path')
        return target, None
    except ValueError as exc:
        return None, str(exc)


def audit(robots: str, origin: str, product_token: str, inventory: list[dict]):
    normalized_origin = _origin(origin)
    if not isinstance(robots, str) or len(robots.encode('utf-8')) > MAX_BYTES:
        raise ValueError('robots content must be UTF-8 text at most 500 KiB')
    if not isinstance(inventory, list) or len(inventory) > MAX_URLS:
        raise ValueError('inventory must be a JSON array of at most 50000 entries')
    # Invalid token must not be disguised as 50000 per-row errors.
    if decide('', product_token, '/').status == 'unknown':
        raise ValueError('invalid user-agent product token')
    rows, seen = [], set()
    duplicate_count = 0
    for i, item in enumerate(inventory, 1):
        if not isinstance(item, dict) or not isinstance(item.get('url'), str):
            raise ValueError(f'inventory row {i}: url string required')
        segment = item.get('segment', 'unassigned')
        clicks = item.get('organic_clicks_30d', 0)
        if not isinstance(segment, str) or not (1 <= len(segment) <= 80):
            raise ValueError(f'inventory row {i}: invalid segment')
        if type(clicks) is not int or not (0 <= clicks <= MAX_CLICKS):
            raise ValueError(f'inventory row {i}: organic_clicks_30d must be nonnegative integer <= 1e9')
        target, error = _inventory_target(item['url'], normalized_origin)
        if target is not None:
            if target in seen:
                duplicate_count += 1
                continue
            seen.add(target)
        decision = decide(robots, product_token, target) if target is not None else None
        status = decision.status if decision else ('out_of_scope' if error == 'URL belongs to a different origin' else 'unknown')
        rows.append({
            'url': item['url'], 'target': target, 'segment': segment,
            'organic_clicks_30d': clicks, 'status': status,
            'matched_rule': decision.rule if decision else None,
            'reason': decision.reason if decision else error,
        })
    counts = Counter(r['status'] for r in rows)
    segments = defaultdict(lambda: {'total': 0, 'allowed': 0, 'disallowed': 0, 'unknown': 0, 'out_of_scope': 0,
                                    'flagged_organic_clicks_30d': 0})
    for row in rows:
        s = segments[row['segment']]
        s['total'] += 1
        s[row['status']] += 1
        if row['status'] in ('disallowed', 'unknown'):
            s['flagged_organic_clicks_30d'] += row['organic_clicks_30d']
    flagged = sorted((r for r in rows if r['status'] in ('disallowed', 'unknown')),
                     key=lambda r: (-r['organic_clicks_30d'], r['url']))
    return {
        'scope': {'origin': f'{normalized_origin[0]}://{normalized_origin[1]}:{normalized_origin[2]}',
                  'product_token': product_token},
        'summary': {'input_rows': len(inventory), 'unique_rows': len(rows),
                    'duplicate_rows_ignored': duplicate_count,
                    'allowed': counts['allowed'], 'disallowed': counts['disallowed'],
                    'unknown': counts['unknown'], 'out_of_scope': counts['out_of_scope'],
                    'flagged_organic_clicks_30d': sum(r['organic_clicks_30d'] for r in flagged)},
        'segments': dict(sorted(segments.items())),
        'review_queue': flagged,
        'excluded_out_of_scope': [r for r in rows if r['status'] == 'out_of_scope'],
        'rows': rows,
        'interpretation': (
            'Offline robots.txt crawl-policy decision aid, not an indexing, ranking, '
            'traffic-loss, or Googlebot verdict. Organic clicks are user-supplied '
            'prioritization context, not estimated lost clicks. Unknown requires manual review. '
            'Out-of-scope URLs are excluded from flagged click totals.'
        ),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--origin', required=True, help='robots.txt origin, e.g. https://example.com')
    ap.add_argument('--user-agent', required=True, help='crawler product token, e.g. Googlebot')
    ap.add_argument('--robots-file', type=Path, required=True, help='locally saved robots.txt')
    ap.add_argument('--inventory', type=Path, required=True, help='JSON list of {url, segment, organic_clicks_30d}')
    ap.add_argument('--output', type=Path, required=True, help='destination JSON report')
    args = ap.parse_args(argv)
    raw = args.robots_file.read_bytes()
    if len(raw) > MAX_BYTES:
        ap.error('robots file exceeds 500 KiB')
    try:
        result = audit(raw.decode('utf-8'), args.origin, args.user_agent,
                       json.loads(args.inventory.read_text(encoding='utf-8')))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        ap.error(str(exc))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
