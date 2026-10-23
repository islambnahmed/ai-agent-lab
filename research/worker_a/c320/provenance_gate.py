"""Offline, fail-closed integrity and redirect-chain gate for robots.txt.

This checks *internal consistency* of a caller-supplied fetch record; it DOES
NOT prove that the caller actually fetched the bytes from the claimed origin.
Only a separately trusted fetch adapter can establish network provenance.
No network access, cache writes, or crawler operations occur here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import hmac
import re
from urllib.parse import urlsplit

from origin_gate import _origin_and_url, decide_scoped

_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class RedirectHop:
    source_url: str
    status_code: int
    location_url: str  # Already resolved absolute URL, as recorded by fetch adapter.


@dataclass(frozen=True)
class RobotsFetchRecord:
    requested_url: str
    final_url: str
    redirects: tuple[RedirectHop, ...]
    status_code: int
    body: bytes
    body_sha256: str
    fetched_at: datetime


@dataclass(frozen=True)
class ProvenanceDecision:
    status: str  # allowed, disallowed, unknown
    reason: str
    origin: str | None
    body_sha256: str | None
    chain_length: int
    evidence_consistent: bool


def _reject(reason: str, chain_length: int = 0) -> ProvenanceDecision:
    return ProvenanceDecision('unknown', reason, None, None, chain_length, False)


def evaluate_record(record: RobotsFetchRecord, product_token: str, target_url: str,
                    *, now: datetime, max_age_seconds: int = 86400,
                    max_redirects: int = 5) -> ProvenanceDecision:
    """Evaluate only self-consistent, fresh, same-origin, HTTP-200 evidence.

    A redirect across origins, stale body, broken hop, or ambiguous URL yields
    UNKNOWN. The returned status is *not* permission to crawl: authorization
    and trusted HTTP evidence remain the responsibility of the caller.
    """
    if not isinstance(record, RobotsFetchRecord):
        return _reject('missing structured fetch record')
    if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds <= 0:
        return _reject('invalid max age')
    if not isinstance(max_redirects, int) or isinstance(max_redirects, bool) or not 0 <= max_redirects <= 20:
        return _reject('invalid redirect bound')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        return _reject('now must be timezone-aware')
    if not isinstance(record.fetched_at, datetime) or record.fetched_at.tzinfo is None or record.fetched_at.utcoffset() is None:
        return _reject('fetched_at must be timezone-aware')
    age = (now - record.fetched_at).total_seconds()
    if age < 0:
        return _reject('fetch timestamp is in the future')
    if age > max_age_seconds:
        return _reject('fetch record is stale')
    if not isinstance(record.redirects, tuple) or len(record.redirects) > max_redirects:
        return _reject('redirect chain missing or too long')
    if not isinstance(record.status_code, int) or isinstance(record.status_code, bool) or record.status_code != 200:
        return _reject('final HTTP status is not verified 200', len(record.redirects))
    if not isinstance(record.body, bytes):
        return _reject('body must contain exact fetched bytes', len(record.redirects))
    if not isinstance(record.body_sha256, str) or not _DIGEST.fullmatch(record.body_sha256):
        return _reject('invalid SHA-256 digest', len(record.redirects))
    actual_digest = hashlib.sha256(record.body).hexdigest()
    if not hmac.compare_digest(actual_digest, record.body_sha256):
        return _reject('body hash mismatch', len(record.redirects))
    try:
        robots_text = record.body.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        return _reject('body is not valid UTF-8', len(record.redirects))
    try:
        source_origin, source_parts = _origin_and_url(record.requested_url)
        target_origin, _ = _origin_and_url(target_url)
        if source_parts.path != '/robots.txt' or '?' in record.requested_url:
            raise ValueError('requested URL must be origin-root /robots.txt without query')
        if source_origin != target_origin:
            raise ValueError('target origin does not match requested origin')
        cursor = record.requested_url
        seen = {cursor}
        for hop in record.redirects:
            if not isinstance(hop, RedirectHop) or hop.source_url != cursor:
                raise ValueError('redirect chain has a missing or altered link')
            if not isinstance(hop.status_code, int) or isinstance(hop.status_code, bool) or hop.status_code not in _REDIRECT_STATUSES:
                raise ValueError('non-redirect HTTP status inside chain')
            hop_origin, _ = _origin_and_url(hop.location_url)
            if hop_origin != source_origin:
                raise ValueError('cross-origin redirect: conservative abstention')
            if hop.location_url in seen:
                raise ValueError('redirect loop')
            cursor = hop.location_url
            seen.add(cursor)
        final_origin, _ = _origin_and_url(record.final_url)
        if cursor != record.final_url or final_origin != source_origin:
            raise ValueError('final URL is not the redirect-chain destination')
    except (ValueError, TypeError, AttributeError) as exc:
        return _reject(str(exc), len(record.redirects))
    # We pass the ORIGINAL root robots URL to the scoped evaluator. Same-origin
    # redirects may end at a different path, but their rules still apply to the
    # original origin, not to a path/origin inferred from the final URL.
    decision = decide_scoped(robots_text, product_token, record.requested_url, target_url)
    return ProvenanceDecision(decision.status, decision.reason, source_origin,
                              actual_digest, len(record.redirects), True)
