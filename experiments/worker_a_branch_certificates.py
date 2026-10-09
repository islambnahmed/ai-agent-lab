"""Worker A: bounded branch-and-bound certificates for 0/1 knapsack.
Standard library only; no optimal labels enter the certifier.
Run: python worker_a_branch_certificates.py
"""
from functools import cmp_to_key
import random, time

DOMAINS = ('packing', 'mixed', 'shift', 'adversarial')
DEPTHS = (0, 1, 2, 3, 4)
N = 30

def instance(rng, domain):
    weights = [rng.randint(1,20) for _ in range(N)]
    if domain == 'packing':
        values = weights[:]
    elif domain == 'mixed':
        values = [max(1, w+rng.randint(-4,12)) for w in weights]
    elif domain == 'shift':
        values = [rng.randint(1,50) for _ in weights]
    elif domain == 'adversarial':
        weights = [rng.randint(12,24) for _ in range(N)]
        values = [w+rng.randint(-2,3) for w in weights]
    else:
        raise ValueError(domain)
    cap = int(sum(weights) * (.35 if domain in ('shift','adversarial') else .5))
    return list(zip(weights, values)), cap

def density_cmp(items, a, b, tie):
    wa, va = items[a]
    wb, vb = items[b]
    t = va*wb-vb*wa
    if t:
        return -1 if t>0 else 1
    if tie == "value" and va != vb:
        return -1 if va > vb else 1
    return (a>b)-(a<b)

def sorted_ids(items, tie):
    return sorted(range(len(items)), key=cmp_to_key(lambda a,b:density_cmp(items,a,b,tie)))

def greedy(items, cap, ids):
    total=0
    for i in ids:
        w,v=items[i]
        if w<=cap:
            cap-=w
            total+=v
    return total

def lp_bound(items, cap, ids, fixed_in, fixed_out):
    # Exact floor of fractional-knapsack upper bound using integer arithmetic.
    value=0
    for i in fixed_in:
        w,v=items[i]
        cap-=w
        value+=v
    if cap<0:
        return -1, None
    fractional=None
    for i in ids:
        if i in fixed_in or i in fixed_out:
            continue
        w,v=items[i]
        if w<=cap:
            cap-=w
            value+=v
        else:
            value+=(cap*v)//w
            fractional=i
            break
    return value, fractional

def certify(items, cap, ids, candidate, max_depth):
    # Both include/exclude subproblems must be proved below candidate.
    calls=0
    def prove(inside, outside, depth):
        nonlocal calls
        ub, frac=lp_bound(items,cap,ids,inside,outside)
        calls+=1
        if ub<=candidate:
            return True
        if depth==0 or frac is None:
            return False
        return prove(inside | {frac},outside,depth-1) and prove(inside,outside | {frac},depth-1)
    return prove(frozenset(),frozenset(),max_depth), calls

def exact(items,cap):
    dp=[0]*(cap+1)
    for w,v in items:
        for c in range(cap,w-1,-1):
            dp[c]=max(dp[c],dp[c-w]+v)
    return dp[cap]

def evaluate(domain, seed, samples, tie, candidate_mode):
    rng=random.Random(seed)
    stats={d:dict(proven=0,calls=0,elapsed_ns=0,invalid=0) for d in DEPTHS}
    errors=0
    for _ in range(samples):
        items,cap=instance(rng,domain)
        ids=sorted_ids(items,tie)
        candidate=greedy(items,cap,ids)
        if candidate_mode == "two_greedy":
            candidate=max(candidate,greedy(items,cap,sorted(range(len(items)), key=lambda i:(-items[i][1], i))))
        truth=exact(items,cap)
        assert candidate<=truth
        errors+=candidate<truth
        for d in DEPTHS:
            start=time.perf_counter_ns()
            proof,calls=certify(items,cap,ids,candidate,d)
            elapsed=time.perf_counter_ns()-start
            stats[d]['proven']+=proof
            stats[d]['calls']+=calls
            stats[d]['elapsed_ns']+=elapsed
            stats[d]['invalid']+=bool(proof and candidate<truth)
    return errors,stats

def exhaustive_validation():
    rng=random.Random(981733)
    count=0
    for domain in DOMAINS:
        for _ in range(30):
            items,_=instance(rng,domain)
            items=items[:12]
            cap=int(sum(w for w,_ in items)*.43)
            opt=exact(items,cap)
            brute=max((sum(v for i,(w,v) in enumerate(items) if mask>>i&1)
                       for mask in range(1<<len(items))
                       if sum(w for i,(w,v) in enumerate(items) if mask>>i&1)<=cap))
            assert opt==brute, (domain,opt,brute)
            for tie in ('value','index'):
                ids=sorted_ids(items,tie)
                candidate=greedy(items,cap,ids)
                prev=False
                for depth in DEPTHS:
                    proof,_=certify(items,cap,ids,candidate,depth)
                    assert not proof or candidate==brute
                    assert not prev or proof
                    prev=proof
                    count+=1
    return count

def main():
    checks=exhaustive_validation()
    print('PASS exhaustive 12-item cross-checks:', checks, 'certificate checks across 120 distinct instances')
    print('domain tie candidate seed n greedy_errors depth proven_pct lp_calls_per_case certificate_ms_per_case invalid')
    for domain in DOMAINS:
        for tie in ("value", "index"):
            for candidate_mode in ("one_greedy", "two_greedy"):
                for seed in (3101,3102,3103):
                    n=500
                    errors, stats=evaluate(domain,seed,n,tie,candidate_mode)
                    for d,s in stats.items():
                        print(f'{domain:11} {tie:5} {candidate_mode:10} {seed} {n} {errors/n:12.2%} {d:5} {s["proven"]/n:10.2%} '
                              f'{s["calls"]/n:17.2f} {s["elapsed_ns"]/1e6/n:23.4f} {s["invalid"]}')
                        assert s['invalid']==0
    print('PASS: no invalid certificates; independent DP checked all samples')

if __name__=='__main__':
    main()
