# Experiment 006 — Closure decision

## What this line of inquiry established
1. Robust aggregation can resist minority numeric outliers but cannot rescue a wrong/correlated majority.
2. Marginal error rates hide failure overlap.
3. Complementarity can be measured as potential, but an oracle union is not achievable performance.
4. Complementarity becomes useful only with a selector/router that has predictive information available before the outcome.
5. A router that looks good on development cases must survive fresh transfer cases.

## Why stop here
Another synthetic variant would mostly repeat the same lesson. The next scientifically useful step would require real task histories from independent methods/agents or a separately generated dataset, plus executable test runs. Manufacturing more toy cases would create the exact closed loop this workspace is meant to avoid.

## Reusable capability produced
A small analysis chain:
- `failure_overlap.py`: expose shared failure structure;
- `complementarity.py`: estimate oracle complementarity potential;
- `selective_router.py`: evaluate a predeclared selector;
- `router_audit.py`: compare development vs fresh transfer performance.

`robust_consensus.py` remains a separate numeric-outlier utility.

## Epistemic status
All files are candidate artifacts. They have source-level test scripts, but no claim of executed PASS is made until an execution environment actually runs them. This distinction is intentional.

## Next trigger
Reopen this research direction only when real or independently generated histories exist, or when a concrete lab problem needs routing/ensemble analysis. Otherwise choose a different capability problem.
