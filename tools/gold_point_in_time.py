"""Point-in-time gold backtest. CSV: date,close,available_at (ISO offset-aware).
Only prices already published at the prediction cutoff can enter training.
Horizon and stride count observations, not calendar days. No accuracy claims.
"""
import argparse
import csv
import datetime as dt
import json
import math
import statistics

def parse_timestamp(value):
    stamp = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError('available_at must contain a UTC offset')
    return stamp.astimezone(dt.timezone.utc)

def validate(rows):
    rows = sorted(rows, key=lambda x: x[0])
    if len(rows) < 3:
        raise ValueError('At least three rows required')
    for i, (day, close, available) in enumerate(rows):
        if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
            raise ValueError('date must be a date')
        if not math.isfinite(close) or close <= 0:
            raise ValueError('close must be positive and finite')
        if not isinstance(available, dt.datetime) or available.tzinfo is None or available.utcoffset() is None:
            raise ValueError('available_at must be timezone aware')
        if available.date() < day:
            raise ValueError('release cannot precede observation date')
        if i and day == rows[i-1][0]:
            raise ValueError('duplicate observation date')
    return rows

def load_rows(path):
    with open(path, newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not {'date', 'close', 'available_at'}.issubset(reader.fieldnames or []):
            raise ValueError('Required columns: date,close,available_at')
        rows = [(dt.date.fromisoformat(r['date']), float(r['close']), parse_timestamp(r['available_at'])) for r in reader]
    return validate(rows)

def evaluate(rows, horizon=7, train_min=120, stride=None):
    if not all(type(v) is int for v in (horizon, train_min)) or horizon < 1 or train_min < 2:
        raise ValueError('invalid horizon or train_min')
    if stride is None:
        stride = horizon
    if type(stride) is not int or stride < horizon:
        raise ValueError('stride must be an integer >= horizon')
    rows = validate(rows)
    out = []
    skipped = 0
    for i in range(train_min - 1, len(rows) - horizon, stride):
        target = rows[i + horizon]
        cutoff = rows[i][2].astimezone(dt.timezone.utc)
        if target[2].astimezone(dt.timezone.utc) <= cutoff:
            skipped += 1
            continue
        train = [(j, r[1]) for j, r in enumerate(rows[:i+1]) if r[2].astimezone(dt.timezone.utc) <= cutoff]
        if len(train) < train_min:
            skipped += 1
            continue
        last_index, last_price = train[-1]
        steps = i + horizon - last_index
        growth = statistics.mean(math.log(b[1] / a[1]) for a, b in zip(train, train[1:]))
        try:
            candidate = last_price * math.exp(growth * steps)
        except OverflowError:
            skipped += 1
            continue
        if not math.isfinite(candidate):
            skipped += 1
            continue
        out.append({
            'origin_date': rows[i][0].isoformat(),
            'cutoff_utc': cutoff.isoformat(),
            'target_date': target[0].isoformat(),
            'last_observed_date': rows[last_index][0].isoformat(),
            'baseline': last_price,
            'candidate': candidate,
            'actual': target[1],
            'baseline_abs_error': abs(last_price - target[1]),
            'candidate_abs_error': abs(candidate - target[1]),
        })
    if not out:
        return {'status': 'insufficient_eligible_windows', 'windows': 0, 'skipped': skipped, 'results': []}
    baseline_mae = statistics.mean(r['baseline_abs_error'] for r in out)
    candidate_mae = statistics.mean(r['candidate_abs_error'] for r in out)
    return {
        'status': 'evaluation_ready' if len(out) >= 20 else 'descriptive_only',
        'windows': len(out), 'skipped': skipped,
        'baseline_mae': baseline_mae,
        'candidate_mae': candidate_mae,
        'improvement_pct': (baseline_mae - candidate_mae) / baseline_mae * 100 if baseline_mae else None,
        'warning': 'Publication timestamps must be source-verified; no accuracy claim without untouched holdout.',
        'results': out,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_path')
    parser.add_argument('--horizon', type=int, default=7)
    parser.add_argument('--train-min', type=int, default=120)
    parser.add_argument('--stride', type=int)
    args = parser.parse_args()
    print(json.dumps(evaluate(load_rows(args.csv_path), args.horizon, args.train_min, args.stride), indent=2))

if __name__ == '__main__':
    main()
