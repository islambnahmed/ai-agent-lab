#!/usr/bin/env python3
"""Offline sitemap-index and URL-set QA; no network or external packages."""
from __future__ import annotations

import argparse
import csv
import os
import tempfile
import datetime as dt
import gzip
import json
from pathlib import Path
import re
import sys
import zlib
from urllib.parse import unquote, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_SITEMAPS = 200
MAX_ENTRIES = 50_000
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'


class ExportFailure(RuntimeError):
    """A CSV output failure must not be mislabeled as a sitemap read error."""


def _date(value: str, today: dt.date) -> str | None:
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            day = dt.date.fromisoformat(value)
        else:
            parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                return 'invalid_lastmod'
            day = parsed.astimezone(dt.timezone.utc).date()
        return 'future_lastmod' if day > today else None
    except ValueError:
        return 'invalid_lastmod'


def _normalize_url(raw: str) -> str | None:
    try:
        parts = urlsplit(raw.strip())
        if parts.scheme.lower() not in ('http', 'https') or not parts.hostname:
            return None
        if parts.username or parts.password or any(c.isspace() for c in raw):
            return None
        port = parts.port  # may raise ValueError
        host = parts.hostname.lower()
        if ':' in host:
            host = '[' + host + ']'
        default = (parts.scheme.lower() == 'https' and port == 443) or (parts.scheme.lower() == 'http' and port == 80)
        authority = host + (f':{port}' if port and not default else '')
        return urlunsplit((parts.scheme.lower(), authority, parts.path or '/', parts.query, ''))
    except ValueError:
        return None


def _local_target(raw: str, base: str, root: Path) -> Path | None:
    url = _normalize_url(raw)
    if not url:
        return None
    p, b = urlsplit(url), urlsplit(base)
    if p.scheme != b.scheme or p.netloc != b.netloc or p.query or p.fragment:
        return None
    # Never resolve external links or paths outside the supplied local directory.
    decoded = unquote(p.path)
    if '\\' in decoded or '\x00' in decoded or '%' in decoded:
        return None
    segments = decoded.lstrip('/').split('/')
    if not segments or any(s in ('', '.', '..') for s in segments):
        return None
    candidate = root.joinpath(*segments).resolve()
    if not candidate.is_relative_to(root):
        return None
    if candidate.suffix not in ('.xml', '.gz') or (candidate.suffix == '.gz' and not candidate.name.endswith('.xml.gz')):
        return None
    return candidate


def audit(root: Path, start: str, base_url: str, today: dt.date, *, max_sitemaps: int = MAX_SITEMAPS, on_url=None) -> dict:
    root = root.resolve()
    base = _normalize_url(base_url)
    if not root.is_dir() or not base or urlsplit(base).path != '/' or urlsplit(base).query:
        raise ValueError('root must be a directory; base URL must be an HTTP(S) origin')
    if max_sitemaps < 1 or max_sitemaps > MAX_SITEMAPS:
        raise ValueError('max_sitemaps must be 1..200')
    start_path = (root / start).resolve()
    if not start_path.is_relative_to(root) or start_path.suffix not in ('.xml', '.gz'):
        raise ValueError('start sitemap must be an XML file inside root')
    issues: list[dict] = []
    seen_urls: dict[str, str] = {}
    visited: set[Path] = set()
    active: set[Path] = set()
    summary = {'sitemaps': 0, 'urlsets': 0, 'indexes': 0, 'urls': 0, 'unique_urls': 0, 'issues': 0}

    def issue(code: str, file: Path, detail: str = '') -> None:
        issues.append({'code': code, 'file': file.relative_to(root).as_posix(), 'detail': detail})

    def walk(path: Path) -> None:
        if path in active:
            issue('index_cycle', path)
            return
        if path in visited:
            issue('repeated_sitemap', path)
            return
        if len(visited) >= max_sitemaps:
            issue('sitemap_limit', path)
            return
        visited.add(path)
        active.add(path)
        summary['sitemaps'] += 1
        try:
            if not path.is_file():
                issue('missing_sitemap', path)
                return
            if path.suffix == '.gz':
                with gzip.open(path, 'rb') as f:
                    payload = f.read(MAX_UNCOMPRESSED_BYTES + 1)
            else:
                with path.open('rb') as f:
                    payload = f.read(MAX_UNCOMPRESSED_BYTES + 1)
            if len(payload) > MAX_UNCOMPRESSED_BYTES:
                issue('oversized_sitemap', path)
                return
            if re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', payload, re.I):
                issue('xml_declaration_unsafe', path)
                return
            try:
                doc = ET.fromstring(payload)
            except ET.ParseError:
                issue('malformed_xml', path)
                return
            if doc.tag == NS + 'sitemapindex':
                summary['indexes'] += 1
                entries = doc.findall(NS + 'sitemap')
                # Wrong-namespace entries are otherwise silently skipped by findall.
                for child in doc:
                    if child.tag.rsplit('}', 1)[-1] == 'sitemap' and child.tag != NS + 'sitemap':
                        issue('wrong_entry_namespace', path, str(child.tag)[:200])
                if len(entries) > MAX_ENTRIES:
                    issue('entry_limit', path, str(len(entries)))
                    return
                for entry in entries:
                    loc = entry.findtext(NS + 'loc')
                    if not loc or not loc.strip():
                        issue('missing_loc', path)
                        continue
                    target = _local_target(loc, base, root)
                    if target is None:
                        issue('unmapped_index_loc', path, loc.strip()[:200])
                    else:
                        walk(target)
            elif doc.tag == NS + 'urlset':
                summary['urlsets'] += 1
                entries = doc.findall(NS + 'url')
                for child in doc:
                    if child.tag.rsplit('}', 1)[-1] == 'url' and child.tag != NS + 'url':
                        issue('wrong_entry_namespace', path, str(child.tag)[:200])
                if len(entries) > MAX_ENTRIES:
                    issue('entry_limit', path, str(len(entries)))
                    return
                for entry in entries:
                    summary['urls'] += 1
                    loc = entry.findtext(NS + 'loc')
                    if not loc or not loc.strip():
                        issue('missing_loc', path)
                        continue
                    norm = _normalize_url(loc)
                    if not norm:
                        issue('invalid_url', path, loc.strip()[:200])
                        continue
                    parsed_url, parsed_base = urlsplit(norm), urlsplit(base)
                    if parsed_url.netloc != parsed_base.netloc:
                        issue('off_host_url', path, norm[:200])
                    elif parsed_url.scheme != parsed_base.scheme:
                        issue('off_origin_url', path, norm[:200])
                    duplicate = norm in seen_urls
                    if duplicate:
                        issue('duplicate_url', path, norm[:200] + ' (first: ' + seen_urls[norm] + ')')
                    else:
                        seen_urls[norm] = path.relative_to(root).as_posix()
                    lastmod = entry.findtext(NS + 'lastmod')
                    if on_url is not None:
                        on_url(path.relative_to(root).as_posix(), norm, lastmod, duplicate)
                    if lastmod is not None:
                        code = _date(lastmod.strip(), today)
                        if code:
                            issue(code, path, norm[:200])
            else:
                issue('unexpected_root', path, doc.tag[:200])
        except (OSError, EOFError, ValueError, zlib.error) as exc:
            issue('unreadable_sitemap', path, type(exc).__name__)
        finally:
            active.remove(path)

    walk(start_path)
    summary['unique_urls'] = len(seen_urls)
    issues.sort(key=lambda i: (i['file'], i['code'], i['detail']))
    summary['issues'] = len(issues)
    return {'schema_version': 1, 'kind': 'offline_sitemap_inventory', 'base_url': base,
            'as_of': today.isoformat(), 'summary': summary, 'issues': issues,
            'limitations': ['No network fetch, HTTP status, robots.txt, canonical, noindex or search-index verification',
                            'Duplicate detection is URL-normalized but does not infer semantic canonical equivalence']}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--start', default='sitemap.xml')
    parser.add_argument('--base-url', required=True, help='HTTP(S) origin matching sitemap-index loc URLs')
    parser.add_argument('--as-of', default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument('--max-sitemaps', type=int, default=MAX_SITEMAPS)
    parser.add_argument('--urls-csv', type=Path, help='Optional atomic CSV export of valid URL entries, including duplicates')
    args = parser.parse_args(argv)
    temporary_csv = None
    try:
        today = dt.date.fromisoformat(args.as_of)
        if args.urls_csv is None:
            report = audit(args.root, args.start, args.base_url, today, max_sitemaps=args.max_sitemaps)
        else:
            destination = args.urls_csv
            if not destination.parent.is_dir():
                raise ValueError('CSV output parent directory must exist')
            # Stream rows rather than retaining an extra inventory in memory.
            # Only replace the requested output after the audit completes.
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                                             dir=destination.parent, prefix='.sitemap-audit-',
                                             suffix='.csv', delete=False) as stream:
                temporary_csv = Path(stream.name)
                writer = csv.writer(stream)
                writer.writerow(['source_sitemap', 'normalized_url', 'lastmod', 'duplicate'])
                def record_url(source, url, lastmod, duplicate):
                    try:
                        writer.writerow([source, url, lastmod or '', 'true' if duplicate else 'false'])
                    except (OSError, ValueError) as exc:
                        raise ExportFailure('CSV write failed') from exc
                report = audit(args.root, args.start, args.base_url, today,
                               max_sitemaps=args.max_sitemaps, on_url=record_url)
            os.replace(temporary_csv, destination)
            temporary_csv = None
    except (ValueError, OSError, ExportFailure) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    finally:
        if temporary_csv is not None:
            try:
                temporary_csv.unlink(missing_ok=True)
            except OSError:
                pass
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report['summary']['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
