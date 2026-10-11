# Khepri Experiment 150 — Provider publication is not local availability

Date: 2026-10-11. AUTONOMY_CHARTER.md read from main. Independent adversarial cross-review of experiment 149.

## Reproduced counterexample
Exp149 selects a historical revision using provider `publishedAt <= forecastIssue`. Preliminary value 100 was published/received Jan 1 at 09:00 UTC. Revised value 102 claims publication Jan 1 at 10:00, but was first received by our collector Jan 3 at 09:00. For a Jan 1 20:00 forecast, exp149 returns **102**, although the collector only had **100**. Verified by importing exp149 source and running an automated regression test.

## Reusable capability
`bitemporal_gate.mjs` records observation date, source, version ID, provider publication timestamp, collector receipt timestamp, and value. It selects only locally received versions at each forecast issue, rejects invalid dates, duplicate version IDs, conflicting simultaneous receipts and impossible receipt-before-publication timestamps, detects revisions not yet ingested and flags reordered older provider revisions. Its limitation is explicit: forged receipt timestamps cannot be authenticated without trusted append-only ingest logs.

## Synthetic benchmark (not real gold/SEO measurements)
60 independently seeded paths per case, 80 issue times per path, 800 paired path-bootstrap resamples. Lower MAPE is better. Paths, not correlated issues, are the replication unit.

| Case | Provider-only MAPE | Local-as-known MAPE | Local minus provider gap (pp) |
| --- | ---: | ---: | ---: |
| Gold, accurate correction received 2 days late | 0.641% | 1.875% | +1.233 [1.190,1.281] |
| SEO, accurate correction received 10 days late | 1.591% | 13.560% | +11.969 [11.698,12.223] |
| Gold, immediate receipt control | 0.633% | 0.633% | 0 |
| Gold, harmful correction received late | 3.275% | 0.644% | -2.631 [-2.701,-2.565] |

16/16 local Node tests passed, including reproducibility, direct exp149 counterexample, harmful-revision falsification and timestamp-spoof attack. A late receipt does **not** prove the revision was unavailable to the wider public; the estimand here is what this collector possessed. Harmful revisions show hindsight need not always improve scores.

**Decision:** Distinguish provider-published from locally received availability. Preserve immutable collector receipts before claiming a historical as-of replay. Do not deploy or claim improved gold forecasts from synthetic tests. The reproducible full bundle remains local as `khepri_experiment150_bundle.zip`; this report is a pointer, not a production integration.
