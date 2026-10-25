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
from fractions import Fraction

def _solve_linear_vertices(c, aeq, beq):
    """Exact small-n LP vertex enumeration, with no numerical feasibility slack.

    Binary-world constraint coefficients are integers. Interpret user-supplied
    probabilities via their decimal spelling, then solve every basis using
    rational arithmetic. A float tolerance can otherwise turn a genuinely
    infeasible cyclic model (e.g. contradictions of size 5e-13) into a false
    reliability certificate. The cyclic solver is deliberately limited to
    four modes, so exact enumeration remains practical.
    """
    n = len(c)
    m = len(aeq)
    rhs = [Fraction(str(b)) for b in beq]
    matrix = [[Fraction(v) for v in row] for row in aeq]
    objective = [Fraction(str(v)) for v in c]
    best_min = None
    best_max = None

    def solve_basis(basis):
        a = [[matrix[i][j] for j in basis] + [rhs[i]]
             for i in range(m)]
        for col in range(m):
            pivot = next((r for r in range(col, m) if a[r][col]), None)
            if pivot is None:
                return None
            a[col], a[pivot] = a[pivot], a[col]
            scale = 1 / a[col][col]
            for j in range(col, m + 1):
                a[col][j] *= scale
            for r in range(m):
                if r == col:
                    continue
                factor = a[r][col]
                if factor:
                    for j in range(col, m + 1):
                        a[r][j] -= factor * a[col][j]
        return [a[i][-1] for i in range(m)]

    for basis in combinations(range(n), m):
        sol = solve_basis(basis)
        if sol is None or any(v < 0 for v in sol):
            continue
        x = [Fraction(0)] * n
        for j, v in zip(basis, sol):
            x[j] = v
        value = sum(ci * xi for ci, xi in zip(objective, x))
        if best_min is None or value < best_min[0]:
            best_min = (value, x)
        if best_max is None or value > best_max[0]:
            best_max = (value, x)

    if best_min is None:
        raise ValueError("constraints are infeasible")
    return ((float(best_min[0]), [float(v) for v in best_min[1]]),
            (float(best_max[0]), [float(v) for v in best_max[1]]))


def all_fail_bounds(marginals, pairwise=None):
    """Return tight bounds on probability all latent modes fail (n<=4).

    marginals: sequence P(mode_i fails)
    pairwise: optional dict {(i,j): P(i and j fail)}
    """
    n=len(marginals)
    if n < 1: raise ValueError("at least one mode is required")
    for p in marginals:
        if not 0 <= p <= 1: raise ValueError("marginals must be in [0,1]")
    pairwise=pairwise or {}
    # Marginals alone have exact Frechet-Hoeffding bounds for any n, so avoid
    # exponential atom enumeration entirely in this common case.
    if not pairwise:
        # Keep decimal input semantics exact until the public float boundary.
        # Float summation can move a sharp bound across its true endpoint.
        vals=[Fraction(str(p)) for p in marginals]
        return (float(max(Fraction(0), sum(vals, Fraction(0)) - (n - 1))),
                float(min(vals)))
    # Validate every supplied edge before choosing a graph-specific solver.
    for (i,j),q in pairwise.items():
        if not (0 <= i < j < n) or not 0 <= q <= 1:
            raise ValueError("invalid pairwise constraint")
        # Necessary Frechet bounds catch contradictory pairwise inputs before
        # floating-point vertex enumeration can blur a tiny infeasibility.
        # Interpret decimal spellings exactly, matching the cyclic LP solver.
        # Float arithmetic can spuriously reject valid boundary inputs:
        # .8 + .8 - 1 rounds to .6000000000000001, not .6.
        pi, pj, joint = (Fraction(str(v)) for v in (marginals[i], marginals[j], q))
        lower = max(Fraction(0), pi + pj - 1)
        upper = min(pi, pj)
        if joint < lower or joint > upper:
            raise ValueError("pairwise constraint violates Frechet bounds")
    # A forest admits exact arbitrary-n all-intersection bounds.  For each
    # connected tree C:
    #   L_C=max(0, sum_e q_e - sum_v (deg(v)-1)p_v), U_C=min_e q_e.
    # Isolated vertices have [p_v,p_v].  Different components have no joint
    # constraints, so their component-intersection events combine by Frechet.
    parent=list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    cyclic=False
    for i,j in pairwise:
        ri,rj=find(i),find(j)
        if ri == rj:
            cyclic=True
            break
        parent[ri]=rj
    if not cyclic:
        # Rebuild components after the detection pass (which may have stopped
        # early only in the cyclic case).
        parent=list(range(n))
        for i,j in pairwise:
            ri,rj=find(i),find(j)
            parent[ri]=rj
        comps={}
        for v in range(n):
            comps.setdefault(find(v), []).append(v)
        lowers=[]; uppers=[]
        for nodes in comps.values():
            node_set=set(nodes)
            edges=[(i,j,Fraction(str(q))) for (i,j),q in pairwise.items()
                   if i in node_set and j in node_set]
            if not edges:
                p=Fraction(str(marginals[nodes[0]]))
                lowers.append(p); uppers.append(p)
                continue
            deg={v:0 for v in nodes}
            for i,j,_ in edges:
                deg[i]+=1; deg[j]+=1
            lo=max(Fraction(0),
                   sum((q for _,_,q in edges), Fraction(0))
                   - sum(((deg[v]-1)*Fraction(str(marginals[v]))
                          for v in nodes), Fraction(0)))
            hi=min(q for _,_,q in edges)
            lowers.append(lo); uppers.append(hi)
        k=len(lowers)
        return (float(max(Fraction(0), sum(lowers, Fraction(0))-(k-1))),
                float(min(uppers)))

    if n > 4:
        raise ValueError("cyclic pairwise prototype supports at most 4 modes")
    worlds=list(product((0,1), repeat=n))
    aeq=[[1.0]*len(worlds)]; beq=[1.0]
    for i,p in enumerate(marginals):
        aeq.append([float(w[i]) for w in worlds]); beq.append(float(p))
    for (i,j),q in pairwise.items():
        aeq.append([float(w[i] and w[j]) for w in worlds]); beq.append(float(q))
    # With all three pairwise joints specified, the eight probability atoms
    # are affine functions of t=P(A&B&C). Non-negativity therefore gives the
    # exact feasible interval below. This avoids floating-point vertex
    # enumeration for the complete triangle and detects globally inconsistent
    # triples that can pass every pairwise Frechet check independently.
    if n == 3 and all(k in pairwise for k in ((0,1),(0,2),(1,2))):
        pa,pb,pc=(Fraction(str(v)) for v in marginals)
        qab,qac,qbc=(Fraction(str(pairwise[k]))
                     for k in ((0,1),(0,2),(1,2)))
        lower=max(Fraction(0), qab+qac-pa, qab+qbc-pb, qac+qbc-pc)
        upper=min(qab, qac, qbc, 1-pa-pb-pc+qab+qac+qbc)
        if lower > upper:
            raise ValueError("pairwise constraints are globally infeasible")
        return float(lower),float(upper)
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
    # Marginals-only bounds remain exact beyond the atom solver's n<=4 scope.
    assert all_fail_bounds([.9]*5) == (.5,.9)
    # Floating-point complements need tolerant comparison (1-.9 != .1).
    survival = any_survives_bounds([.9]*5)
    assert abs(survival[0] - .1) < 1e-12 and abs(survival[1] - .5) < 1e-12
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
    # Forest pairwise graphs have exact arbitrary-n bounds.
    lo,hi=all_fail_bounds([.5]*5,{(0,1):.25,(1,2):.25,(2,3):.25,(3,4):.25})
    assert abs(lo-0.0)<1e-12 and abs(hi-.25)<1e-12
    # Disconnected forest: one edge plus three isolated .9 vertices.
    lo,hi=all_fail_bounds([.9]*5,{(0,1):.8})
    assert abs(lo-.5)<1e-12 and abs(hi-.8)<1e-12
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
    # Structural probability constraints are exact input semantics: solver
    # tolerances must not legalize even sub-tolerance contradictions.
    for impossible_q in (.100000001, .1 + 5e-13):
        try:
            any_survives_bounds([.1,.1],{(0,1):impossible_q})
            raise AssertionError("expected near-boundary infeasible constraints")
        except ValueError:
            pass
    # Four fair pairwise-independent failures need not be mutually independent.
    # Exact extremal all-failure interval is [0,1/6], not the iid point 1/16.
    pair4 = {(i,j):.25 for i in range(4) for j in range(i+1,4)}
    lo,hi=all_fail_bounds([.5]*4,pair4)
    assert abs(lo) < 1e-12 and abs(hi-1/6) < 1e-12
    slo,shi=any_survives_bounds([.5]*4,pair4)
    assert abs(slo-5/6) < 1e-12 and abs(shi-1.0) < 1e-12
    # A globally impossible triangle remains impossible when embedded in n=4.
    try:
        all_fail_bounds([.1,.1,.1,.5],{(0,1):0.0,(0,2):.1,(1,2):.1})
        raise AssertionError("expected globally infeasible four-mode cycle")
    except ValueError:
        pass
    # Cross-review: a numeric 1e-12 feasibility tolerance previously accepted
    # impossible cyclic constraints when the contradiction was only 5e-13.
    # In a four-cycle, the first three equal-joint edges force all four
    # events to coincide, contradicting a zero joint on the closing edge.
    tiny = 5e-13
    for impossible_edges in (
        {(0,1):0.0, (0,2):tiny, (1,2):tiny},
        {(0,1):tiny, (1,2):tiny, (2,3):tiny, (0,3):0.0},
    ):
        try:
            all_fail_bounds([tiny]*4, impossible_edges)
            raise AssertionError("expected sub-tolerance cyclic infeasibility")
        except ValueError:
            pass
    # Exact enumeration must still accept a truly feasible tiny four-cycle.
    lo,hi = all_fail_bounds([tiny]*4,
                            {(0,1):tiny, (1,2):tiny,
                             (2,3):tiny, (0,3):tiny})
    assert lo == tiny and hi == tiny
    # Exact boundary checks: float Frechet validation rejected this feasible
    # all-equal three-mode model (.8+.8-1 > .6 due rounding).
    lo,hi=all_fail_bounds([.8]*3,{(0,1):.6,(0,2):.6,(1,2):.6})
    assert lo == .4 and hi == .4
    # Disjoint events exhaust the sample space: float cancellation previously
    # made the upper bound negative and falsely reported infeasibility.
    lo,hi=all_fail_bounds([.3,.3,.4],{(0,1):0.0,(0,2):0.0,(1,2):0.0})
    assert lo == 0.0 and hi == 0.0
    # Boundary pairwise checks also apply to the forest shortcut.
    assert all_fail_bounds([.8,.8],{(0,1):.6}) == (.6,.6)
    # A feasible forest of identical events must never return lower > upper.
    # Float accumulation previously produced (0.7000000000000002, 0.7).
    chain={(i,i+1):.7 for i in range(4)}
    assert all_fail_bounds([.7]*5,chain) == (.7,.7)
    # Two disconnected trees each force their component event to probability
    # .7, so their intersection is bounded by exactly [.4, .7].
    two_chains={(i,i+1):.7 for i in (0,1,2,4,5,6)}
    assert all_fail_bounds([.7]*8,two_chains) == (.4,.7)
    print("dependence_bounds: all tests passed")
