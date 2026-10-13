# Khepri exp157 — asymmetric forecast bands can fail at long horizons
Date: 2026-10-13. Research only; synthetic price paths, no gold-market claim.

**Question:** Does causal 10th/90th-percentile signed-return calibration beat symmetric 80th-percentile absolute-return calibration under the proper 80% interval score?

**Method:** 48 seeded independent synthetic price paths per scenario; 4 scenarios (Gaussian, left-tail shock, right-tail shock, left-to-right reversal); horizons 1/7/30; 250 historical training origins with matured outcomes only (j+h<=t); evaluation origins 1200..1840-h, strides 7 and 30. Score=(interval width + 10 * out-of-band distance)/origin price. Lower is better. Paired bootstrap resamples paths, not overlapping forecasts.

**Stride-7 relative interval-score improvement of asymmetric vs symmetric (h=1 / 7 / 30):**
- Gaussian: -0.13% / -2.02% / **-7.80%**.
- Left-tail shocks: +1.73% / **+12.70%** / -2.24%.
- Right-tail shocks: +1.53% / **+14.71%** / +2.32%.
- Tail reversal: +0.90% / +11.17% / +0.84%.

**Key counterexample:** Gaussian h=30 coverage is **74.50%** with asymmetric vs **79.24%** symmetric, despite nominal 80%. Right-tail h=30 coverage 71.92% vs 77.56% even when asymmetric score is slightly better. For stride=30, Gaussian h=30 asymmetric score remains 8.62% worse; coverage 73.61% vs 79.96%.

Path-level bootstrap 95% intervals for absolute interval-score difference (symmetric minus asymmetric, normalized percentage points): left h=7 +1.65 [1.46,1.83]; right h=7 +2.03 [1.81,2.24]; Gaussian h=30 -1.22 [-1.57,-0.85].

**Tests:** 7/7 pass locally, including no-future-data prefix invariance, maturation, price-scale invariance, constant prices, and malformed input rejection. Synthetic results only. No production change. A better interval score does not ensure adequate coverage. Long-horizon overlapping residuals reduce effective tail information; that is a plausible mechanism, not proven causal attribution.

**Decision:** Keep symmetric as the default; research signed quantiles only as a horizon-specific candidate. Require score **and** coverage, plus independent gold receipts, before any promotion. Local reproducible bundle: khepri_exp157_reproducible.zip (generated during this cycle; not automatically synced into GitHub).
