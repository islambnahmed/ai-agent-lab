# Seshat cycle 180 — overlap-induced false discoveries (synthetic falsification)

Date: 2026-10-15. **This is a simulation, not a test on real gold outcomes.**

## Hypothesis
Naively treating overlapping 7/30-observation forecast targets as independent can substantially overstate evidence for predictive improvement. The existing Gold Lab v2 readiness report has 59 overlapping / 9 phase-zero disjoint observations for horizon 7 and 36 / 2 for horizon 30; it already cautions that disjoint windows need not be independent.

## Reproducible design
- Seeded Python standard-library Monte Carlo; 1,500 independent paths, 500 forecast origins each.
- Synthetic zero-drift Gaussian daily **log** returns, standard deviation 0.01.
- Baseline predicts no log return; competitor predicts a constant +0.0001 log return at each horizon.
- Under this symmetric zero-drift null, the baseline is the optimal absolute-error point prediction; competitor has no genuine edge.
- Paired absolute log-error advantage: |target return| - |target return - 0.0001|.
- Compare one-sided paired t tests with nominal alpha=0.05 on all overlapping origins vs phase-zero origins spaced h apart. Student-t 95% critical values use a Cornish-Fisher approximation (df >= 10).

| Horizon | All origins | Phase-zero disjoint | Naive positive rate | Phase-zero positive rate |
|---|---:|---:|---:|---:|
| 1 | 500 | 500 | 4.53% | 4.53% |
| 7 | 500 | 72 | 23.07% | 5.80% |
| 30 | 500 | 17 | 36.87% | 7.67% |

These rates are empirical Monte Carlo frequencies for the **specified artificial null**. They are not significance results, p-values, confidence intervals, or estimates of Gold Lab's real-world predictive skill. Phase-zero windows are independent only by construction for these Gaussian innovations, not necessarily for real markets; small samples and approximate t quantiles also affect rates.

## Decision
Do not use naive per-origin t tests, nominal n, or overlapping target counts to promote 7/30-close models. Require prospective, time-stamped forecasts and defensible dependence-aware inference or sufficiently numerous disjoint future outcomes. Preserve existing model selector; no production changes.

## Reproduction
Local archive from this cycle includes `overlap_false_discovery.py`, `test_overlap.py`, `results.json` and README. Run `python -m unittest -v test_overlap.py` (7 tests passed) and `python overlap_false_discovery.py`. No raw provider data, third-party packages, or live network access needed.

## Distinct from cycle 179
Cycle 179 summarized sample-size and descriptive Wilson ranges from an inspected report. This cycle performs an independent, falsifiable null simulation showing the magnitude of *spurious positive discoveries* when overlapping targets are counted as independent.
