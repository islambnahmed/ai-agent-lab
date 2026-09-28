# Evidence Aggregation 14 — Bounds Oracle Validation

## Goal
Validate the new small-n dependence-bounds oracle against a case where pairwise independence leaves higher-order dependence unidentified.

## Setup
Three binary latent failure modes each have marginal failure probability 0.2.

Known pairwise moments:
- P(X and Y fail) = 0.04
- P(X and Z fail) = 0.04
- P(Y and Z fail) = 0.04

These constraints make every pair independent, but do not impose mutual independence.

## Oracle result
The exact feasible interval for:

**P(at least one evidence path survives)**

is:

```
[0.96, 1.00]
```

The fully independent model gives:

```
1 - 0.2^3 = 0.992
```

which is only one admissible point inside the interval.

## Interpretation
Knowing all marginals plus all pairwise moments still leaves a four-percentage-point uncertainty band in this example. Reporting 0.992 as if identified would silently add a higher-order independence assumption.

The bounds oracle therefore changes the semantics of evidence aggregation:
- point estimates are appropriate only when sufficient dependence structure is justified;
- otherwise report a tight feasible interval;
- additional structural assumptions should be valued by how much they narrow a decision-relevant interval.

## Falsification target
A useful next attack is not another synthetic dependence example. Test whether the oracle itself is trustworthy:
1. compare it against analytically known Fréchet bounds;
2. generate feasible joint distributions and verify their target probabilities lie inside returned bounds;
3. test infeasible constraints;
4. search for numerical/vertex-enumeration failures near degenerate constraints.

If those survive, extend from n<=3 to a solver-backed general small-n implementation rather than hand-expanding special cases.
