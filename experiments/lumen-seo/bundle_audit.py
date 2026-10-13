#!/usr/bin/env python3
"""Offline sitemap-index bundle integrity check and regression diff (stdlib only).

Manifest: {"index":"index.xml", "sitemaps":{"https://site/a.xml":"a.xml"}}.
Exit 0: valid/no critical removal; 1: mass removal; 2: incomplete/invalid input.
This validates *local* snapshots, not live HTTP or search indexing.
"""
import argparse
import gzip
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SM = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
XHTML = '{http://www.w3.org/1999/xhtml}'
LIMIT = 20 * 1024 * 1024
BAD_PERCENT = re.compile(r'%(?![0-9a-fA-F]{2})')


def canonical(raw):
    if not isinstance(raw, str) or not raw or raw != raw.strip() or BAD_PERCENT.search(raw):
        raise ValueError('invalid URL text or percent escape')
    if any(ch.isspace() or ord(ch) < 32 for ch in raw) or '\\' in raw:
        raise ValueError('invalid whitespace/control/backslash in URL')
    p = urlsplit(raw)
    if p.scheme.lower() not in ('http', 'https') or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError('expected absolute HTTP(S) URL without credentials or fragment')
    host = p.hostname.lower().encode('idna').decode('ascii')
    if ':' in host:
        host = '[' + host + ']'
    port = p.port
    if port and (p.scheme.lower(), port) not in (('http', 80), ('https', 443)):
        host += ':' + str(port)
    return urlunsplit((p.scheme.lower(), host, p.path or '/', p.query, ''))


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate manifest key: ' + key)
        result[key] = value
    return result


def within(base, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('manifest paths must be nonempty relative strings')
    path = (base / name).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError('missing or unsafe bundle file: ' + name)
    return path


def read_xml(path):
    if path.stat().st_size > LIMIT:
        raise ValueError('compressed/XML input too large')
    with (gzip.open(path, 'rb') if path.suffix.lower() == '.gz' else path.open('rb')) as f:
        data = f.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError('decompressed XML too large')
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('DTD/entities forbidden')
    return ET.fromstring(data), hashlib.sha256(path.read_bytes()).hexdigest()


def read_index(path):
    root, digest = read_xml(path)
    if root.tag != SM + 'sitemapindex' or not len(root):
        raise ValueError('expected nonempty sitemapindex')
    urls = set()
    for node in root:
        if node.tag != SM + 'sitemap':
            raise ValueError('unexpected index child')
        loc = node.findall(SM + 'loc')
        if len(loc) != 1 or len(loc[0]) or any(n.tag not in (SM+'loc', SM+'lastmod') for n in node):
            raise ValueError('invalid index entry')
        url = canonical(loc[0].text)
        if url in urls:
            raise ValueError('duplicate index source')
        urls.add(url)
    return urls, digest


def read_urlset(path):
    root, digest = read_xml(path)
    if root.tag != SM + 'urlset' or not len(root):
        raise ValueError('expected nonempty urlset')
    pages = {}
    for node in root:
        if node.tag != SM + 'url':
            raise ValueError('unexpected urlset child')
        loc = node.findall(SM + 'loc')
        if len(loc) != 1 or len(loc[0]):
            raise ValueError('invalid page loc')
        url = canonical(loc[0].text)
        if url in pages:
            raise ValueError('duplicate page URL')
        alts = {}
        for link in node.findall(XHTML + 'link'):
            if link.get('rel') == 'alternate':
                lang = (link.get('hreflang') or '').strip().lower()
                if not lang or lang in alts:
                    raise ValueError('duplicate/missing hreflang')
                alts[lang] = canonical(link.get('href'))
        pages[url] = alts
    return pages, digest


def audit_bundle(manifest):
    manifest = Path(manifest).resolve()
    if manifest.stat().st_size > LIMIT:
        raise ValueError('manifest too large')
    data = json.loads(manifest.read_text(encoding='utf-8'), object_pairs_hook=no_duplicate_keys)
    if not isinstance(data, dict) or set(data) != {'index', 'sitemaps'} or not isinstance(data['sitemaps'], dict):
        raise ValueError('manifest needs index and sitemaps mapping')
    base = manifest.parent
    index_file = within(base, data['index'])
    index_urls, index_sha = read_index(index_file)
    mapped = {}
    for raw_url, relative in data['sitemaps'].items():
        url = canonical(raw_url)
        if url in mapped:
            raise ValueError('duplicate canonical sitemap URL')
        mapped[url] = within(base, relative)
    if set(mapped) != index_urls:
        raise ValueError('incomplete sitemap bundle: missing=' + repr(sorted(index_urls-set(mapped))) + ' extra=' + repr(sorted(set(mapped)-index_urls)))
    if len(set(mapped.values())) != len(mapped) or index_file in mapped.values():
        raise ValueError('duplicate local child or index used as child')
    pages = {}
    evidence = []
    for url, path in sorted(mapped.items()):
        child, sha = read_urlset(path)
        for page, alts in child.items():
            if page in pages:
                raise ValueError('duplicate URL across sitemap children: ' + page)
            pages[page] = alts
        evidence.append({'source': url, 'path': str(path.relative_to(base)), 'sha256': sha})
    return {'pages': pages, 'sources': index_urls,
            'evidence': {'index_sha256': index_sha, 'children': evidence}}


def compare(before, after, allow_source_set_change=False, threshold=0.2, min_mass=5):
    if not 0 < threshold <= 1 or min_mass < 1:
        raise ValueError('invalid threshold')
    old_sources, new_sources = before['sources'], after['sources']
    drift = {'removed': sorted(old_sources-new_sources), 'added': sorted(new_sources-old_sources)}
    if (drift['removed'] or drift['added']) and not allow_source_set_change:
        raise ValueError('sitemap source set changed; explicit --allow-source-set-change required')
    old, new = before['pages'], after['pages']
    removed = sorted(set(old)-set(new))
    added = sorted(set(new)-set(old))
    hreflang_changes = [dict(page=p, language=lang, before=old[p].get(lang), after=new[p].get(lang))
                        for p in sorted(set(old)&set(new))
                        for lang in sorted(set(old[p])|set(new[p])) if old[p].get(lang) != new[p].get(lang)]
    mass = len(removed) >= min_mass and len(removed)/max(1, len(old)) >= threshold
    return {'status': 'compared', 'before_pages': len(old), 'after_pages': len(new),
            'removed_urls': removed, 'added_urls': added, 'hreflang_changes': hreflang_changes,
            'source_set_changes': drift, 'mass_removal_alert': mass,
            'severity': 'critical' if mass else ('warning' if removed or hreflang_changes or any(drift.values()) else 'info'),
            'evidence': {'before': before['evidence'], 'after': after['evidence']},
            'scope': 'local bundle completeness only; no live HTTP/indexing verification'}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before-bundle', required=True)
    p.add_argument('--after-bundle', required=True)
    p.add_argument('--allow-source-set-change', action='store_true')
    p.add_argument('--mass-threshold', type=float, default=0.2)
    p.add_argument('--min-mass', type=int, default=5)
    args = p.parse_args(argv)
    try:
        result = compare(audit_bundle(args.before_bundle), audit_bundle(args.after_bundle),
                         args.allow_source_set_change, args.mass_threshold, args.min_mass)
    except (ValueError, TypeError, KeyError, OSError, EOFError, ET.ParseError, UnicodeError, json.JSONDecodeError) as e:
        print(json.dumps({'status': 'invalid_input', 'error': str(e)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result['mass_removal_alert'] else 0


if __name__ == '__main__':
    sys.exit(main())
