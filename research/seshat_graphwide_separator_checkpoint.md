# Seshat graph-wide separator checkpoint

A violated odd-cycle inequality can be searched graph-wide with a two-layer parity expansion. Each original vertex v becomes states (v,0) and (v,1). For edge e={u,v} with disagreement probability d_e, add parity-preserving transitions with cost d_e and parity-flipping transitions with cost 1-d_e. A shortest path from (v,0) to (v,1) represents an odd-labelled closed walk; distance below 1 is a sound rejection certificate with margin 1-distance.

This avoids relying on a fundamental cycle basis, which the prior K4 counterexample showed can miss a violated non-basis cycle. Costs are nonnegative, so Dijkstra gives a polynomial-time detector. A repeated traversal of one edge with opposite labels always costs exactly 1, so the useful predicate is distance < 1; the objective is naturally capped at zero violation even when all simple cycles have negative slack.

Falsification: differential testing on random undirected graphs with 3 through 6 vertices compared exhaustive enumeration of all simple cycles and all odd edge subsets against the parity-expanded shortest-path detector. Across 1,000 trials per graph size, it matched max(0, strongest exhaustive violation) exactly within 1e-9 tolerance, with no missed positive violation or false rejection.

Scope: this separates odd-cycle inequalities over disagreement variables; passing is not a proof of global joint feasibility.

Next step: implement witness reconstruction and integrate this as a pre-solver rejection layer, with regressions for the prior 5-cycle, the K4 basis-miss case, random feasible joint distributions, and exhaustive small-graph differential checks.
