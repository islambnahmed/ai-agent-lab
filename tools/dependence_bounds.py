"""Exact probability bounds for small binary latent-failure systems.

No independence assumption is made. Constraints may include marginal failure
probabilities and selected pairwise joint failure probabilities. The solver
enumerates the 2^n binary worlds conceptually; this module implements the
small-n cases with a vertex-enumeration fallback specialized for n<=4 so it
has no third-party runtime dependency.

For three modes, bounds on P(A&B&C) have a closed LP representation. This
module exposes the useful evidence-survival quantity 1-P(all specified modes
fail).
"""
from itertools import product, combinations

EPS = 1e-12
FEAS_TOL = 1e-12

def _solve_linear_vertices(c, aeq, beq):
    """Min/max c.x over x>=0, Aeq x=b using basic feasible vertices."""
    import itertools
    n = len(c)
    m = len(aeq)
    best_min = (float("inf"), None)
    best_max = (-float("inf"), None)
    # Gaussian solve tiny square systems without numpy.
    def solve(mat, rhs):
        a=[list(map(float,row))+[float(r)] for row,r in zip(mat,rhs)]
        for col in range(len(a)):
            pivot=max(range(col,len(a)), key=lambda r: abs(a[r][col]))
            if abs(a[pivot][col]) < EPS: return None
            a[col],a[pivot]=a[pivot],a[col]
            d=a[col][col]
            a[col]=[v/d for v in a[col]]
            for r in range(len(a)):
                if r==col: continue
                f=a[r][col]
                a[r]=[x-f*y for x,y in zip(a[r],a[col])]
        return [row[-1] for row in a]
    for basis in itertools.combinations(range(n), m):
        mat=[[row[j] for j in basis] for row in aeq]
        sol=solve(mat,beq)
        if sol is None or min(sol) < -FEAS_TOL: continue
        x=[0.0]*n
        for j,v in zip(basis,sol): x[j]=max(0.0,v)
        if any(abs(sum(row[j]*x[j] for j in range(n))-b)>FEAS_TOL for row,b in zip(aeq,beq)):
            continue
        val=sum(ci*xi for ci,xi in zip(c,x))
        if val < best_min[0]: best_min=(val,x)
        if val > best_max[0]: best_max=(val,x)
    if best_min[1] is None: raise ValueError("constraints are infeasible")
    return best_min, best_max

def all_fail_bounds(marginals, pairwise=None):
    """Return tight bounds on probability all latent modes fail.

    Marginals-only bounds use the closed-form Frechet-Hoeffding interval for
    any number of modes. Selected pairwise constraints use the exact small-n
    vertex solver and are currently limited to n<=4.

    marginals: sequence P(mode_i fails)
    pairwise: optional dict {(i,j): P(i and j fail)}
    """
    n=len(marginals)
    if n < 1: raise ValueError("at least one mode is required")
    for p in marginals:
        if not 0 <= p <= 1: raise ValueError("marginals must be in [0,1]")
    pairwise=pairwise or {}
    if not pairwise:
        return max(0.0, sum(map(float, marginals)) - (n - 1)), min(map(float, marginals))
    if n > 4: raise ValueError("pairwise-constrained prototype supports at most 4 modes")
    worlds=list(product((0,1), repeat=n))
    aeq=[[1.0]*len(worlds)]; beq=[1.0]
    for i,p in enumerate(marginals):
        aeq.append([float(w[i]) for w in worlds]); beq.append(float(p))
    for (i,j),q in pairwise.items():
        if not (0 <= i < j < n) or not 0 <= q <= 1:
            raise ValueError("invalid pairwise constraint")
        # Necessary Frechet bounds catch contradictory pairwise inputs before
        # floating-point vertex enumeration can blur a tiny infeasibility.
        lower = max(0.0, float(marginals[i]) + float(marginals[j]) - 1.0)
        upper = min(float(marginals[i]), float(marginals[j]))
        if q < lower or q > upper:
            raise ValueError("pairwise constraint violates Frechet bounds")
        aeq.append([float(w[i] and w[j]) for w in worlds]); beq.append(float(q))
    # With all three pairwise joints specified, the eight probability atoms
    # are affine functions of t=P(A&B&C). Non-negativity therefore gives the
    # exact feasible interval below. This avoids floating-point vertex
    # enumeration for the complete triangle and detects globally inconsistent
    # triples that can pass every pairwise Frechet check independently.
    if n == 3 and all(k in pairwise for k in ((0,1),(0,2),(1,2))):
        pa,pb,pc=map(float,marginals)
        qab=float(pairwise[(0,1)]); qac=float(pairwise[(0,2)]); qbc=float(pairwise[(1,2)])
        lower=max(0.0, qab+qac-pa, qab+qbc-pb, qac+qbc-pc)
        upper=min(qab, qac, qbc, 1.0-pa-pb-pc+qab+qac+qbc)
        if lower > upper:
            raise ValueError("pairwise constraints are globally infeasible")
        return lower,upper
    c=[1.0 if all(w) else 0.0 for w in worlds]
    lo,hi=_solve_linear_vertices(c,aeq,beq)
    return lo[0],hi[0]

def any_survives_bounds(marginals, pairwise=None):
    """Tight bounds on P(at least one evidence path survives)."""
    lo,hi=all_fail_bounds(marginals,pairwise)
    return 1.0-hi, 1.0-lo

if __name__ == "__main__":
    # Marginals only: Frechet bound.
    assert any_survives_bounds([.2,.2]) == (.8,1.0)
    # Marginals-only bounds scale without enumerating 2^n worlds.
    assert all_fail_bounds([.5]*5) == (0.0,.5)
    assert all_fail_bounds([.9]*5) == (.5,.9)
    # Three pairwise-independent failures need not be mutually independent.
    lo,hi=any_survives_bounds([.2]*3,{(0,1):.04,(0,2):.04,(1,2):.04})
    assert abs(lo-.96)<1e-9 and abs(hi-1.0)<1e-9
    # Full independence would pick .992, but that is only one point in [.96,1].
    assert lo <= .992 <= hi
    # Inconsistent constraints must be rejected.
    try:
        any_survives_bounds([.1,.1],{(0,1):.2})
        raise AssertionError("expected infeasible constraints")
    except ValueError:
        pass
    # Complete 3-event pairwise information has an exact closed-form path.
    # This locally valid triangle is globally impossible.
    try:
        all_fail_bounds([.1,.1,.1],{(0,1):0.0,(0,2):.1,(1,2):.1})
        raise AssertionError("expected globally infeasible triangle")
    except ValueError:
        pass
    # Feasible complete triangle: exact triple-intersection interval [0,.25].
    lo,hi=all_fail_bounds([.5,.5,.5],{(0,1):.25,(0,2):.25,(1,2):.25})
    assert lo == 0.0 and hi == .25
    # Four pairwise-independent failures need not be mutually independent.
    lo,hi=all_fail_bounds([.5]*4,{(0,1):.25,(0,2):.25,(0,3):.25,(1,2):.25,(1,3):.25,(2,3):.25})
    assert abs(lo) < 1e-12 and abs(hi - 1.0/6.0) < 1e-12
    # Structural probability constraints are exact input semantics: solver
    # tolerances must not legalize even sub-tolerance contradictions.
    for impossible_q in (.100000001, .1 + 5e-13):
        try:
            any_survives_bounds([.1,.1],{(0,1):impossible_q})
            raise AssertionError("expected near-boundary infeasible constraints")
        except ValueError:
            pass
    print("dependence_bounds: all tests passed")
