"""Deterministic differential oracle for the forest fast path.

Build feasible 4-event distributions from seeded integer atom weights, derive
marginals plus a random spanning tree, and compare the production forest
formula with the generic exact vertex solver. No third-party dependency.
"""
import random
from itertools import product
from tools.dependence_bounds import all_fail_bounds, _solve_linear_vertices

def oracle(marginals, pairwise):
    n=len(marginals)
    worlds=list(product((0,1), repeat=n))
    aeq=[[1.0]*len(worlds)]
    beq=[1.0]
    for i,p in enumerate(marginals):
        aeq.append([float(w[i]) for w in worlds]); beq.append(float(p))
    for (i,j),q in pairwise.items():
        aeq.append([float(w[i] and w[j]) for w in worlds]); beq.append(float(q))
    c=[1.0 if all(w) else 0.0 for w in worlds]
    lo,hi=_solve_linear_vertices(c,aeq,beq)
    return lo[0],hi[0]

def random_tree(rng,n):
    # Each new vertex attaches to an earlier one: always a spanning tree.
    return [(rng.randrange(v),v) for v in range(1,n)]

def run(cases=100, seed=20261004):
    rng=random.Random(seed)
    worlds=list(product((0,1), repeat=4))
    worst=0.0
    for case in range(cases):
        # Positive integer weights guarantee a feasible interior distribution
        # and make the generated evidence reproducible across Python versions.
        weights=[rng.randint(1,20) for _ in worlds]
        total=float(sum(weights))
        probs=[w/total for w in weights]
        marg=[sum(p for p,w in zip(probs,worlds) if w[i]) for i in range(4)]
        edges=random_tree(rng,4)
        pairs={(i,j):sum(p for p,w in zip(probs,worlds) if w[i] and w[j])
               for i,j in edges}
        fast=all_fail_bounds(marg,pairs)
        exact=oracle(marg,pairs)
        err=max(abs(a-b) for a,b in zip(fast,exact))
        worst=max(worst,err)
        if err > 1e-9:
            raise AssertionError((case, marg, pairs, fast, exact, err))
    print(f"forest oracle: {cases}/{cases} matched; worst error={worst:.3g}")

if __name__=="__main__":
    run()
