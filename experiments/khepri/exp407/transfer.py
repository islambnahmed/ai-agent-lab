"""Transfer check on ordinary-range synthetic gold prices and SEO traffic."""
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.gold_walkforward import predict_drift
from stable_drift import predict_drift_stable


def run():
    rng = random.Random(407)
    summary={}
    for label, base, daily_mu, daily_sigma in (
        ('gold_synthetic', 2200., .0003, .009),
        ('seo_traffic_synthetic', 10000., .001, .04),
    ):
        series=[base]
        for _ in range(600):
            series.append(series[-1] * math.exp(rng.gauss(daily_mu, daily_sigma)))
        errors=[]
        for origin in range(100, len(series), 5):
            for horizon in (1,7,30):
                old=predict_drift(series[:origin],horizon)
                new=predict_drift_stable(series[:origin],horizon)
                errors.append(abs(new/old-1))
        summary[label]={"comparisons":len(errors),"max_relative_change":max(errors),
                        "mean_relative_change":sum(errors)/len(errors)}
    return summary


if __name__=='__main__':
    print(json.dumps(run(),indent=2))
