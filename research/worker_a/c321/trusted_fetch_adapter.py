"""Opt-in, bounded HTTPS robots fetch with offline-testable transport boundary.

NOT a general crawler or proof of unforgeable provenance. This module makes
response bytes/timestamps/redirects originate from a transport call rather
than caller-supplied RobotsFetchRecord. Network is disabled by default.

The stdlib HTTPS transport uses certificate verification, disables environment
proxies and automatic redirects. Its DNS resolution is not IP-pinned: external
egress restrictions and a tightly managed origin allowlist are REQUIRED before
production deployment. No authorization to crawl follows from a robots result.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
from typing import Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import (build_opener, HTTPSHandler, HTTPRedirectHandler,
                            ProxyHandler, Request)
import ssl

from origin_gate import _origin_and_url
from provenance_gate import (RedirectHop, RobotsFetchRecord, ProvenanceDecision,
                             evaluate_record)

REDIRECTS = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    effective_url: str
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class FetchOutcome:
    status: str  # allowed, disallowed, unknown
    reason: str
    transport_kind: str  # test_double, stdlib_tls, none
    decision: ProvenanceDecision | None
    record: RobotsFetchRecord | None


def _unknown(reason: str, transport_kind: str = 'none') -> FetchOutcome:
    return FetchOutcome('unknown', reason, transport_kind, None, None)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def stdlib_https_transport(url: str, timeout: float, max_body_bytes: int) -> TransportResponse:
    """One HTTPS request, no implicit redirects, cookies or proxy inheritance.

    HTTPError is a response for non-2xx status, not an exception to conceal.
    This function is not an SSRF defense and does not pin resolved IPs.
    """
    if urlsplit(url).scheme != 'https':
        raise ValueError('HTTPS required')
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()),
                          _NoRedirect())
    req = Request(url, method='GET', headers={
        'User-Agent': 'AI-Agent-Lab-Robots-Verification/0.1',
        'Accept': 'text/plain', 'Accept-Encoding': 'identity',
    })
    try:
        response = opener.open(req, timeout=timeout)
    except HTTPError as exc:
        response = exc
    try:
        headers = {k.lower(): v for k, v in response.headers.items()}
        length = headers.get('content-length')
        if length is not None and length.isdecimal() and int(length) > max_body_bytes:
            raise ValueError('declared body too large')
        if headers.get('content-encoding', 'identity').lower().strip() != 'identity':
            raise ValueError('encoded response body unsupported')
        body = response.read(max_body_bytes + 1)
        if len(body) > max_body_bytes:
            raise ValueError('response body exceeds limit')
        return TransportResponse(int(response.code), response.geturl(), headers, body)
    finally:
        response.close()


def fetch_and_decide(target_url: str, product_token: str, *,
                     allowed_origins: frozenset[str], allow_network: bool = False,
                     transport: Callable[[str, float, int], TransportResponse] | None = None,
                     max_redirects: int = 5, max_body_bytes: int = 512_000,
                     timeout_seconds: float = 5.0) -> FetchOutcome:
    """Fetch robots for an explicitly allowed HTTPS origin, then decide.

    The optional transport is ONLY for controlled tests: it is never called
    'authenticated' and its evidence is marked test_double. The allowlist is
    an exact normalized origin string, e.g. https://example.org:443.
    """
    if not allow_network:
        return _unknown('network operation not explicitly enabled')
    if not isinstance(allowed_origins, frozenset) or not all(isinstance(x, str) for x in allowed_origins):
        return _unknown('invalid trusted origin allowlist')
    if not isinstance(max_redirects, int) or isinstance(max_redirects, bool) or not 0 <= max_redirects <= 5:
        return _unknown('invalid redirect limit')
    if not isinstance(max_body_bytes, int) or isinstance(max_body_bytes, bool) or not 0 < max_body_bytes <= 1_048_576:
        return _unknown('invalid body limit')
    if (not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 10):
        return _unknown('invalid timeout')
    try:
        origin, parts = _origin_and_url(target_url)
        if parts.scheme != 'https':
            raise ValueError('HTTPS-only transport')
        if origin not in allowed_origins:
            raise ValueError('origin is not explicitly authorized')
        if parts.hostname is None:
            raise ValueError('missing host')
        # Production egress MUST additionally enforce public destinations and
        # pin DNS/IP to avoid rebinding. This testable adapter cannot do that.
        root = origin + '/robots.txt'
        _origin_and_url(root)
    except (TypeError, ValueError, AttributeError) as exc:
        return _unknown(str(exc))

    chosen_transport = transport if transport is not None else stdlib_https_transport
    kind = 'test_double' if transport is not None else 'stdlib_tls'
    cursor, hops, seen = root, [], {root}
    for _ in range(max_redirects + 1):
        try:
            response = chosen_transport(cursor, float(timeout_seconds), max_body_bytes)
            if not isinstance(response, TransportResponse):
                raise ValueError('transport response type invalid')
            if response.effective_url != cursor:
                raise ValueError('transport performed an unrecorded redirect')
            if not isinstance(response.status_code, int) or isinstance(response.status_code, bool):
                raise ValueError('invalid HTTP status')
            if not isinstance(response.body, bytes) or len(response.body) > max_body_bytes:
                raise ValueError('invalid or oversized response bytes')
            if not isinstance(response.headers, Mapping):
                raise ValueError('invalid headers')
            headers = {str(k).lower(): v for k, v in response.headers.items()}
            if str(headers.get('content-encoding', 'identity')).lower().strip() != 'identity':
                raise ValueError('encoded response unsupported')
            if response.status_code in REDIRECTS:
                if len(hops) >= max_redirects:
                    raise ValueError('redirect limit exceeded')
                location = headers.get('location')
                if (not isinstance(location, str) or not location.strip()
                        or any(c.isspace() or ord(c) < 32 for c in location)
                        or '\\' in location or '#' in location):
                    raise ValueError('redirect without valid Location')
                destination = urljoin(cursor, location)
                new_origin, new_parts = _origin_and_url(destination)
                if new_origin != origin or new_parts.scheme != 'https':
                    raise ValueError('cross-origin or insecure redirect refused')
                if destination in seen:
                    raise ValueError('redirect loop')
                hops.append(RedirectHop(cursor, response.status_code, destination))
                seen.add(destination)
                cursor = destination
                continue
            if response.status_code != 200:
                raise ValueError(f'HTTP {response.status_code}: no authoritative 200 body')
            fetched_at = datetime.now(timezone.utc)
            body = response.body
            record = RobotsFetchRecord(root, cursor, tuple(hops), 200, body,
                                       hashlib.sha256(body).hexdigest(), fetched_at)
            decision = evaluate_record(record, product_token, target_url,
                                       now=datetime.now(timezone.utc), max_redirects=max_redirects)
            return FetchOutcome(decision.status, decision.reason, kind, decision, record)
        except (ValueError, TypeError, OSError, TimeoutError, ssl.SSLError) as exc:
            return _unknown(str(exc), kind)
    return _unknown('redirect traversal did not terminate', kind)
