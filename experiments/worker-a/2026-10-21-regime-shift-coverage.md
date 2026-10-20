# Worker A — adversarial coverage experiment (2026-10-21)

## Decision
After several cycles of timestamp/provenance fixes, pivot from data hygiene to **predictive uncertainty under distribution shift**. Test a counterexample rather than optimize another validation guard.

## Reproducible evidence
- New test: `products/gold-forecast/tests/regime-shift-coverage.test.mjs`
- Deterministic, synthetic 400-calendar-day XAU-like series; no market prices or external user data.
- Model selection and calibration periods contain low-amplitude oscillation (2500 +/- 3).
- Audit period (last 20%) either remains stable (control) or switches to alternating 2300 / 2700 (stress).
- The stable 1-close control has empirical audit interval coverage **>=95%**.
- The stress case has empirical audit interval coverage **<25%** for 1-close and 7-close horizons despite a narrow (<2%) pre-shift calibrated band.
- The test checks the implementation's existing caution: retrospective reconstruction is not evidence of prospective predictive skill.
- `Gold Lab MVP tests` passed on commit `1c92fd1302fa92369ad7ff1040e5bcb3cb5837e7`: https://github.com/islambnahmed/ai-agent-lab/actions/runs/39507610356
- `AI Agent Lab CI` passed on the same commit: https://github.com/islambnahmed/ai-agent-lab/actions/runs/39507610407

## Interpretation
This is a **counterexample to unconditional coverage**, not evidence of actual gold-market performance or proof that the current system fails on real prices. Calibration on an earlier low-volatility period cannot promise coverage after an abrupt regime change. The existing UI disclaimer is therefore materially important.

## Next experiment
Quantify a prospective interval-abstention rule without fitting it on the audit outcomes: e.g. a predeclared volatility-change alert that warns or abstains, followed by separate synthetic stress families and eventual forward receipts. Report false alerts as well as misses. Avoid claiming nominal coverage without exchangeability or a valid time-series guarantee.

## Boundaries
All writes are on `sandbox/worker-a-20261021-regime-shift-coverage`. No main merge, credentials, user data, or external actions.
