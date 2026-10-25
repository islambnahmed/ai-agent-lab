# Khepri exp434 — point-in-time feature revisions and evaluation leakage

**2026-10-25 · offline, synthetic, standard-library Python · no production connections**

## Question

Can an agent's evaluation look excellent even with chronological train/test splits, simply because historical feature tables contain revisions published *after* the decisions being evaluated? Can a point-in-time join eliminate this failure mode, and does the result transfer across different reporting delays and class prevalences?

This changes direction from exp431–433's test-portfolio optimization to **evaluation validity**: a seemingly high-performing model may be measuring unavailable hindsight, not forecasting skill.

## Prototype

`pit_eval.py` defines `Example` (decision time, binary label, label maturity time) and `Revision` (observation time, publication/availability time, revision number, binary feature value). The strict snapshot picks the most recent feature revision with **both** `observed_at <= decision_at` and `available_at <= decision_at`. The intentionally leaky comparator uses the latest historical revision, regardless of publication time. Both policies use the **same** chronological walk-forward folds and train a one-feature binary stump **only on each fold's training examples**. Training examples are excluded unless their labels are mature at the start of that fold's test period. The `gap` option excludes a specified number of immediately preceding rows.

Each synthetic example has an early, weakly predictive preliminary observation and a delayed, nearly label-perfect revised observation. Both revisions describe the same earlier observation date. In real systems this resembles retrospective backfilling of price reconciliation or search-performance reports; the simulation intentionally makes the revision depend on the future label to create a controlled counterexample. **This is not a claim that actual gold or SEO datasets behave this way.**

- Gold: balanced classes, early-signal accuracy ~56%, revised-signal accuracy ~98.5%, revision delay 1 time unit, label delay 2.
- SEO: positive-class prevalence ~38%, early-signal accuracy ~61%, revised-signal accuracy ~97%, revision delay 7 time units, label delay 14.
- 360 examples per domain, 7 walk-forward folds of 40 test examples each, 280 out-of-sample decisions evaluated per domain and seed.

## Reproduce

From this directory:

```bash
python -m unittest -v test_pit_eval.py
python pit_eval.py
python stress.py
```

`stress.py` runs 200 deterministic seeds per domain (400 domain/seed datasets, 112,000 held-out decisions per policy) plus 200 negative-control datasets per domain in which delayed revisions are randomized independently of the labels. No internet, dependencies, or credentials required.

## Observed results

| Domain | Single-seed strict | Single-seed leaky | 200-seed strict mean | 200-seed leaky mean | Mean inflation | Min inflation |
|---|---:|---:|---:|---:|---:|---:|
| Gold | 151/280 (53.93%) | 271/280 (96.79%) | 54.88% | 98.61% | +43.73 pp | +32.50 pp |
| SEO | 186/280 (66.43%) | 276/280 (98.57%) | 61.71% | 97.07% | +35.36 pp | +27.50 pp |

Inflation was positive in **200/200 seeds per domain**. All delayed final revisions in this synthetic setup were unavailable at decision time. The early features were always available.

**Negative control:** When delayed revisions were replaced by independent random bits, mean leaky accuracy was **49.97% gold** and **61.32% SEO**, versus strict **54.88% gold** and **61.71% SEO**. The inflated scores are thus not caused merely by selecting later revisions or by the chronological split; they require the later revisions to carry information correlated with the outcome. The SEO negative control's ~61% is consistent with majority-class prediction under imbalanced labels, not real forecasting skill.

`test_pit_eval.py` includes unit tests for availability gating, future-observation exclusion, revision tie-breaking, missing-feature fallback, chronological label-maturity filtering, duplicate keys, both domain transfers, and a metamorphic test: arbitrarily flipping **future** revisions cannot change the strict feature snapshot but changes the leaky snapshot.

## Counterexamples, assumptions, limitations

1. **Chronological CV is insufficient** when test features are retrospectively backfilled. An as-of join is required in addition to temporal splits.
2. **Not all revisions are leakage.** If a revision was truly available at the decision time, strict evaluation permits it; if later revisions contain no outcome information, the inflated score disappears (negative control).
3. **Availability timestamps must be authentic.** If the source backdates `available_at`, this algorithm cannot detect the fraud; immutable source snapshots or independently timestamped ingestion records are needed.
4. **No causal or market claims.** Gold and SEO are different synthetic delay/prevalence regimes; labels and revisions are intentionally generated to expose failure. The learner is a one-feature stump, not a competitive forecasting model.
5. **Clock semantics matter.** Time units are integer abstractions; label availability at exactly the test cutoff is assumed usable. Real systems need timezone, release-time, clock-skew and ingestion-lag policies.
6. **Gap is a row count**, not a calendar embargo. Overlapping targets, entity grouping, and serial correlation require additional purging beyond this minimal example.
7. **No performance guarantee.** Point-in-time correctness prevents one identifiable leakage channel; it cannot guarantee generalization or protect against other confounding and data-quality failures.

## Reusable lesson

Every predictive feature needs a *decision-time availability contract*, not just an event timestamp. Evaluate on the feature values and labels actually available at the time. A high backtest score without as-of provenance is untrustworthy even when the train/test split is chronological. The counterexample and negative control distinguish leakage-driven optimism from ordinary revisions and class imbalance.
