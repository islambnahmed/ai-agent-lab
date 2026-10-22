"""Synthetic coverage experiment: 1500 replicates per scenario, fixed seed."""
import json
import math
import random
from dependence_audit import audit,ci_contains_zero

SEED=20261023
REPS=1500

def iid(rng,n):
    return [rng.gauss(0,1) for _ in range(n)]

def gold_regime(rng,n):
    rho=.75
    x=rng.gauss(0,1)
    out=[]
    for _ in range(n):
        x=rho*x+math.sqrt(1-rho*rho)*rng.gauss(0,1)
        out.append(x)
    return out

def seo_weekly(rng,n):
    return [0.9*weekly+0.45*rng.gauss(0,1)
            for weekly in (rng.gauss(0,1) for _ in range(n//7))
            for _ in range(7)]

def evaluate(name,generator,n,reps=REPS):
    rng=random.Random(SEED+len(name))
    counts=[0,0,0]
    absrho=0.;ratio=0.
    for _ in range(reps):
        x=generator(rng,n)
        a,b=audit(x,12),audit(x,20)
        counts[0]+=ci_contains_zero(a["iid_95_interval"])
        counts[1]+=ci_contains_zero(a["hac_95_interval"])
        counts[2]+=ci_contains_zero(b["hac_95_interval"])
        absrho+=abs(a["lag1_autocorrelation"])
        ratio+=a["hac_se"]/a["iid_se"]
    return {"scenario":name,"replicates":reps,"n_windows":n,
            "iid_coverage_pct":round(100*counts[0]/reps,2),
            "hac12_coverage_pct":round(100*counts[1]/reps,2),
            "hac20_coverage_pct":round(100*counts[2]/reps,2),
            "mean_abs_lag1_corr":round(absrho/reps,3),
            "mean_hac12_se_ratio":round(ratio/reps,3)}

if __name__=="__main__":
    print(json.dumps({"seed":SEED,"coverage_target_pct":95,
      "note":"Synthetic dependent paired losses, not live prices.",
      "scenarios":[evaluate("iid_control",iid,240),
                   evaluate("gold_like_persistent_regime",gold_regime,240),
                   evaluate("seo_like_weekly_effect",seo_weekly,210)]},indent=2))
