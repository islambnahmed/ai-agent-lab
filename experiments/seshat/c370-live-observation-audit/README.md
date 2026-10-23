# Seshat C370 — live provider observation probe (2026-10-23)

## Hypothesis
The seven-observation forecast may now have a target close in the provider's current feed, but no result should be presented as a certified prospective outcome without its original issue-time vintage and independent publication evidence.

## Method
`probe.mjs` fetches **only the exact public 1y URL pinned in the committed h7 receipt** and checks JSON shape, UTC daily close completeness, current origin close agreement, provider cadence and the seventh observation strictly after the origin. It prints the date, price, error comparison, source attribution, fetch time and raw SHA-256, **without storing or redistributing raw feed data**. If the origin price changed or is missing, the probe fails closed. A successful probe is still marked `tentative_current_vintage` rather than certified. No settlement or outcome-lock write occurs.

Run `node --test experiments/seshat/c370-live-observation-audit/probe.test.mjs` locally, then `node experiments/seshat/c370-live-observation-audit/probe.mjs` in an environment with internet. A push to the experimental branch runs the same probe in GitHub Actions with read-only permissions, providing a server-timestamped execution log. Network errors are explicitly reported, never converted into synthetic prices.

## Limits
The original `historyHash` vintage was not recovered; matching the pinned origin close is necessary but not sufficient to establish an unchanged historical sequence. The provider may revise prices, and the run timestamp only proves when the GitHub runner made the request, **not when the provider originally published the target**. One observation per UTC day is a parser convention, not an exchange calendar guarantee. This experiment is about data availability, not predictive skill.

## Source
Data by Standard Bullion — https://standardbullion.com/gold-price-api
