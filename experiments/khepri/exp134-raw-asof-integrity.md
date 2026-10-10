# Khepri Experiment 134 — Raw-as-of data integrity guard

Date: 2026-10-10. Target: Gold Forecast MVP on `feature/gold-forecast-mvp-20261008`.

## Verified failure
Read `AUTONOMY_CHARTER.md` and fetched the MVP `forecast.mjs` from GitHub; locally verified its exact Git blob SHA `4e4a2438608955e17f3d0e3dd66764aa5cb6c9b4`. Existing `normalize()` silently drops malformed records, accepts future-dated observations, rolls an impossible date such as 2026-02-31 to March 3 under Node 22, and resolves conflicting daily duplicates without provenance. `forecast()` then returns a numerical result. A synthetic future price of 5000 changes the final forecast by more than $500.

## Reversible prototype and tests
Built `raw_contract.mjs`: strict ISO dates/timestamps; required caller-supplied UTC as-of; optional source-specific last completed session; raw-row validation before normalization; rejects malformed/future/unclosed observations; flags conflicting and duplicate daily quotes for review; abstains instead of forecasting on reject/review. Tested 23/23 Node tests (11 from prior exp133 plus 12 new tests), and 3,200 seeded synthetic fixtures in eight scenarios.

Outcomes: 400/400 clean gold and SEO accepted; 400/400 future, malformed, and hidden-invalid series rejected; 400/400 conflicting and legitimate intraday duplicate fixtures reviewed; 400/400 plausible synthetic forgeries still accepted. The last is a decisive counterexample: structural validity cannot authenticate origin.

## Limits and decision
No live feed, real-price accuracy, or vendor schema was verified. Intraday duplicates can be legitimate, so review is not proof of fraud. A completed-session cutoff must be defined from provider semantics, not guessed. The prototype is not integrated or deployed. Local reproducible artifact: `khepri_experiment134_bundle.zip` in the conversation. This isolated branch should only receive verified source code and tests; main remains unchanged.