"""Offline, origin-scoped robots.txt decisions. No HTTP fetches or crawler actions.

A robots file is only authoritative for its own scheme, host and effective port.
Ambiguous URLs or missing fetch evidence result in UNKNOWN, never ALLOWED.
This deliberately bounded validator does not implement DNS/IDNA resolution,
redirects, fetch caching, or HTTP status policies.
"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address, IPv4Address, IPv6Address
import re
from urllib.parse import urlsplit

from robots_gate import decide

_HOST_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")


@dataclass(frozen=True)
class ScopedDecision:
    status: str  # allowed, disallowed, unknown
    fetch_state: str  # fetched, unavailable, unreachable, not_fetched, invalid
    origin: str | None
    group: str | None
    rule: str | None
    reason: str


def _origin_and_url(url: str) -> tuple[str, object]:
    if not isinstance(url, str) or not url or any(c.isspace() or ord(c) < 32 for c in url):
        raise ValueError('URL must be an absolute URL without whitespace/control characters')
    if '\\' in url:
        raise ValueError('backslash in URL is ambiguous')
    if '#' in url:
        raise ValueError('URL fragment is not permitted in this decision contract')
    try:
        parts = urlsplit(url)
        if parts.scheme not in ('http', 'https') or not parts.netloc:
            raise ValueError('only absolute HTTP(S) URLs are supported')
        if '@' in parts.netloc or parts.username is not None or parts.password is not None:
            raise ValueError('credentials are not supported in URL authority')
        if parts.netloc.endswith(':'):
            raise ValueError('empty explicit port')
        hostname = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise ValueError('invalid URL authority: ' + str(exc)) from exc
    if not hostname or '%' in parts.netloc:
        raise ValueError('missing or percent-encoded host')
    if any(ord(c) > 127 for c in hostname):
        raise ValueError('non-ASCII host requires external IDNA verification')
    if hostname.endswith('.'):
        raise ValueError('trailing-dot host requires external normalization')
    try:
        ip = ip_address(hostname)
    except ValueError:
        if not all(_HOST_LABEL.fullmatch(label) for label in hostname.split('.')):
            raise ValueError('unsupported DNS host spelling')
        if hostname.replace('.', '').isdigit():
            raise ValueError('ambiguous numeric host')
        normalized = hostname.lower()
    else:
        if isinstance(ip, IPv6Address):
            if not parts.netloc.startswith('['):
                raise ValueError('IPv6 host must be bracketed')
            normalized = f'[{ip.compressed}]'
        else:
            normalized = str(ip)
    if port is None:
        port = 80 if parts.scheme == 'http' else 443
    if port < 1 or port > 65535:
        raise ValueError('invalid port')
    return f'{parts.scheme}://{normalized}:{port}', parts


def decide_scoped(robots: str | None, product_token: str,
                  robots_url: str, target_url: str,
                  *, fetch_state: str = 'fetched') -> ScopedDecision:
    """Decide only when both URLs share an exact web origin and robots is fetched.

    Fetch states are *evidence labels*, not HTTP policy decisions. In particular,
    unavailable/unreachable are UNKNOWN until a crawler-specific policy exists.
    """
    if fetch_state not in ('fetched', 'unavailable', 'unreachable', 'not_fetched'):
        return ScopedDecision('unknown', 'invalid', None, None, None, 'invalid fetch state')
    try:
        robots_origin, robots_parts = _origin_and_url(robots_url)
        target_origin, _ = _origin_and_url(target_url)
        if robots_parts.path != '/robots.txt' or '?' in robots_url:
            raise ValueError('robots source must be the origin-root /robots.txt without query')
        if robots_origin != target_origin:
            raise ValueError('robots source and target have different origins')
    except ValueError as exc:
        return ScopedDecision('unknown', fetch_state, None, None, None, str(exc))
    if fetch_state != 'fetched':
        return ScopedDecision('unknown', fetch_state, robots_origin, None, None,
                              f'robots fetch state {fetch_state}: no authoritative body to evaluate')
    if not isinstance(robots, str):
        return ScopedDecision('unknown', 'fetched', robots_origin, None, None,
                              'fetched state requires a robots text body')
    result = decide(robots, product_token, target_url)
    return ScopedDecision(result.status, 'fetched', robots_origin,
                          result.group, result.rule, result.reason)
