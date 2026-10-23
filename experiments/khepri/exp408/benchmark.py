"""Fixed-seed metamorphic test on two synthetic series families and five scales."""
import datetime as dt
import json
import math
import random
from decimal import Decimal, localcontext
from pathlib import Path
from metric_audit import summarize
from tools.gold_walkforward import backtest


def decimal_rmse(rows):
    with localcontext() as ctx:
        ctx.prec = 80
        errs = [Decimal.from_float(c) - Decimal.from_float(a) for b, c, a in rows]
        return float((sum(e*e for e in errs) / Decimal(len(errs))).sqrt())


def run():
    rng = random.Random(408)
    scales = (1e-170, 1e-100, 1.0, 1e100, 1e170)
    families = {'gold': 2100., 'seo': 90000.}
    report = {'seed': 408, 'trajectories_per_family': 200, 'scales': scales, 'per_family': {}}
    for family, initial in families.items():
        data = {str(scale): {'runs': 0, 'upstream_crashes': 0, 'upstream_direction_mismatches': 0,
                             'upstream_rmse_zero_while_nonzero': 0, 'candidate_direction_mismatches': 0,
                             'candidate_decimal_rmse_relerr_max': 0.} for scale in scales}
        for _ in range(200):
            growth = rng.uniform(.0001, .005)
            base = [initial*(1. + growth*i) for i in range(6)]
            for scale in scales:
                rows = [(dt.date(2026, 1, 1) + dt.timedelta(days=i), v*scale) for i, v in enumerate(base)]
                k = str(scale)
                data[k]['runs'] += 1
                old = None
                try:
                    old = backtest(rows, horizon=1, train_min=2, stride=1)
                except (OverflowError, ValueError, ZeroDivisionError):
                    data[k]['upstream_crashes'] += 1
                    # Independent predictions for the candidate, not affected by old metric overflow.
                    from tools.gold_walkforward import predict_drift
                    records = [(rows[i][1], predict_drift([p for _, p in rows[:i+1]], 1), rows[i+1][1]) for i in range(1,5)]
                else:
                    records = [(r['baseline'], r['candidate'], r['actual']) for r in old['results']]
                fixed = summarize(records)
                exact_dirs = [((Decimal.from_float(c) > Decimal.from_float(b)) == (Decimal.from_float(a) > Decimal.from_float(b)) and c != b and a != b) for b,c,a in records]
                expected_accuracy = sum(exact_dirs)/len(exact_dirs)
                if fixed['candidate_direction_accuracy'] != expected_accuracy:
                    data[k]['candidate_direction_mismatches'] += 1
                if old is not None:
                    if old['candidate_direction_accuracy'] != expected_accuracy:
                        data[k]['upstream_direction_mismatches'] += 1
                    if old['candidate_rmse'] == 0 and fixed['candidate_rmse'] > 0:
                        data[k]['upstream_rmse_zero_while_nonzero'] += 1
                oracle = decimal_rmse(records)
                if oracle:
                    relative = abs(fixed['candidate_rmse'] - oracle)/oracle
                    data[k]['candidate_decimal_rmse_relerr_max'] = max(data[k]['candidate_decimal_rmse_relerr_max'], relative)
                old = None
        report['per_family'][family] = data
    return report


if __name__ == '__main__':
    result = run()
    target = Path(__file__).with_name('results.json')
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
