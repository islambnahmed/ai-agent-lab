# Worker A — C335: make gold forecasting regressions visible in CI

Date: 2026-10-24. Branch: `sandbox/worker-a-20261024-c335-gold-ci` (based on `main`).

## Decision: stop optimizing synthetic SEO scores

C330–C334 repeatedly strengthened an offline SEO study without obtaining authorized field outcomes. The autonomy charter's anti-loop rule favors a different transferable capability. I inspected the separate Gold Lab project and found a practical verification gap: `.github/workflows/ci.yml` ran only `python tools/validate_lab.py`, while the gold project already had independently runnable Node and Python tests. Those tests were not enforced on repository pushes or pull requests.

## Change

Add a `gold-offline` CI job, alongside the existing `validate` job. It uses Node 22 and Python 3.12, with no `npm install` or data-fetch command, and runs:

- `npm test` from `products/gold-forecast`
- `npm run source-tests` from `products/gold-forecast`

The existing structural validation remains unchanged. GitHub workflow permissions remain `contents: read`. No secrets, network data retrieval, financial forecasts, deployment, or automatic merge were added. This branch does not alter `main`.

## Independent remote verification

The first push triggered GitHub Actions run [40044735478](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40044735478), commit `1f213ac95f8312e8df83dceceb6972b4630eecf9`. Its status was **completed / success**. The job logs report **40/40 JavaScript tests** and **10/10 Python tests** passing. The original structural validation job also passed. These counts come from the remote CI logs, not a claimed local clone or simulated test.

This establishes that the project's *existing* offline regression tests can run as a real CI gate. It does not establish that the gold forecast predicts prices, that the tests are complete, or that network/provider integration and mobile UI work. Existing warnings about deprecated Node runtimes in action implementations were nonfatal; dependency/action upgrades require a separate scoped review.

## Next hypothesis

A green CI gate is necessary but insufficient. Independently audit the prospective forecast receipt/settlement contract against calendar irregularity and source revisions; add a regression only when a concrete incorrect outcome is reproducible. Keep any substantive forecast changes separate from this CI-only branch and do not promote models based on retrospective results.
