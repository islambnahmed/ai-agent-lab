# Coverage denominator audit — Lumen (2026-10-10)

Source reviewed: `products/gold-forecast/forecast.mjs`, Git blob `4e4a2438608955e17f3d0e3dd66764aa5cb6c9b4`.

**Confirmed defect:** `sample()` computes `mape=abs(predicted-actual)/actual`, and `forecast()` uses that ratio both to set `band` and count `coverage`. But the visible interval is `[predicted*(1-band), predicted*(1+band)]`. Membership in that displayed interval requires `abs(predicted-actual)/predicted <= band`. Consequently the displayed holdout coverage and reported coverage disagree. Example: predicted=100, actual=110, band=0.095: reported covered, displayed interval [90.5,109.5] excludes actual.

Independent deterministic synthetic audit (100 seeds per regime, 360 trading observations each): at 30-session horizon, stationary reported 76.72% vs displayed 74.93%; acceleration reported 16.84% vs displayed 14.63%. On individual paths the gap reached 30.23 percentage points. These are synthetic stress results, not real gold-market evidence.

**Minimal reversible fix:** keep `mape` for the MAPE metric, add `bandError=abs(predicted-actual)/predicted` in `sample()`, and use `bandError` for both the 80th-percentile band and the holdout coverage. Add a regression that reconstructs the holdout interval at every origin and asserts equality to reported coverage. Do not publish until the fix passes CI and browser checks.
