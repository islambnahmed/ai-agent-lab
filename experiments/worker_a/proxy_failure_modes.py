#!/usr/bin/env python3
"""Synthetic proxy failure modes; NO real gold data. Causal labels and observations."""
import argparse, json, math, random, statistics, unittest
N=720; SHIFT=400; W=80; PW=20
PHASES={'early':(400,480),'late':(550,680)}
def quantile(xs):
    if not xs or not all(math.isfinite(x) for x in xs): raise ValueError('bad scores')
    ys=sorted(abs(x) for x in xs)
    return ys[min(len(ys),math.ceil((len(ys)+1)*0.8))-1]
def ar_shocks(rng,n,rho,multiplier):
    if not -1<rho<1: raise ValueError('rho')
    state=0.; out=[]
    for j in range(n):
        state=rho*state+math.sqrt(1-rho*rho)*rng.gauss(0,1)
        out.append(state*(multiplier if j>=SHIFT else 1.))
    return out
def proxy_at(observed,t,lag=0):
    end=t-lag+1
    if lag<0 or end<=0: raise ValueError('not observable')
    x=observed[max(0,end-PW):end]
    return math.sqrt(sum(v*v for v in x)/len(x))
def generate(seed,h,rho,scenario):
    if h not in (7,30): raise ValueError('horizon')
    rng=random.Random(seed)
    target=ar_shocks(rng,N+h+1,rho,1. if scenario=='false_alarm' else 3.)
    if scenario in ('aligned_jump','lagged_jump'):
        signal=target; lag=10 if scenario=='lagged_jump' else 0
    elif scenario=='decoupled_jump':
        signal=ar_shocks(rng,N+h+1,rho,1.); lag=0
    elif scenario=='false_alarm':
        signal=ar_shocks(rng,N+h+1,rho,3.); lag=0
    else: raise ValueError('scenario')
    errors=[sum(target[t+1:t+h+1])/math.sqrt(h) for t in range(N)]
    proxies=[proxy_at(signal,t,lag) if t>=lag else 1. for t in range(N)]
    return errors,proxies
def width(errors,proxies,t,h,method):
    stop=t-h; start=stop-W
    if start<0 or t>=len(errors) or len(proxies)!=len(errors): raise ValueError('maturity')
    if method=='rolling': return quantile(errors[start:stop])
    if method=='proxy_scaled':
        if not math.isfinite(proxies[t]) or proxies[t]<=0: raise ValueError('proxy')
        return quantile([errors[i]/max(proxies[i],1e-8) for i in range(start,stop)])*proxies[t]
    raise ValueError('method')
def trial(seed,h,rho,scenario):
    errors,proxies=generate(seed,h,rho,scenario); out={}
    for phase,(a,b) in PHASES.items():
        for method in ('rolling','proxy_scaled'):
            widths=[width(errors,proxies,t,h,method) for t in range(a,b)]
            out[phase+'_'+method]=(sum(abs(errors[t])<=widths[t-a] for t in range(a,b))/(b-a),statistics.mean(widths))
    return out
def run(reps=100):
    if reps<2: raise ValueError('reps')
    scenarios={
        'aligned_jump':'target and proxy jump 3x',
        'lagged_jump':'target jumps 3x; proxy lags by 10',
        'decoupled_jump':'target jumps 3x; independent proxy stationary',
        'false_alarm':'target stationary; independent proxy jumps 3x'}
    result={'synthetic_only':True,'replications':reps,'horizons':[7,30],'rhos':[0.,0.6],
            'target_coverage':0.8,'label_rule':'issue_i+h<issue_t',
            'proxy_rule':'signal observed at index <= t-lag','proxy_window':PW,
            'residual_window':W,'phases':PHASES,'scenarios':scenarios,'cases':{}}
    for h in (7,30):
        for rho in (0.,0.6):
            for scenario in scenarios:
                sims=[trial(33000+j,h,rho,scenario) for j in range(reps)]
                result['cases'][f'h{h}_rho{rho}_{scenario}']={
                    k:{'coverage':round(statistics.mean(s[k][0] for s in sims),4),
                       'coverage_se':round(statistics.stdev(s[k][0] for s in sims)/math.sqrt(reps),4),
                       'mean_half_width':round(statistics.mean(s[k][1] for s in sims),4)}
                    for k in sims[0]}
    return result
class TestCausality(unittest.TestCase):
    def test_no_future_proxy(self):
        a=[.2]*500; b=a.copy(); b[401:]=[999]*99
        for lag in (0,10): self.assertEqual(proxy_at(a,400,lag),proxy_at(b,400,lag))
    def test_real_lag(self):
        a=[1.]*500; a[399]=100.
        self.assertGreater(proxy_at(a,400),proxy_at(a,400,10))
    def test_immature_labels_excluded(self):
        e,p=generate(5,30,0.,'aligned_jump'); old=width(e,p,420,30,'proxy_scaled')
        e[390:420]=[999.]*30
        self.assertEqual(old,width(e,p,420,30,'proxy_scaled'))
    def test_mature_labels_included(self):
        e,p=[1.]*720,[1.]*720; old=width(e,p,420,30,'proxy_scaled')
        e[310:390]=[5.]*80
        self.assertNotEqual(old,width(e,p,420,30,'proxy_scaled'))
    def test_future_errors_excluded(self):
        e,p=generate(6,7,.6,'aligned_jump'); old=width(e,p,420,7,'proxy_scaled')
        e[420:]=[999.]*(len(e)-420)
        self.assertEqual(old,width(e,p,420,7,'proxy_scaled'))
    def test_distinct_proxy(self):
        self.assertNotEqual(generate(9,7,0.,'aligned_jump')[1][450],
                            generate(9,7,0.,'decoupled_jump')[1][450])
    def test_repeatable(self):
        self.assertEqual(trial(7,30,.6,'false_alarm'),trial(7,30,.6,'false_alarm'))
    def test_invalid(self):
        with self.assertRaises(ValueError): proxy_at([1,2],0,10)
        with self.assertRaises(ValueError): generate(1,5,0.,'aligned_jump')
        with self.assertRaises(ValueError): width([1.]*720,[1.]*720,50,30,'rolling')
        with self.assertRaises(ValueError): run(1)
    def test_nan(self):
        with self.assertRaises(ValueError): quantile([1.,float('nan')])
    def test_constant_proxy(self):
        e=[(i%5)+1 for i in range(720)]; p=[1.]*720
        self.assertEqual(width(e,p,400,7,'rolling'),width(e,p,400,7,'proxy_scaled'))
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true')
    parser.add_argument('--reps',type=int,default=100)
    a=parser.parse_args()
    if a.test: unittest.main(argv=['proxy_failure_modes.py'])
    else: print(json.dumps(run(a.reps),indent=2))
