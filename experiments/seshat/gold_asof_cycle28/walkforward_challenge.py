"""Retrospective pseudo-holdout stress test for Seshat's 26-month gold extract.

NOT a prospective or untouched test: these months were inspected in earlier lab
cycles. Historical publication timestamps are hypothetical; prices are rounded
secondary-source values, not verified official historical vintages.
"""
from datetime import date, datetime, timezone
from math import exp, isfinite, log
from statistics import mean
from point_in_time import load_observations, information_set

POLICIES = ("no_change", "endpoint", "trailing_3", "trailing_6", "trailing_12")

def month_gap(a, b):
    if a.day != 1 or b.day != 1:
        raise ValueError("Dates must be first of month")
    gap = (b.year-a.year)*12 + b.month-a.month
    if gap < 1:
        raise ValueError("Target must follow last known month")
    return gap

def forecast(observations, issued_at, target, policy):
    if policy not in POLICIES:
        raise ValueError("Unknown policy")
    if target.day != 1:
        raise ValueError("Target must be first of month")
    known = [o for o in information_set(list(observations), issued_at)
             if o.month < target]
    if len(known) < 2 or len(set(o.month for o in known)) != len(known):
        raise ValueError("Insufficient or duplicate history")
    prices = [o.price for o in known]
    if not all(isfinite(p) and p > 0 for p in prices):
        raise ValueError("Prices must be finite and positive")
    horizon = month_gap(known[-1].month, target)
    if policy == "no_change":
        slope = 0.0
    elif policy == "endpoint":
        slope = log(prices[-1]/prices[0])/month_gap(known[0].month, known[-1].month)
    else:
        lag = min(int(policy.split("_")[1]), len(known)-1)
        slope = log(prices[-1]/prices[-1-lag])/month_gap(known[-1-lag].month, known[-1].month)
        slope = max(-0.05, min(0.05, slope))
    return {"prediction": prices[-1]*exp(horizon*slope),
            "horizon": horizon, "latest_known_month": known[-1].month.isoformat()[:7]}

def score(observations, issue_day):
    if issue_day not in range(1,29):
        raise ValueError("Issue day outside 1..28")
    targets = list(observations)[12:]
    if len(targets) != 14 or len(set(o.month for o in observations)) != len(observations):
        raise ValueError("Expected 14 unique targets")
    rows = []
    for target in targets:
        issued = datetime(target.month.year,target.month.month,issue_day,tzinfo=timezone.utc)
        preds = {p: forecast(observations,issued,target.month,p) for p in POLICIES}
        rows.append({"month":target.month.isoformat()[:7],
                     "actual":target.price,
                     "horizon":preds["no_change"]["horizon"],
                     "latest_known_month":preds["no_change"]["latest_known_month"],
                     "abs_errors":{p:abs(target.price-v["prediction"]) for p,v in preds.items()}})
    train, pseudo_holdout = rows[:7], rows[7:]
    def mae(items,p):
        return mean(r["abs_errors"][p] for r in items)
    selected = min(POLICIES,key=lambda p:(mae(train,p),POLICIES.index(p)))
    return {"issue_day":issue_day,
            "training_months":[r["month"] for r in train],
            "pseudo_holdout_months":[r["month"] for r in pseudo_holdout],
            "selected_policy":selected,
            "training_mae":{p:round(mae(train,p),3) for p in POLICIES},
            "pseudo_holdout_mae":{p:round(mae(pseudo_holdout,p),3) for p in POLICIES},
            "selected_minus_nochange_mae":round(mae(pseudo_holdout,selected)-mae(pseudo_holdout,"no_change"),3),
            "rows":rows,
            "limitations":"Not an untouched holdout; hypothetical publication dates; rounded secondary data; seven months per split."}

def scenarios():
    return {"issue_day_1":score(load_observations(),1),
            "issue_day_3":score(load_observations(),3),
            "issue_day_3_extra_lag":score(load_observations(delay_months=1),3)}

if __name__ == "__main__":
    import json
    print(json.dumps(scenarios(),indent=2))
