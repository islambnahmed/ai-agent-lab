# Khepri experiment 395 — point-in-time vintages (synthetic)

## Question
Can an offline evaluation look artificially better because it uses revisions that were not available at decision time? **Yes.** Backdated provider publication times are not proof of historical availability.

## Reproduce
Node.js >=22; no dependencies:
```sh
node --test experiments/khepri/exp395/vintage_gate.test.mjs
node experiments/khepri/exp395/benchmark.mjs
```
13/13 local tests passed. Seeded 12,000 synthetic trials per domain.

## Policies
- Latest: highest source revision from the entire dataset, regardless of arrival.
- Provider cutoff: source-claimed publication time at/before decision; vulnerable to backdating.
- Trusted receipt snapshot: last actual ingestion at/before decision with effective observation time at/before decision; abstains if none.

| Domain | Policy | Future-received selections / 12,000 | Coverage | Relative RMSE |
|---|---|---:|---:|---:|
| Gold-like | latest | 8,390 | 100% | 0.00101 |
| Gold-like | provider cutoff | 5,095 | 100% | 0.01440 |
| Gold-like | receipt snapshot | **0** | 89.67% | 0.01657 |
| SEO-like | latest | 8,371 | 100% | 0.00232 |
| SEO-like | provider cutoff | 5,064 | 100% | 0.03262 |
| SEO-like | receipt snapshot | **0** | 90.02% | 0.03769 |

Revisions are 70% late and 50% have backdated provider times; initial receipts arrive late 15% of the time. Revisions are artificially more accurate. Thus the **lowest hindsight error is the most leaky**. This is a counterexample to treating low backtest RMSE as evidence of deployable quality.

## Limitations
The safety property requires a truly trusted, immutable, non-backdatable ingestion ledger. This in-memory prototype cannot authenticate the caller-supplied receipt time, does not persist after restart, and does not resolve multi-source disagreements. Synthetic trials are not calibrated to real gold/SEO data. No live feed, production deployment, trading action, or main-branch modification.

## Lesson
Historical evaluations must reconstruct the information set available at each decision time. Do not silently backfill missing vintages with future revisions. Compose this temporal gate with source-lineage verification (exp394) only after validating the ingestion provenance.
