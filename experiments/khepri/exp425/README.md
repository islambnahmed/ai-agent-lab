# Khepri exp425 — Complete-opportunity evaluation under selective missingness

**Date:** 2026-10-24. **Environment:** local Python standard-library, synthetic only. This experiment audits the observation-protocol caveat in exp424 and tests a *pointwise conservative* alternative to treating missing scores as neutral.

## Question

If an agent evaluation logs successes but selectively drops failures, can we preserve anytime familywise validity without assuming missingness is random?

## Result and rationale

Yes, **conditionally on a complete, externally honest list of opportunities** and a bounded potential score for each opportunity. Pre-register the candidate roster, then process every numbered round. For each candidate, use observed `X` in `[-1,1]`, or use **-1** if missing. Let `Y = X` when observed and `Y = -1` otherwise. Then **pathwise** `Y <= X`, regardless of whether missingness depends on the score. Under the null `E[X_j,t | full prior history] <= 0`, also `E[Y_j,t | full prior history] <= 0`. Each product `prod_s(1 + lambda Y_j,s)` is a nonnegative supermartingale for fixed `lambda in [0,1)`. A fixed mixture of those products is too. Ville's inequality and a union bound with `alpha/M` for `M` pre-registered candidates control the probability of *any* false rejection at any time by alpha. Dependence between candidates **within a round** is allowed. The theorem does **not** make the underlying null true.

`opportunity_gate.py` is a fixed-roster prototype with sequential round IDs, atomic validation, and `-1` for both omitted and explicit `None` candidate scores. It rejects invalid score types, unknown candidates, skipped/duplicate round numbers. Its **critical limitation** is that an untrusted caller can drop an *entire* round and renumber later rounds. It cannot independently verify that all opportunities were submitted.

## Verified local evidence

`python -m unittest -v test_opportunity_gate.py`: **11/11 pass**, including exact enumeration of fair signs under outcome-dependent observation rules, exact two-agent familywise error check, and an explicit adversarial omitted-round counterexample.

`python benchmark.py > results.json`: **600 seeded trials per scenario**, **100 opportunities/trial**, **8 agents**, alpha=.05, fixed mixture lambda=(.05,.1,.2,.4,.8). In the two all-null cases, the naive `missing -> 0` strategy reports any false rejection in **600/600** trials when only positive observations are logged. Conservative `missing -> -1` reports **14/600 (2.33%)** for independent SEO-like scores and **4/600 (0.67%)** for finance-like fresh same-round correlated shocks. These are empirical rates, not formal confidence bounds. With full data and positive alternatives, both approaches report any crossing in **600/600** trials. With random 50% missing under positive alternatives, naive reports **499/600 (83.17%)**, conservative **0/600**: validity costs substantial power.

## Counterexample that limits the result

Take 120 alternating deterministic +1/-1 source opportunities (balanced overall). A malicious logger omits every -1 *entire round* and renumbers the remaining +1 rounds 1..60. The gate sees no missingness and rejects. **No in-process gate can prove that an untrusted upstream logger enumerated all opportunities.** Use an independent append-only opportunity manifest or a trusted scheduled source, and reconcile IDs before making claims. Even a manifest cannot repair persistent across-round confounding that violates the conditional-null assumption.

## Reproduction

```sh
cd experiments/khepri/exp425
python -m unittest -v test_opportunity_gate.py
python benchmark.py > results.json
```

**Transferable lesson:** when outcomes are bounded, replacing missing measurements by the worst allowed score is a mathematically safe response to arbitrary score-dependent missingness *provided the opportunity count itself is independently trusted*. This may destroy statistical power, so missingness rates should be reported alongside any positive claim. This is a research prototype, not a production causal or security guarantee.
