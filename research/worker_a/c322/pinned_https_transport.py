"""Experimental fail-closed, DNS/IP-pinned HTTPS transport for robots fetches.

No network is initiated at import. Call only with separately authorized origins.
Every resolution is checked before a socket is created; any non-global address
fails the entire lookup. A selected sockaddr is connected directly, avoiding
DNS re-resolution at connect time. TLS SNI/hostname verification uses the
original hostname. No proxies, cookies or automatic redirects are involved.

This is a defense-in-depth prototype, NOT a complete SSRF boundary: require
external egress firewall and reviewed origin authorization before live use.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urlsplit

from trusted_fetch_adapter import TransportResponse
from origin_gate import _origin_and_url


def vetted_addresses(host: str, port: int, *, resolver=None):
    """Return socket addresses only if *every* DNS answer is globally routable."""
    resolver = socket.getaddrinfo if resolver is None else resolver
    infos = resolver(host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    if not infos:
        raise ValueError('empty DNS result')
    candidates = []
    for family, socktype, proto, canon, sockaddr in infos:
        if family not in (socket.AF_INET, socket.AF_INET6) or socktype != socket.SOCK_STREAM:
            raise ValueError('unsupported DNS result family/type')
        if proto not in (0, socket.IPPROTO_TCP):
            raise ValueError('unsupported DNS protocol')
        if not isinstance(sockaddr, tuple) or len(sockaddr) < 2 or sockaddr[1] != port:
            raise ValueError('invalid DNS socket address')
        try:
            addr = ipaddress.ip_address(sockaddr[0])
        except ValueError as exc:
            raise ValueError('non-IP DNS socket address') from exc
        if addr.version != (4 if family == socket.AF_INET else 6):
            raise ValueError('DNS address family mismatch')
        if not addr.is_global or addr.is_multicast or addr.is_reserved or addr.is_unspecified:
            raise ValueError('non-global DNS address rejected')
        candidates.append((family, socktype, proto, sockaddr))
    return tuple(candidates)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, *, timeout, addresses, context):
        super().__init__(host, port, timeout=timeout, context=context)
        self._addresses = addresses

    def connect(self):
        # Avoid HTTPSConnection.connect(): it would re-resolve the hostname.
        last_error = None
        for family, socktype, proto, sockaddr in self._addresses:
            raw = socket.socket(family, socktype, proto)
            try:
                raw.settimeout(self.timeout)
                raw.connect(sockaddr)  # literal vetted IP, not DNS hostname
                self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
                return
            except (OSError, ssl.SSLError) as exc:
                last_error = exc
                raw.close()
        raise last_error or OSError('no vetted connection candidate')


def pinned_https_transport(url: str, timeout: float, max_body_bytes: int) -> TransportResponse:
    origin, parts = _origin_and_url(url)
    if parts.scheme != 'https':
        raise ValueError('HTTPS required')
    if not isinstance(max_body_bytes, int) or not 0 < max_body_bytes <= 1_048_576:
        raise ValueError('invalid size limit')
    host, port = parts.hostname, parts.port or 443
    addresses = vetted_addresses(host, port)
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    path = parts.path or '/'
    if parts.query:
        path += '?' + parts.query
    conn = _PinnedHTTPSConnection(host, port, timeout=timeout, addresses=addresses, context=context)
    try:
        conn.request('GET', path, headers={
            'Host': parts.netloc, 'User-Agent': 'AI-Agent-Lab-Robots-Verification/0.2',
            'Accept': 'text/plain', 'Accept-Encoding': 'identity', 'Connection': 'close',
        })
        response = conn.getresponse()
        headers = {k.lower(): v for k, v in response.getheaders()}
        length = headers.get('content-length')
        if length is not None and length.isdecimal() and int(length) > max_body_bytes:
            raise ValueError('declared body too large')
        if headers.get('content-encoding', 'identity').lower().strip() != 'identity':
            raise ValueError('encoded response unsupported')
        body = response.read(max_body_bytes + 1)
        if len(body) > max_body_bytes:
            raise ValueError('response body exceeds limit')
        return TransportResponse(int(response.status), url, headers, body)
    finally:
        conn.close()
