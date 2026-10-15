# Worker A — Cycle 134: source-aware evidence gate (2026-10-15)

**New direction after cycles 130–133:** stop iterating on synthetic volatility proxies until the actual published gold reports are audited. This cycle reads the two *already committed* retrospective report artifacts; it does not download market prices, issue forecasts, alter production code, or assert new live skill.

## Verified source reports
- `products/gold-forecast/reports/research-benchmark-20261012.json` — HistData XAUUSD M1 bid aggregated to completed UTC-day close; 3,221 source rows; 2016-01-03 to 2026-05-31; report timestamp 2026-10-12T18:18:34Z.
- `products/gold-forecast/reports/readiness-20261012.json` — Standard Bullion indicative daily closes; 324 source rows; 2025-10-12 to 2026-10-11; report timestamp 2026-10-12T17:12:52Z.

**These are different price products, date ranges, model selections and audit windows. They must not be pooled or treated as a controlled head-to-head comparison.**

| Report | Horizon (future observed closes) | Model | Reported coverage / nominal 80% | Overlapping audit rows | First disjoint phase | Candidate vs baseline MAE |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| HistData research | 1 | persistence | 64.81% | 645 | 645 | 31.70 / 31.70 |
| HistData research | 7 | persistence | 63.85% | 639 | 92 | 88.84 / 88.84 |
| HistData research | 30 | persistence | 68.67% | 616 | 21 | 183.97 / 183.97 |
| Standard Bullion readiness | 1 | persistence | 90.77% | 65 | 65 | 39.41 / 39.41 |
| Standard Bullion readiness | 7 | mean_reversion | 77.97% | 59 | 9 | 122.52 / 118.88 |
| Standard Bullion readiness | 30 | momentum | 88.89% | 36 | **2** | **258.77 / 226.33** |

## Interpretation and corrective decision
1. The **longer HistData research series shows descriptive undercoverage** against the 80% nominal band on all three horizons. Its h1 audit has 418 covered of 645; the illustrative iid Wilson 95% interval is **61.04%–68.39%**. Market serial dependence means this is not a valid market-process confidence guarantee; it simply reinforces that the 64.81% observed fraction is far below nominal.
2. Standard Bullion's apparently attractive h30 coverage **88.89%** is based on 36 *overlapping* windows; the first non-overlapping phase has only **two** cases, and the selected momentum model has **14.33% worse MAE than persistence** in that retrospective audit. No deployment inference follows.
3. HistData h30 has 616 overlapping rows but only 21 first-phase non-overlapping rows. The `>=30` non-overlap requirement in the tool is an **explicit conservative policy threshold**, not a statistical theorem.
4. The two sources cannot validate one another's intervals without matched timestamps, measurement and issue-time availability. Different outcomes are not evidence of a bug or gain in isolation.
5. Previous synthetic proxy experiments are useful stress tests, **not a justification to promote** any proxy-scaled interval into the actual gold workflow.

## Reproducibility
```bash
cd experiments/worker_a
python3 evidence_gate.py --test
python3 evidence_gate.py ../../products/gold-forecast/reports/research-benchmark-20261012.json ../../products/gold-forecast/reports/readiness-20261012.json
```

The Python tool validates integer covered counts, phase partitions, disjoint first-phase counts, provenance, and prevents retrospective evidence from enabling automatic promotion. The local reference passed **10 tests** and was run against **derived aggregate-only snapshots transcribed from the two committed reports**. The published source was read back from GitHub; **GitHub CI has not been run on it**. The full raw source reports were inspected via GitHub but not copied into the local test environment.

## Next action
Seek genuinely prospective, Git-timestamped, mature forecast outcomes. Require frozen source vintages, outcome publication-time proof, and matched measurement before testing any interval adjustment. Until then, keep the production selector and bands unchanged. If new evidence remains sparse, invest in data freshness and independent audit rather than synthetic model tweaking.

**Status:** research diagnostic only; no market-performance claim; no production changes.
