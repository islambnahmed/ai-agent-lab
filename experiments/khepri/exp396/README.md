# Khepri exp396 — receipt order is not observation order

## Question and counterexample
Does exp395's trusted receipt snapshot always return the freshest *observation* available at a decision? **No.** It sorts by `receivedAt` first. A correction to an older observation can arrive after a newer observation and displace it. This is not future-data leakage; it is a distinct **observation freshness** error. If the intended query is "last received update", exp395 is behaving as specified. The bug arises when consumers interpret that result as "latest observed value".

Concrete reproduction: observation t-1000 arrives at t-500; observation t-100 arrives at t-300; correction to t-1000 arrives at t-50. At decision t, exp395 returns the correction to t-1000; the new selector returns t-100.

## Reproduce
Node.js 22+, no dependencies; this branch includes exp395's original module:
```sh
node --test experiments/khepri/exp396/latest_observation.test.mjs
node experiments/khepri/exp396/benchmark.mjs
```
9/9 local tests passed. Fixed seed 3962026; 10,000 synthetic trials per domain.

## Selection semantics
- **Receipt-first (exp395)**: choose largest `receivedAt` among observations with `receivedAt <= decisionAt` and `effectiveAt <= decisionAt`.
- **Observation-first (exp396)**: choose largest `effectiveAt` among those same eligible observations, then choose the latest `receivedAt` vintage for that observation. Revision and ID break ties deterministically.
- Both abstain if no eligible observation passes `maxAge` (age is measured from `effectiveAt`, not revision arrival).
- For a newly observed point not yet received, the selector correctly falls back to the most recent *available* older point; it never backfills a future receipt.

## Synthetic results
| Domain | Receipt-first chose old observation despite newer one being available | Observation-first | Receipt-first relative RMSE | Observation-first relative RMSE |
|---|---:|---:|---:|---:|
| Gold-like | 4,529 / 10,000 | 0 | 0.01494 | 0.00652 |
| SEO-like | 4,459 / 10,000 | 0 | 0.07678 | 0.03333 |

Both approaches had **zero future-received selections** in this test. The 10% of trials with the newest observation not yet received are not errors; both policies use older available data. Simulated drift and arrival probabilities were deliberately constructed to stress this semantic distinction. RMSE improvements are scenario-dependent, not evidence of improved real-world forecasting accuracy.

## Boundaries and next step
This selector assumes the exp395 ledger's receipt timestamps are trustworthy, the `effectiveAt` values correspond to comparable observation times, and the query is for a single series with a coherent cadence/source. It does not validate price truth, authenticate timestamps, deduplicate cross-source reports, or address outliers. A revision with a forged later `effectiveAt` can still appear fresh. For production, explicitly separate APIs: `latest_received_update_as_of` versus `latest_observation_as_of`; add source-specific identity and immutable receipt verification. Do not silently change the existing exp395 function's semantics.

No live data, trading, external effects, main-branch modifications, or production deployment.
