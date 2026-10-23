# Seshat C373 — All-offset phase sensitivity, not another source-definition gate

Date: 2026-10-23. Following C370–C372's repeated price-vintage/source-definition blockers, deliberately switch to a falsifiable **evaluation stability** question: **does a reported disjoint backtest result depend on the arbitrarily selected starting phase?**

## Pre-registered method (before live result)

1. Fetch Standard Bullion's public rolling one-year XAU/USD daily history once on GitHub Actions. Validate with the existing production parser. Log only SHA-256 and derived metrics, not licensed raw history.
2. Recompute existing *unchanged* model selection and audit rows for horizons 1, 7 and 30. Do not tune the model or change main.
3. For each horizon h, rotate the disjoint slice through **all h offsets**, not only offset zero. For each offset log count, paired model/baseline MAE, relative MAE skill, win/loss/tie counts. Also log pooled MAE skill across every overlapping audit origin.
4. Classify direction as mixed_sign, nonnegative_all_phases, nonpositive_all_phases, or no_direction. This is a *descriptive* phase-sensitivity diagnostic, not a hypothesis test. Do not treat any phase as an independent experiment.
5. Treat any phase with only 1–2 windows as **too small for inferential claims**. If the GitHub probe fails, retain the six successful offline unit tests and explicitly report the failure; never invent live results.

## Existing evidence motivating the test

The 2026-10-12 readiness report shows **H7 pooled skill −3.056%** (59 overlapping origins) but the chosen offset-zero disjoint sample shows MAE **115.47** versus baseline **119.28** (9 origins), a sign reversal. H30 pooled skill **−14.33%** (36 overlapping origins) but offset-zero disjoint sample contains only **2 origins**. Without the other phase offsets, the disjoint headline can mislead even when no selection bias was intended.

## Run

Offline: node --test experiments/seshat/c373-phase-rotation/phase_metrics.test.mjs

Live: node experiments/seshat/c373-phase-rotation/live_phase_probe.mjs

The GitHub Actions workflow has contents: read only and prints a current-vintage descriptive report. A successful run would not certify the historical close or prove predictive skill. Original forecast receipts and main are unchanged.

## Next decision

If mixed-sign phases are observed, explicitly avoid quoting a single-offset disjoint MAE as model advantage. For future prospective evaluation, preregister issuance/settlement rules and collect enough non-overlapping genuinely forward outcomes; do not repeatedly retune the same inspected historical period.
