"""Strict cross-runtime JSON hashing profile: numeric tokens forbidden.

Only strings, booleans, null, arrays, and objects with ASCII letter-leading keys.
No Unicode normalization: distinct payload bytes remain distinct intents.
"""
import hashlib
import json
import re

KEY = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
DECIMAL = re.compile(r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$')
MAX_DEPTH = 24
MAX_NODES = 10000
MAX_BYTES = 1024 * 1024

class InvalidPayload(ValueError):
    pass


def canonical_decimal(s):
    if not isinstance(s, str) or not DECIMAL.fullmatch(s):
        raise InvalidPayload('invalid decimal string')
    sign = '-' if s.startswith('-') else ''
    unsigned = s.lstrip('-')
    whole, dot, fraction = unsigned.partition('.')
    fraction = fraction.rstrip('0')
    if not any(ch != '0' for ch in whole + fraction):
        return '0'
    return sign + whole + ('.' + fraction if fraction else '')


def canonical_bytes(value):
    count = [0]
    def check(v, depth):
        count[0] += 1
        if count[0] > MAX_NODES or depth > MAX_DEPTH:
            raise InvalidPayload('complexity limit')
        if v is None or isinstance(v, bool):
            return
        if isinstance(v, str):
            if any(0xD800 <= ord(c) <= 0xDFFF for c in v):
                raise InvalidPayload('unpaired surrogate')
            return
        if isinstance(v, list):
            for x in v:
                check(x, depth + 1)
            return
        if isinstance(v, dict):
            for k, x in v.items():
                if not isinstance(k, str) or not KEY.fullmatch(k):
                    raise InvalidPayload('unsafe object key')
                check(x, depth + 1)
            return
        raise InvalidPayload('JSON numbers and non-JSON types prohibited')
    check(value, 0)
    b = json.dumps(value, ensure_ascii=False, sort_keys=True,
                   separators=(',', ':')).encode('utf-8')
    if len(b) > MAX_BYTES:
        raise InvalidPayload('payload too large')
    return b


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def gold_payload(op_id, amount, currency='USD', note=''):
    return {'kind': 'gold.receipt.issue', 'id': op_id, 'amount': canonical_decimal(amount),
            'currency': currency, 'note': note}


def seo_payload(op_id, page, word_count, title):
    return {'kind': 'seo.page.publish', 'id': op_id, 'page': page,
            'wordCount': canonical_decimal(word_count), 'title': title}
