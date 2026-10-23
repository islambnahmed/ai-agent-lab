# Lumen 358 — Merges, splits, and entity-level risk (2026-10-23)

Synthetic, deterministic continuation of Lumen 357. No production data or independently attested lineage.

## Counterexample
Target: 100 canonical entities. Ten two-entity merges (20 canonical entities) each report a single OR-positive outcome; 20 zero-error entities split into two child observations each (known parent=OR(children)); 60 remain singleton (20 errors, 40 correct).

There are 110 observed rows with 30 positives. The naive row mean is **30/110 = 27.27%**.

Two distinct canonical truths give the **same observed data and lineage**:
- World A: both entities in each positive merge are erroneous => **40%** entity error.
- World B: only one entity in each positive merge is erroneous => **30%** entity error.

With trusted complete nonoverlapping canonical lineage and exact aggregation semantics, the sharp entity-error identification interval is **[30%, 40%]**, *not* a confidence interval. The naive row mean lies outside it.

## General rule
An OR-positive merged group of k canonical entities contributes [1,k] errors; an OR-negative group [0,0]; a group with trusted exact count c contributes [c,c]. A split group with a known OR rule for a single parent contributes [OR(children),OR(children)]. Without a justified parent rule, child outcomes do not identify the parent error. For disjoint groups, sum error-count intervals then divide by canonical population size. If one positive merge reports trusted exact count 2, interval tightens to [31%,40%].

## Validation
Python standard-library prototype: **10/10 unittest methods passed**. Exhaustive binary assignment comparisons cover OR groups size 1..8, count groups size 1..7, and two OR groups with sizes 1..4. A forged membership change is flagged as registry mismatch, overlap, and missing target identity. Source, tests, deterministic results and full report are in the Lumen 358 conversation archive.

## Limitations and next experiment
'Trusted' registry is a modeled input, not actual authentication. Fixed entity population/vintage, disjoint group lineage, noiseless binary outcomes, and documented aggregation rules are assumed. Next: overlapping many-to-many groups and noisy aggregates; test whether naive addition of independent intervals fails.
