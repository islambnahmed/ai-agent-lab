"""Reproducible synthetic numerical stress test with high-precision oracle."""
import json
import math
import random
import sys
from decimal import Decimal, localcontext
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.gold_walkforward import predict_drift
from stable_drift import predict_drift_stable, ForecastRangeError


def oracle(first, last, length, horizon):
    with localcontext() as ctx:
        ctx.prec = 80
        dfirst, dlast = Decimal.from_float(first), Decimal.from_float(last)
        log_prediction = dlast.ln() + (dlast.ln() - dfirst.ln()) * Decimal(horizon) / Decimal(length-1)
        return float(log_prediction.exp())


def run(seed=407, trials=10000):
    rng = random.Random(seed)
    result = {"seed":seed, "trials":trials, "representable":0, "oracle_unrepresentable":0,
              "original_exception":0, "original_nonfinite_or_zero":0, "original_wrong_gt_1e_9":0,
              "stable_exception_when_representable":0, "stable_wrong_gt_1e_9":0,
              "stable_range_errors_when_unrepresentable":0,
              "original_failures_on_representable":0, "original_valid_on_representable":0,
              "original_max_relative_error":0.0, "stable_max_relative_error":0.0}
    examples=[]
    for k in range(trials):
        n = rng.randint(2,25)
        h = rng.randint(1,10)
        efirst = rng.uniform(-300,300)
        elast = rng.uniform(-300,300)
        first = 10.0 ** efirst
        last = 10.0 ** elast
        train = [first] + [10.0 ** rng.uniform(-300,300) for _ in range(n-2)] + [last]
        truth = oracle(first,last,n,h)
        valid = math.isfinite(truth) and truth > 0
        result['representable' if valid else 'oracle_unrepresentable'] += 1
        try:
            old = predict_drift(train,h)
            if not math.isfinite(old) or old <= 0:
                result['original_nonfinite_or_zero'] += 1
                if valid: result['original_failures_on_representable']+=1
            elif valid:
                result['original_valid_on_representable']+=1
                err=abs(old/truth-1)
                result['original_max_relative_error']=max(result['original_max_relative_error'],err)
                if err>1e-9: result['original_wrong_gt_1e_9']+=1
        except (ValueError, OverflowError, ZeroDivisionError):
            result['original_exception']+=1
            if valid: result['original_failures_on_representable']+=1
        try:
            new = predict_drift_stable(train,h)
            if valid:
                err=abs(new/truth-1)
                result['stable_max_relative_error']=max(result['stable_max_relative_error'],err)
                if err>1e-9:
                    result['stable_wrong_gt_1e_9']+=1
                    if len(examples)<5: examples.append({'trial':k,'first':first,'last':last,'n':n,'h':h,'truth':truth,'new':new,'error':err})
            else:
                if len(examples)<5: examples.append({'trial':k,'unexpected_finite':new})
        except ForecastRangeError:
            if valid:
                result['stable_exception_when_representable']+=1
                if len(examples)<5: examples.append({'trial':k,'unexpected_range_error':True,'truth':truth})
            else: result['stable_range_errors_when_unrepresentable']+=1
    result['exceptions_or_invalid_original'] = result['original_exception'] + result['original_nonfinite_or_zero']
    result['counterexamples']=examples
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
