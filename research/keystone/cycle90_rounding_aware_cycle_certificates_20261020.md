# Keystone cycle 90 — rounding-aware cycle-inconsistency certificates

Date: 2026-10-20. Scope: authorized `islambnahmed/ai-agent-lab` repository only. This is an experimental, **necessary-only** feasibility presolver, not a replacement for the complete LP oracle.

## Why this cycle changed direction

Cycle 89 found a cyclic four-event system incorrectly accepted by the floating-point vertex solver on `main` (`tools/dependence_bounds.py`, blob `0c20b059f27a576dc62ff6d4a91f1a612ec006ff`). Rather than retrying a blocked edit to that solver, this cycle explored an independent mathematical rejection certificate and discovered a second, opposite failure mode: converting valid rational probability moments to separate Python floats can make them *exactly inconsistent as binary rationals*. Simply replacing the solver with `Fraction(float)` can therefore reject valid intended inputs.

## Mathematical certificate

For binary events `X_i`, let `p_i=P(X_i=1)`, `q_ij=P(X_i=X_j=1)`, and `d_ij=p_i+p_j-2*q_ij=P(X_i != X_j)`. For every path `i=v_0,...,v_k=j`, the pointwise inequality `1[X_i != X_j] <= sum_t 1[X_v(t) != X_v(t+1)]` implies `d_ij <= sum_t d_v(t),v(t+1)`. A violated shortest-path inequality proves global infeasibility, without a tolerance-based LP solve. This test is necessary, not sufficient: three disjoint events each with probability 1/2 pass its triangle inequality but cannot coexist.

### Rounding-aware extension

Interpret a Python float as a *rounded measurement* whose underlying real value lies between midpoints to the previous and next representable floats, clipped to [0,1]. Interpret `Fraction` and integers as exact. Each edge then has a certified disagreement interval:

- `d_lo = p_i_lo + p_j_lo - 2*q_ij_hi`
- `d_hi = p_i_hi + p_j_hi - 2*q_ij_lo`

If `d_lo(edge) > shortest_path_using_d_hi(edge endpoints)`, **no** choice of underlying probabilities inside those rounding intervals can be feasible. The certificate is deliberately conservative. It cannot prove feasibility, and a contradiction smaller than the rounding resolution cannot be identified from the rounded floats alone.

## Reproducible local tests

A prototype and 13 `unittest` cases were executed locally, all passed in 1.274 s.

- 2,000 random four-event distributions built from nonnegative integer world counts: no rejection with exact `Fraction` inputs.
- 2,000 generic feasible distributions independently converted to float: no rejection by the rounding-aware test.
- 2,000 **boundary** feasible distributions with `X_0 != X_1` always, independently converted to float: **1,278/2,000** were rejected by the *strict* `Fraction(float)` path check (505 invalid disagreement distances, 773 path violations), but **0/2,000** were rejected by the rounding-aware check. This is a deterministic seeded stress test, not a population error-rate estimate.
- 400 exact near-infeasible cyclic cases: all detected by both guards.
- 300 independently rounded float cyclic cases with contradictions larger than their rounding envelopes: all detected by the rounding-aware guard.
- Cycle 89's four-event contradiction at `5e-13` is detected. An input perturbation `1e-18` to `0.5` rounds away entirely and is correctly *not* claimed detectable.
- 2,000 independently generated exact fractions were verified to lie inside the midpoint intervals of their converted floats.
- A deliberately impossible three-event triangle is **not** detected; this documents incompleteness.

The cycle-89 local reproduction still shows the original float vertex solver accepting the `5e-13` contradiction, while the previously prototyped exact LP rejects it. No current `main` file was modified.

## Decision

Keep the rounding-aware shortest-path test as a **cheap necessary precheck** only, and keep complete LP feasibility validation as a separate requirement. A future API should explicitly choose between (1) exact-count/`Fraction` semantics, and (2) rounded observations with declared error intervals. Do **not** silently cast independently rounded floats to exact rationals and claim that this recovers the original data. Do not merge this experimental branch without running it in repository CI and reviewing semantics.

## Reproduction artifact

Local scripts: `path_metric_guard.py`, `rounding_aware_metric.py`, `test_cycle90.py`, `test_rounding_aware.py`. Reproduce with `python -m unittest test_cycle90 test_rounding_aware -v` from the artifact directory.

## Provenance

Current `main` source and charter were read through the authorized GitHub connector. The earlier cycle-89 reproduction and exact-solver prototypes came from the attached user-owned archive. All reported new tests were executed in the local runtime; no claim is made that this experiment was run in GitHub Actions or merged into `main`.
