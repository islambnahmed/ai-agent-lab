#!/usr/bin/env python3
"""Synthetic h=1 interval calibration stress test. No market data."""
import argparse, json, math, random, statistics, unittest

def order_quantile(errors, level=0.8):
    if not errors: raise ValueError("empty calibration")
    xs=sorted(abs(e) for e in errors)
    return xs[min(len(xs), math.ceil((len(xs)+1)*level))-1]

def widths_before(errors,t, fixed_end=250,rolling_window=80):
    if t<fixed_end or fixed_end<rolling_window: raise ValueError("invalid calibration")
    return order_quantile(errors[:fixed_end]),order_quantile(errors[t-rolling_window:t])

def simulate(seed, scenario, rho=0.0, n=800, shift_at=500):
    rng=random.Random(seed); errors=[]; last=0.0
    for t in range(n):
        sigma=1.0 if scenario=="stationary" or t<shift_at else 3.0
        last=rho*last+sigma*math.sqrt(1-rho*rho)*rng.gauss(0,1)
        errors.append(last)
    out={}
    for phase,start,end in [("pre_shift",300,500),("early_post",500,580),("late_post",650,800)]:
        for method in ("fixed","rolling"):
            hits=widths=0.0
            for t in range(start,end):
                f,r=widths_before(errors,t)
                width=f if method=="fixed" else r
                hits+=abs(errors[t])<=width
                widths+=width
            out[phase+"_"+method]=(hits/(end-start),widths/(end-start))
    return out

def aggregate(reps=400):
    result={"experiment":"synthetic h=1, absolute-error 80% intervals",
            "replicates":reps,"n_per_replicate":800,"calibration":250,
            "rolling_window":80,"shift_index":500,
            "note":"Simulated errors, NOT observed gold prices or trading performance",
            "cases":{}}
    for scenario in ("stationary","volatility_triples_at_t500"):
        for rho in (0.0,0.6):
            sims=[simulate(10000+i,"stationary" if scenario=="stationary" else "shift",rho) for i in range(reps)]
            stats={}
            for key in sims[0]:
                coverages=[sim[key][0] for sim in sims]
                widths=[sim[key][1] for sim in sims]
                stats[key]={"coverage":round(statistics.mean(coverages),4),
                            "avg_half_width":round(statistics.mean(widths),4),
                            "coverage_se":round(statistics.stdev(coverages)/math.sqrt(reps),4)}
            result["cases"][f"{scenario}_rho{rho}"]=stats
    return result

class TestCausality(unittest.TestCase):
    def test_future_outlier_cannot_change_prior_interval(self):
        e=[math.sin(i) for i in range(800)]
        old=widths_before(e,550); e[550:]=[999.0]*250
        self.assertEqual(old,widths_before(e,550))
    def test_rolling_uses_only_past(self):
        e=[0.5]*800; e[470:550]=[5.0]*80
        self.assertEqual(widths_before(e,550),(0.5,5.0))
    def test_rank_boundary(self):
        self.assertEqual(order_quantile([1,2,3,4,5],0.8),5)
        self.assertEqual(order_quantile([1,2,3,4],0.8),4)
    def test_deterministic(self):
        self.assertEqual(simulate(4,"shift",0.6),simulate(4,"shift",0.6))
    def test_no_data_before_start(self):
        with self.assertRaises(ValueError): widths_before([1]*800,249)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--reps",type=int,default=400)
    parser.add_argument("--test",action="store_true")
    args=parser.parse_args()
    if args.test: unittest.main(argv=["interval_shift_experiment.py"])
    else: print(json.dumps(aggregate(args.reps),indent=2))
