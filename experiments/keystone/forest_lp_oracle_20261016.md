# Keystone: independent forest-bounds LP oracle (2026-10-16)

## Question
The repository's `tools/dependence_bounds.py` claims an exact, dependency-free formula for the all-fail probability bounds when the supplied pairwise graph is a forest, including disconnected components and arbitrary numbers of modes. Does the formula agree with a general linear-programming oracle?

## Method
Read the implementation from main (tree at `8d8b4be50acc22e94882610d834e6f17b459b275`). Built an **independent research-only** oracle with SciPy `linprog(method='highs')`, not a production dependency. Enumerated all `2**n` binary worlds, constrained normalization, each marginal, and selected pairwise joints, then separately minimized/maximized the all-ones world probability. Compared those extrema with the closed-form forest-component formula.

Deterministic `numpy.random.default_rng(418)`; `n=3..8`; 300 distributions per n = **1,800 feasible tests**. Per n: 3 Dirichlet concentration levels (`alpha=0.02, 1, 100`), 4 graph families (chain, star, random forest, disconnected), 25 trials per combination. Pairwise probabilities derived from sampled joint distributions, guaranteeing mathematical feasibility. LP used `primal_feasibility_tolerance=1e-9` and `dual_feasibility_tolerance=1e-9`.

## Result
**1,800/1,800 matched within 1e-7**. Maximum absolute discrepancy was **8.833208406479433e-10**. No counterexample found. With default HiGHS tolerances the maximum discrepancy had been **7.527905254711698e-08**, illustrating why near-boundary tests need explicit numerical tolerances.

## Interpretation / limitations
This is randomized corroboration, **not a proof** that the forest formula is exact for all admissible inputs. It does not cover infeasible constraints, cyclic graphs, arbitrary n, or stability at probabilities below the LP's feasibility tolerance. SciPy is only an independent research oracle; production remains dependency-free.

## Next useful experiments
Test globally infeasible *cyclic* pairwise inputs that pass each individual Frechet check, and compare the 4-mode vertex enumerator to the LP oracle at extreme sparse and near-degenerate distributions. Prefer a reproducible failing case over additional random successes. Do not modify production behavior based on this passing audit alone.
