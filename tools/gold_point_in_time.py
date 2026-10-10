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
        if available.astimezone(dt.timezone.utc).date() < day:
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
    skip_reasons = {'target_already_available': 0, 'insufficient_published_history': 0, 'nonfinite_forecast': 0}
    for i in range(train_min - 1, len(rows) - horizon, stride):
        target = rows[i + horizon]
        # Forecast at start of next UTC day, not at a potentially late release.
        cutoff = dt.datetime.combine(rows[i][0] + dt.timedelta(days=1), dt.time.min, tzinfo=dt.timezone.utc)
        if target[2].astimezone(dt.timezone.utc) <= cutoff:
            skip_reasons['target_already_available'] += 1
            skipped += 1
            continue
        train = [(j, r[1]) for j, r in enumerate(rows[:i+1]) if r[2].astimezone(dt.timezone.utc) <= cutoff]
        if len(train) < train_min:
            skip_reasons['insufficient_published_history'] += 1
            skipped += 1
            continue
        last_index, last_price = train[-1]
        steps = i + horizon - last_index
        # Published observations can be sparse; normalize by index distance.
        growth = math.log(last_price / train[0][1]) / (last_index - train[0][0])
        try:
            candidate = last_price * math.exp(growth * steps)
        except OverflowError:
            skip_reasons['nonfinite_forecast'] += 1
            skipped += 1
            continue
        if not math.isfinite(candidate):
            skip_reasons['nonfinite_forecast'] += 1
            skipped += 1
            continue
        out.append({
            'origin_date': rows[i][0].isoformat(),
            'cutoff_utc': cutoff.isoformat(),
            'target_date': target[0].isoformat(),
            'last_observed_date': rows[last_index][0].isoformat(),
            'origin_lag_observations': i - last_index,
            'baseline': last_price,
            'candidate': candidate,
            'actual': target[1],
            'baseline_abs_error': abs(last_price - target[1]),
            'candidate_abs_error': abs(candidate - target[1]),
        })
    attempted = len(out) + skipped
    stale_count = sum(r['origin_lag_observations'] > 0 for r in out)
    audit = {
        'attempted_windows': attempted,
        'coverage_pct': 100 * len(out) / attempted if attempted else 0.0,
        'skip_reasons': skip_reasons,
        'stale_origin_windows': stale_count,
        'stale_origin_pct': 100 * stale_count / len(out) if out else 0.0,
        'max_origin_lag_observations': max((r['origin_lag_observations'] for r in out), default=0),
    }
    if not out:
        return {'status': 'insufficient_eligible_windows', 'windows': 0, 'skipped': skipped, **audit, 'results': []}
    baseline_mae = statistics.mean(r['baseline_abs_error'] for r in out)
    candidate_mae = statistics.mean(r['candidate_abs_error'] for r in out)
    return {
        'status': 'evaluation_ready' if len(out) >= 20 and stale_count == 0 else 'descriptive_only',
        'windows': len(out), 'skipped': skipped, **audit,
        'baseline_mae': baseline_mae,
        'candidate_mae': candidate_mae,
        'improvement_pct': (baseline_mae - candidate_mae) / baseline_mae * 100 if baseline_mae else None,
        'warning': 'Raw MAE includes stale-origin windows. Use the quality-gate audit for fresh-only metrics; verify timestamps and untouched holdout.',
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
