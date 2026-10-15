"""Research-only rolling-window witness for prospective XAU receipts.

Does not modify production journal.mjs, settleReceipt, or existing v1 receipts.
A witness proves overlap consistency, NOT source authenticity or outcome publication time.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

DAY = re.compile(r'^\d{4}-\d{2}-\d{2}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')


def _instant(value):
    if not isinstance(value, str) or not (value.endswith('Z') or re.search(r'[+-]\d\d:\d\d$', value)):
        raise ValueError('Explicit timestamp timezone required')
    try:
        x = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if x.tzinfo is None:
            raise ValueError('Missing timezone')
        return x.astimezone(dt.timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ValueError('Invalid timestamp') from exc


def _date(value):
    if not isinstance(value, str) or not DAY.fullmatch(value):
        raise ValueError('YYYY-MM-DD date required')
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Invalid date') from exc
    return value


def _price(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError('Invalid price')
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid price') from exc
    if not n.is_finite() or n <= 0:
        raise ValueError('Invalid price')
    return format(n.normalize(), 'f')


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()


def _rows(series):
    if not isinstance(series, list):
        raise ValueError('Expected rows list')
    out = {}
    for row in series:
        if not isinstance(row, dict):
            raise ValueError('Invalid row')
        day = _date(row.get('date'))
        price = _price(row.get('price'))
        if day in out:
            raise ValueError('Duplicate date: ' + day)
        out[day] = price
    return sorted(out.items())


def issue_witness(series, *, issued_at, source, raw_sha256, snapshot_received_at, horizon, tail_size=30):
    issued, received = _instant(issued_at), _instant(snapshot_received_at)
    if received > issued or (issued-received).total_seconds() > 3600:
        raise ValueError('Snapshot must precede issue by no more than one hour')
    if not isinstance(source, str) or not source.strip() or not SHA256.fullmatch(raw_sha256):
        raise ValueError('Missing source or raw snapshot hash')
    if horizon not in (1, 7, 30) or type(horizon) is not int:
        raise ValueError('Unsupported horizon')
    if type(tail_size) is not int or not 10 <= tail_size <= 90:
        raise ValueError('Tail size must be 10..90')
    rows = _rows(series)
    if len(rows) < tail_size or rows[-1][0] >= issued.date().isoformat():
        raise ValueError('Insufficient completed historical closes')
    tail = rows[-tail_size:]
    body = {'witnessVersion': 1, 'issuedAt': issued_at, 'source': source,
            'snapshotReceivedAt': snapshot_received_at, 'rawSha256': raw_sha256,
            'horizon': horizon, 'originDate': rows[-1][0], 'historyLength': len(rows),
            'tailHashes': [{'date': day, 'sha256': _hash({'date': day, 'price': price})} for day, price in tail]}
    return {**body, 'id': _hash(body)}


def assess_rolling_snapshot(witness, series, *, received_at, raw_sha256, min_overlap=10):
    """Return a cautious status; never claim a fully authenticated settlement."""
    if not isinstance(witness, dict):
        raise ValueError('Invalid witness')
    body = {k: v for k, v in witness.items() if k != 'id'}
    if witness.get('id') != _hash(body) or body.get('witnessVersion') != 1:
        raise ValueError('Witness integrity mismatch')
    received, issued = _instant(received_at), _instant(body['issuedAt'])
    if received <= issued or not SHA256.fullmatch(raw_sha256):
        raise ValueError('Invalid outcome snapshot metadata')
    if type(min_overlap) is not int or min_overlap < 1:
        raise ValueError('Invalid min_overlap')
    rows = _rows(series)
    if not rows:
        return {'status': 'quarantined', 'reason': 'empty_outcome_snapshot'}
    by_day = dict(rows)
    witness_dates = body['tailHashes']
    if len(witness_dates) != len({x['date'] for x in witness_dates}):
        raise ValueError('Duplicate witness dates')
    overlap = 0
    for item in witness_dates:
        day = _date(item['date'])
        if day in by_day:
            overlap += 1
            if _hash({'date': day, 'price': by_day[day]}) != item['sha256']:
                return {'status': 'quarantined', 'reason': 'historical_revision', 'date': day}
        elif rows[0][0] <= day <= rows[-1][0]:
            return {'status': 'quarantined', 'reason': 'interior_historical_gap', 'date': day}
    if overlap < min_overlap or body['originDate'] not in by_day:
        return {'status': 'quarantined', 'reason': 'insufficient_overlap_or_origin_missing', 'matched': overlap}
    future = [(day, price) for day, price in rows if day > body['originDate']]
    if len(future) < body['horizon']:
        return {'status': 'pending', 'matched': overlap, 'observedFuture': len(future), 'horizon': body['horizon']}
    day, price = future[body['horizon'] - 1]
    if day >= received.date().isoformat():
        return {'status': 'pending', 'reason': 'target_day_not_completed', 'targetDate': day}
    return {'status': 'provisional', 'targetDate': day, 'actual': price,
            'matched': overlap, 'outcomeReceivedAt': received_at, 'outcomeRawSha256': raw_sha256,
            'limitation': 'Overlap consistency only. Not proof of provider publication time or independent source authenticity.'}
