# Keystone: freshness-gated point-in-time gold evaluation

Run: `python -m unittest discover -s tests -p 'test_gold*.py'`.

Use `tools.gold_quality_gate.audit(rows, horizon=3, train_min=10)` on parsed `date,close,available_at` observations (timezone-aware ISO publication times). The base evaluator forecasts at the start of the next UTC day, never at the origin row's potentially late publication time. Missing published observations are handled with observation-index-adjusted drift.

A synthetic counterexample: 80 observations; delay releases for indices 10–44 by 100 days; horizon 3; train_min 10. Raw coverage is 23/23 = 100%, but 11/23 forecasts are stale and only 12/23 have a fresh origin. The fresh-only quality gate correctly returns insufficient_fresh_windows.

`ready_for_holdout` means only that at least 20 fresh-origin windows exist. It is NOT evidence of a trading edge. Real price feeds and publication timestamps remain unverified. Raw and fresh-only metrics must not be confused; a later untouched holdout is still required.
