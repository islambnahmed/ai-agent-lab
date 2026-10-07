# Seshat — Linear-time odd cycle inequality separation

## Result

For a cycle with edge disagreement probabilities (d_1,ldots,d_m), every realizable joint distribution obeys, for every odd edge subset (F),

[
sum_{e\in F} d_e-sum_{e\notin F}d_e \le |F|-1.
]

A positive value of

[
V(F)=sum_{e\in F} d_e-sum_{e\notin F}d_e-|F|+1
]

is therefore a sound infeasibility certificate.

Naively separating this family checks (2^{m-1}) odd subsets. The strongest violation can instead be found in O(m).

Let

[
g_e=2d_e-1,qquad B=1-sum_e d_e.
]

Then (V(F)=B+sum_{e\in F}g_e). Ignoring parity, the maximizing set contains exactly edges with (g_e>0). If that set has odd cardinality, it is already optimal. If it has even cardinality, odd parity is restored by the cheapest single membership flip, i.e. an edge minimizing (|g_e|). Thus exact separation is linear in cycle length.

## Falsification

A local exhaustive-vs-linear comparison sampled 5,000 random disagreement vectors for each cycle length 3 through 10. The maximum discrepancy between brute-force separation and the O(m) separator was (8.88\times10^{-16}), consistent with floating-point roundoff.

For (d=[0.1,0.1,0.1,0.1,0.6]), both methods select the singleton odd subset containing the 0.6 edge and return violation 0.2. Hence these locally admissible edge disagreements cannot arise from one global binary joint distribution.

## Scope

This is a rejection certificate, not a feasibility proof. A system that passes the checked cycle inequalities may still be globally infeasible. A practical next layer is to run this separator over a cycle basis before invoking an exponential atom solver or external LP solver.

## Reproducibility note

The derivation is algebraic: substituting (g_e=2d_e-1) into (B+sum_{e\in F}g_e) gives the original violation expression exactly. The parity repair is optimal because changing parity requires an odd number of membership flips and every additional flip incurs nonnegative loss relative to the unconstrained optimum; the minimum-loss single flip therefore dominates all multi-flip repairs.
