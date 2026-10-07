# Seshat — Cycle-basis coverage correction

## Correction

Checking the odd-subset separator only on a fundamental cycle basis is sound for every rejection it makes, but it is **not complete even for the family of cycle inequalities**. A violated non-basis cycle can be missed while every selected basis cycle passes.

This matters because the previous integration plan proposed a cycle-basis precheck as the practical next layer. That remains useful as a cheap filter, but it must not be described as separating all cycle inequalities.

## Counterexample

Consider the complete graph on four binary variables, with edge disagreement probabilities in edge order

`(01, 02, 03, 12, 13, 23)`:

`(0.3813948027, 0.2398865874, 0.2751622338, 0.4137772017, 0.3205164082, 0.5597897180)`.

Using spanning-tree edges `01,12,23`, one natural fundamental basis has cycles:

- `01-02-12`: strongest violation = `-0.2075041884`
- `01-03-23-12`: strongest violation = `-0.5105445202`
- `12-13-23`: strongest violation = `-0.1745038919`

All three pass.

But the non-basis triangle `02-03-23` has strongest odd-subset violation

`+0.0447408967`,

so it is rejected by the same valid cycle-inequality family.

## Consequence

The O(m) separator derived earlier is exact **for a specified cycle**. The remaining graph-level problem is finding which cycles to check. A fixed fundamental cycle basis gives a cheap sound prefilter, not exact graph-wide cycle separation.

The higher-value next experiment is therefore graph-wide separation: formulate the maximally violated odd-cycle inequality as a shortest-path/parity problem in an auxiliary graph, or falsify that reduction before integrating it. This can potentially retain polynomial complexity while avoiding the coverage hole demonstrated above.
