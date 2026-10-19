#!/usr/bin/env python3
"""Offline, dependency-free bilingual HTML SEO consistency audit.

Usage: python audit_bilingual_seo.py pages.json [--strict]
Manifest: [{"url":"https://example.test/ar/", "file":"ar.html"}, ...]
All file paths resolve relative to the manifest; no network requests are made.
"""
import argparse
from collections import defaultdict
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, urlunsplit

LANG = re.compile(r'^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$')


def norm_url(value):
    if not isinstance(value, str):
        return None
    try:
        p = urlsplit(value.strip())
        if p.scheme.lower() not in ('http', 'https') or not p.netloc or p.username or p.password:
            return None
        if p.fragment:
            return None
        # Preserve path and query: silently rewriting either risks false matches.
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', p.query, ''))
    except ValueError:
        return None


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = []
        self.in_title = False
        self.canonicals = []
        self.alternates = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        elif tag == 'title':
            self.in_title = True
        elif tag == 'link':
            rel = set((a.get('rel') or '').lower().split())
            if 'canonical' in rel:
                self.canonicals.append(a.get('href'))
            if 'alternate' in rel and a.get('hreflang'):
                self.alternates.append((a.get('hreflang'), a.get('href')))
        elif tag == 'meta' and (a.get('name') or '').lower() in ('robots', 'googlebot'):
            self.robots.append(a.get('content') or '')

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def audit(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    items = json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(items, list) or not items:
        raise ValueError('Manifest must be a nonempty JSON array')
    # Reject duplicate URL keys before touching any referenced file.
    seen_urls = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('file'), str):
            raise ValueError('Each manifest item needs url and file')
        url = norm_url(item.get('url'))
        if not url:
            raise ValueError('Manifest has an invalid absolute URL')
        if url in seen_urls:
            raise ValueError('Duplicate manifest URL: ' + url)
        seen_urls.add(url)
    pages = {}
    findings = []

    def emit(code, severity, url, detail):
        findings.append({'code': code, 'severity': severity, 'url': url, 'detail': detail})

    for item in items:
        url = norm_url(item.get('url'))
        source = (manifest_path.parent / item['file']).resolve()
        if not source.is_relative_to(manifest_path.parent):
            raise ValueError('HTML file must remain under manifest directory')
        doc = Extract()
        doc.feed(source.read_text(encoding='utf-8'))
        title = ' '.join(' '.join(doc.title).split())
        lang = (doc.lang or '').lower()
        if not LANG.fullmatch(lang):
            emit('INVALID_LANG', 'error', url, 'Missing/invalid html lang')
        if not title:
            emit('MISSING_TITLE', 'error', url, 'No nonempty <title>')
        if len(doc.canonicals) != 1:
            emit('CANONICAL_COUNT', 'error', url, f'Expected one canonical, got {len(doc.canonicals)}')
        canonical = norm_url(doc.canonicals[0]) if len(doc.canonicals) == 1 else None
        if len(doc.canonicals) == 1 and not canonical:
            emit('INVALID_CANONICAL', 'error', url, 'Canonical must be absolute HTTP(S) without fragment')
        if canonical and canonical != url:
            emit('NONSELF_CANONICAL', 'warning', url, f'Canonical points to {canonical}')
        noindex = any('noindex' in [x.strip().lower() for x in s.split(',')] for s in doc.robots)
        if noindex:
            emit('NOINDEX', 'warning', url, 'Page declares noindex')
        alternates = {}
        for code, target in doc.alternates:
            code = code.lower()
            target = norm_url(target)
            if code != 'x-default' and not LANG.fullmatch(code):
                emit('INVALID_HREFLANG', 'error', url, f'Invalid hreflang: {code}')
            if not target:
                emit('INVALID_ALTERNATE_URL', 'error', url, f'Invalid alternate for {code}')
                continue
            if code in alternates and alternates[code] != target:
                emit('CONFLICTING_HREFLANG', 'error', url, f'Multiple destinations for {code}')
            alternates[code] = target
        pages[url] = {'lang': lang, 'title': title, 'canonical': canonical,
                      'alternates': alternates, 'noindex': noindex}

    titles = defaultdict(list)
    for url, page in pages.items():
        if page['title']:
            titles[page['title'].casefold()].append(url)
    for urls in titles.values():
        if len(urls) > 1:
            for url in urls:
                emit('DUPLICATE_TITLE', 'warning', url, f'Title shared by {len(urls)} pages')

    for url, page in pages.items():
        if page['lang'] and page['alternates'].get(page['lang']) != url:
            emit('MISSING_SELF_HREFLANG', 'warning', url, 'Self-referencing hreflang missing')
        for locale, target in page['alternates'].items():
            if locale == 'x-default':
                continue
            if target not in pages:
                emit('UNVERIFIED_EXTERNAL_ALTERNATE', 'info', url, f'{locale} => {target} not in manifest')
                continue
            other = pages[target]
            if other['lang'] != locale:
                emit('HREFLANG_LANG_MISMATCH', 'error', url, f'{locale} targets html lang={other["lang"]!r}')
            if other['noindex']:
                emit('HREFLANG_NOINDEX', 'error', url, f'{locale} target declares noindex')
            if other['canonical'] != target:
                emit('HREFLANG_NONCANONICAL', 'error', url, f'{locale} target is not self-canonical')
            if page['lang'] and other['alternates'].get(page['lang']) != url:
                emit('HREFLANG_NOT_RECIPROCAL', 'error', url, f'{locale} target lacks reciprocal {page["lang"]} => {url}')
    findings.sort(key=lambda f: (f['url'], f['code'], f['detail']))
    return {'pages': len(pages), 'errors': sum(f['severity'] == 'error' for f in findings),
            'warnings': sum(f['severity'] == 'warning' for f in findings), 'findings': findings,
            'caveat': 'Offline manifest-only check; does not validate live HTTP responses, crawling, robots.txt, or search rankings.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--strict', action='store_true', help='Exit nonzero if audit has errors')
    args = parser.parse_args()
    try:
        report = audit(args.manifest)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({'fatal': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.strict and report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
