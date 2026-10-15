# Worker A — Cycle 137: interval quality is not coverage alone (2026-10-15)

## Why this direction
Cycles 130–133 showed that a volatility proxy can raise empirical coverage simply by widening intervals. A coverage-only dashboard can reward an uninformative interval. This cycle changes strategy from source-vintage repairs to a **proper interval scoring rule**.

## Independently checked prospective receipts
Source: `products/gold-forecast/reports/prospective/2026-10-11-h{1,7,30}.json` on `main`, retrieved on 2026-10-15. All issued 2026-10-12T17:12:52.272Z with origin 2026-10-11, source Standard Bullion, baseline USD 4,207.98/oz.

| Horizon (future observed closes) | Model | Band width (USD/oz) | Width / origin baseline |
|---|---|---:|---:|
| 1 | persistence | 193.9064 | 4.6081% |
| 7 | mean_reversion | 364.5762 | 8.6639% |
| 30 | momentum | 883.1464 | 20.9874% |

The 30-close interval is about 4.55x wider than the 1-close interval in percentage terms; horizons are different and **must not be pooled or compared as equivalent difficulty**.

**No actual outcomes were retrieved or authenticated in this cycle.** The three widths are issue-time descriptive facts, not coverage, accuracy, or skill estimates. The October 12 GitHub Actions run 38282833087 has **zero artifacts**, so it cannot supply the missing original provider snapshot.

## Scoring design
For central 80% intervals, the interval score is:
`S_0.2(l,u;y) = (u-l) + 10*(l-y) if y<l + 10*(y-u) if y>u`.
The two miss penalties are additive and zero inside the band. Lower is better. Compare *both* observed coverage and average interval score, plus normalized width and paired point/baseline absolute errors. Do not declare victory by coverage alone.

Counterexample: if actual=100, [99,101] and [80,120] both cover it (100% coverage), but their interval scores are 2 and 40. If actual=110, scores are 92 and 40, so the wider interval becomes preferable. This is why the scoring rule rewards sharpness without ignoring misses.

## Guardrails
The research-only Python module `experiments/worker_a/interval_quality.py` rejects invalid numbers, incomplete UTC target days, target/source mismatches, mixed horizons/sources/versions, duplicate receipt IDs, and empty outcome sets. A claimed outcome is **always labeled provisional**: its fields cannot independently prove publisher authenticity, receipt anchoring, raw hash integrity, or that it is exactly the h-th future observed close. It does not touch production code or automatically promote models.

Local verification: `python -m unittest -v test_interval_quality.py` passed **20 tests** in the local workspace. Repository CI is not yet verified; if publication succeeds, treat published code as an independent candidate pending CI.

## Next decision
Acquire source-authenticated, timestamped prospective outcomes; only then compute interval scores by horizon, preserving paired comparison with the same targets. If that evidence remains unavailable, pivot to independent reproducibility and publication-time data capture rather than inventing settlements.
