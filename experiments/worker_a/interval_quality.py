"""Research-only proper interval scoring for prospective XAU/USD receipts.

Never authenticates a receipt, source, or publication timestamp. No model promotion.
For a central 80% interval, alpha=0.2 and misses cost 10x distance.
"""
from datetime import datetime, date, timezone
from math import isfinite
from statistics import mean
import json
import sys


def positive_number(value, name):
    if type(value) not in (int, float) or not isfinite(value) or value <= 0:
        raise ValueError(f'{name}: positive finite number required')
    return float(value)


def utc_instant(value):
    if not isinstance(value, str) or not (value.endswith('Z') or ('+' in value[10:] or '-' in value[10:])):
        raise ValueError('Explicit timezone required')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            raise ValueError('Timezone required')
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ValueError('Invalid timestamp') from exc


def iso_day(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError('YYYY-MM-DD required')
    try:
        d = date.fromisoformat(value)
        if d.isoformat() != value:
            raise ValueError('Noncanonical day')
        return d
    except ValueError as exc:
        raise ValueError('Invalid day') from exc


def interval_score(actual, lower, upper, alpha=0.2):
    y = positive_number(actual, 'actual')
    lo = positive_number(lower, 'lower')
    hi = positive_number(upper, 'upper')
    if lo > hi:
        raise ValueError('lower exceeds upper')
    if type(alpha) not in (float, int) or not isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be between 0 and 1')
    return (hi - lo) + (2 / alpha) * max(lo - y, 0) + (2 / alpha) * max(y - hi, 0)


def inspect_receipt(receipt):
    """Widths are observable at issue time; no outcomes or predictive skill inferred."""
    if not isinstance(receipt, dict):
        raise ValueError('receipt must be object')
    if type(receipt.get('horizon')) is not int or receipt['horizon'] not in (1, 7, 30):
        raise ValueError('unsupported horizon')
    if not isinstance(receipt.get('id'), str) or len(receipt['id']) != 64:
        raise ValueError('receipt ID required (not cryptographic verification)')
    issued = utc_instant(receipt.get('issuedAt'))
    origin = iso_day(receipt.get('originDate'))
    if origin >= issued.date():
        raise ValueError('origin must precede issue UTC date')
    point = positive_number(receipt.get('point'), 'point')
    lo = positive_number(receipt.get('lower'), 'lower')
    hi = positive_number(receipt.get('upper'), 'upper')
    base = positive_number(receipt.get('baseline'), 'baseline')
    if not lo <= point <= hi:
        raise ValueError('point outside interval')
    if not isinstance(receipt.get('source'), str) or not receipt['source'].strip():
        raise ValueError('source required')
    return {'id': receipt['id'], 'horizon': receipt['horizon'], 'source': receipt['source'],
            'originDate': str(origin), 'issuedAt': receipt['issuedAt'], 'model': receipt.get('model'),
            'point': point, 'baseline': base, 'widthUsd': hi - lo,
            'widthPctOfBaseline': 100 * (hi - lo) / base,
            'status': 'awaiting_verified_outcome',
            'limitation': 'Width only; receipt hash, data provenance, and timestamp are not independently authenticated.'}


def score_observation(receipt, outcome, alpha=0.2):
    """Score only a complete, source-matched *claimed* observation; status provisional.

    Caller must separately establish Git issuance anchor, source authenticity,
    raw snapshot hash, and the exact h-th future provider close.
    """
    inspect_receipt(receipt)
    if not isinstance(outcome, dict):
        raise ValueError('outcome object required')
    received = utc_instant(outcome.get('receivedAt'))
    issued = utc_instant(receipt['issuedAt'])
    if received <= issued:
        raise ValueError('outcome must be received after issue')
    target = iso_day(outcome.get('targetDate'))
    if not iso_day(receipt['originDate']) < target < received.date():
        raise ValueError('target must be after origin and a completed UTC day')
    if receipt.get('targetDate') is not None and target != iso_day(receipt['targetDate']):
        raise ValueError('target date mismatch')
    if outcome.get('source') != receipt['source']:
        raise ValueError('source mismatch: do not combine providers')
    actual = positive_number(outcome.get('actual'), 'actual')
    point, baseline = float(receipt['point']), float(receipt['baseline'])
    lo, hi = float(receipt['lower']), float(receipt['upper'])
    return {'id': receipt['id'], 'source': receipt['source'], 'horizon': receipt['horizon'],
            'modelVersion': receipt.get('modelVersion'), 'targetDate': str(target),
            'covered': lo <= actual <= hi, 'intervalScore': interval_score(actual, lo, hi, alpha),
            'scaledIntervalScore': interval_score(actual, lo, hi, alpha) / baseline,
            'widthPctOfBaseline': 100 * (hi - lo) / baseline,
            'pointAbsError': abs(point - actual), 'baselineAbsError': abs(baseline - actual),
            'status': 'provisional_unverified_provenance'}


def aggregate(scores):
    if not scores:
        raise ValueError('no outcomes: do not compute coverage or skill')
    ids = [s['id'] for s in scores]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate receipt ID')
    keys = {(s['source'], s['horizon'], s['modelVersion']) for s in scores}
    if len(keys) != 1:
        raise ValueError('cannot pool sources, horizons, or model versions')
    source, horizon, version = next(iter(keys))
    baseline = mean(s['baselineAbsError'] for s in scores)
    return {'n': len(scores), 'source': source, 'horizon': horizon, 'modelVersion': version,
            'coveragePct': 100 * mean(s['covered'] for s in scores),
            'meanWidthPctOfBaseline': mean(s['widthPctOfBaseline'] for s in scores),
            'meanScaledIntervalScore': mean(s['scaledIntervalScore'] for s in scores),
            'pointMAE': mean(s['pointAbsError'] for s in scores), 'baselineMAE': baseline,
            'pointSkillPct': 100 * (1 - mean(s['pointAbsError'] for s in scores) / baseline) if baseline > 0 else None,
            'status': 'descriptive_provisional_only',
            'limitations': ['No authentication of original issue or source publication time',
                            'Overlapping target windows may make observations dependent',
                            'No statistical confidence interval or live predictive-skill claim']}


if __name__ == '__main__':
    # Reads only user-supplied local receipt files; no network, no mutations.
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python interval_quality.py RECEIPT.json [...]')
    print(json.dumps([inspect_receipt(json.load(open(p, encoding='utf-8'))) for p in sys.argv[1:]], indent=2))
