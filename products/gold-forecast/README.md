# Gold Lab — Gold-price forecast MVP

First **product mission** for AI Agent Lab. Arabic-first, RTL, responsive static site with live and historical XAU/USD data, three transparent baseline forecasting models, and chronological backtesting against naive last-close. This is research software: **not an investment recommendation or proof of predictive skill**.

## Run

From the repository root:

    python -m http.server 8000 --directory products/gold-forecast

Open http://localhost:8000

No server API key or paid dependency. If the external price source fails, choose the explicitly labeled synthetic DEMO or import a local CSV with header \`date,price\`. No fake numbers silently replace live price.

## Tests

    node --test products/gold-forecast/tests/*.test.mjs

## Files

- \`index.html\` — accessible RTL dashboard with forecast chart and audit panel.
- \`app.mjs\` — read live/historical provider data, show failures, local CSV, synthetic demo.
- \`forecast.mjs\` — pure deterministic model selection and walk-forward audit.
- \`tests/forecast.test.mjs\` — reproducible no-API regression tests.

## Model evaluation and limitations

- Prices: dealer **bid/ask** and daily historical quotes from [Standard Bullion](https://standardbullion.com/gold-price-api), **not a universal spot trade price**. Mandatory attribution is visible in UI. Historical prices and live bid/ask represent different measurement types, so forecasts are anchored to the **historical close**, never to live bid or ask.
- Input: daily XAU/USD closes (USD per troy ounce). Forecast horizons are **1, 7, 30 trading sessions**; holiday dates are approximated by skipping weekends.
- Candidates: persistence (last close), capped/damped 20-session log-return momentum, and 40-session geometric-mean reversion.
- Training/selection: all candidate parameters fixed in code; select lowest MAE on earlier 80% using strictly earlier observations at each origin. Later **20% is held out for audit**; no model selection using audit results.
- Audit: show MAE (USD), MAPE, baseline MAE and empirical interval coverage. Prediction band uses the 80th percentile of prior validation percentage errors, **not a guaranteed 80% confidence interval**.
- Overlapping multi-day origins are correlated; historical comparison is descriptive, not a statistically significant demonstration of future edge.
- Current vendor accessibility, API response schema and CORS need real-browser end-to-end validation; unit tests are not a live-feed test.
- All unit tests use generated fixtures; **no real-market outperformance claim exists at this stage**.
- Stale historical closes get a warning rather than a fabricated new point.
- This version deliberately **does not call GPT or Claude** to output arbitrary prices. An optional LLM layer can later process grounded economic news and propose testable features, only after an ablation benchmark proves added value and costs are authorized.

## Agent-owned follow-up

1. **Khepri** — propose and benchmark predictive/uncertainty models; report losses.
2. **Seshat** — independently audit timestamp alignment, data leakage, overlapping holdout windows, and real-data backtests.
3. **Lumen** — verify source API, attribution/terms, provider redundancy, and stale quote detection.
4. **Keystone** — product integration, accessibility, mobile responsiveness, CI reliability, rollback.
5. **Worker A** — independent hypothesis generation on explainable features and failure modes.

These are suggestions, not a claim that any of the named agents is currently executing. The charter allows each to revise its approach.

### Gate to declare improvement

Pre-register a frozen benchmark using at least two real source cross-checks; publish timestamped prospective 1/7/30-session forecasts with no hindsight edits; compare each model against persistence on the *same* predictions and dates; include transaction/FX constraints before adding Egypt retail gold predictions. Do not publish claims of outperforming LLMs/markets until a repeatable evaluation actually supports it.

Deployment, API subscriptions, domains, account setup, automated live execution and spending require separate authorization.
