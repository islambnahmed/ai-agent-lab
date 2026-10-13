#!/usr/bin/env python3
"""Offline hreflang-cluster consistency check for local XML/XML.GZ sitemaps."""
import argparse
import gzip
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
XHTML = '{http://www.w3.org/1999/xhtml}'
LIMIT = 20 * 1024 * 1024


def canonical(raw):
    u = urlsplit(raw.strip())
    if u.scheme.lower() not in ('http', 'https') or not u.hostname or u.username or u.password:
        raise ValueError('absolute HTTP(S) URL without credentials required')
    host = u.hostname.lower().encode('idna').decode('ascii')
    if ':' in host:  # urlsplit removes IPv6 brackets
        host = '[' + host + ']'
    port = u.port
    authority = host + (f':{port}' if port and (u.scheme.lower(), port) not in [('http', 80), ('https', 443)] else '')
    return urlunsplit((u.scheme.lower(), authority, u.path or '/', u.query, ''))


def audit(files):
    issues, declared, seen = [], {}, set()

    def flag(severity, code, source, detail):
        issues.append(dict(severity=severity, code=code, source=source, detail=detail))

    for path in files:
        path = Path(path)
        if str(path.resolve()) in seen:
            flag('warning', 'duplicate_input', str(path), 'already loaded')
            continue
        seen.add(str(path.resolve()))
        try:
            if path.stat().st_size > LIMIT:
                raise ValueError('compressed/file size limit exceeded')
            with (gzip.open(path, 'rb') if path.suffix.lower() == '.gz' else path.open('rb')) as f:
                raw = f.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise ValueError('uncompressed size limit exceeded')
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise ValueError('DTD and entity declarations prohibited')
            root = ET.fromstring(raw)
            if root.tag != NS + 'urlset':
                raise ValueError('expected urlset; pass child XML files, not sitemapindex')
        except (OSError, EOFError, ET.ParseError, ValueError) as exc:
            flag('error', 'invalid_input', str(path), str(exc))
            continue
        for page in root.findall(NS + 'url'):
            try:
                loc = canonical(page.findtext(NS + 'loc') or '')
            except ValueError as exc:
                flag('error', 'invalid_loc', str(path), str(exc))
                continue
            if loc in declared:
                flag('error', 'duplicate_loc', loc, str(path))
                continue
            links = {}
            for el in page.findall(XHTML + 'link'):
                if el.get('rel') != 'alternate':
                    continue
                lang = (el.get('hreflang') or '').strip().lower()
                try:
                    href = canonical(el.get('href') or '')
                except ValueError:
                    flag('error', 'invalid_alternate', loc, lang)
                    continue
                if not lang or lang in links:
                    flag('error', 'duplicate_or_missing_language', loc, lang)
                links[lang] = href
            declared[loc] = links

    pairs = set()
    for source, links in sorted(declared.items()):
        if not links:
            continue
        if source not in links.values():
            flag('warning', 'missing_self_alternate', source, 'no self URL in hreflang set')
        for target in sorted(set(links.values())):
            if target not in declared:
                flag('warning', 'target_not_in_inputs', source, target)
                continue
            if source not in declared[target].values():
                flag('error', 'nonreciprocal', source, target)
            if target == source:
                continue
            pair = tuple(sorted((source, target)))
            if pair in pairs:
                continue
            pairs.add(pair)
            peer = declared[target]
            if links != peer:
                flag('warning', 'inconsistent_cluster', source, target)
            a, b = defaultdict(set), defaultdict(set)
            for language, url in links.items():
                if language != 'x-default':
                    a[url].add(language)
            for language, url in peer.items():
                if language != 'x-default':
                    b[url].add(language)
            for url in sorted(a.keys() & b.keys()):
                if a[url] != b[url]:
                    flag('error', 'language_conflict', source,
                         f'{url}: {sorted(a[url])} vs {sorted(b[url])}')
    issues.sort(key=lambda x: (x['severity'], x['code'], x['source'], x['detail']))
    return {'scope': 'offline XML declarations only; no HTTP or indexation checks',
            'pages': len(declared), 'errors': sum(x['severity'] == 'error' for x in issues),
            'warnings': sum(x['severity'] == 'warning' for x in issues), 'issues': issues}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('sitemaps', nargs='+')
    args = p.parse_args()
    result = audit(args.sitemaps)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
