# Seshat C372 — Historical-close definition firewall (2026-10-23)

## Decision

**Do not certify H7 by treating a second website's same-calendar-date number as an interchangeable settlement.** The observed target date, 2026-10-18, was a **Sunday**. The pinned forecast measures **seven observations from Standard Bullion's historical feed**, not seven London business-day auctions. The provider describes its daily close as its **last captured quote of the day**; its live quote is an indicative dealer bid/ask. This is not necessarily equivalent to another site's “daily close,” and it is not an LBMA Sunday fixing.

## Sources and independently visible values

- Original forecast and provider observation: [C371 report](../c371-observed-h7-evidence/README.md); [GitHub-hosted probe execution](https://github.com/islambnahmed/ai-agent-lab/actions/runs/39993282182), 2026-10-23 17:13:30 UTC. Standard Bullion Oct 18 daily point **4192.32 USD/troy oz**; observation remains `tentative_current_vintage`.
- [Standard Bullion API methodology](https://standardbullion.com/gold-price-api) and [terms](https://standardbullion.com/market-data): daily closes are last capture of the day, live quotes are dealer quotes, historical pre-capture series includes published LBMA/USGS data; provider terms forbid bulk redistribution. Thus a rolling 1y response is not a guaranteed original vintage.
- [GoldPrice.org October 18, 2026 page](https://goldprice.org/gold-price-today/2026-10-18): lists **4165.56 USD/troy oz** as a Sunday close. This is a different published figure, **26.76 USD** lower. Its exact close timestamp, quote construction, and publication-time archive have not been established; it is **not a verified same-definition substitute**.
- [LBMA value dates](https://www.lbma.org.uk/prices-and-data/value-dates) concern London business-day conventions; a Sunday dealer quote should not be labeled a London benchmark auction.

## Numerical sensitivity (not a certified settlement)

Pinned forecast = **4225.483424799358**, no-change baseline = **4207.98**. For absolute error, the model is better only if the target price is above **4216.731712399678**; the baseline is better below it.

| Candidate Oct 18 price | Model absolute error | Baseline absolute error | Winner for this candidate |
|---|---:|---:|---|
| Standard Bullion current-vintage 4192.32 | 33.1634 | 15.6600 | baseline |
| GoldPrice.org site close 4165.56 | 59.9234 | 42.4200 | baseline |

The baseline wins under both *candidate numbers*. This robustness is useful, but the numbers are not equivalent observations and **do not certify** a prospective score, an original-price vintage, or any general predictive-skill claim.

## Reproducible guard

`definition_gate.mjs` rejects cross-source certification when source identity, instrument, unit, calendar date, close method, clock basis, or independent release evidence is missing or incompatible. Even with comparable inputs it reports only threshold consistency, not source independence or vintage integrity. `definition_gate.test.mjs` has nine offline tests, including the false-equivalence trap and the exact H7 decision boundary.

Run: `node --test experiments/seshat/c372-close-definition-gate/definition_gate.test.mjs`.

## Next discriminating experiment

1. Obtain the provider's documented timestamp/market-session cutoff and a lawful independently timestamped same-definition historical snapshot, or mark verification **unavailable**.
2. Keep the original 2026-10-12 prefix hash mismatch/unavailable-history limitation explicit. The original raw response was not retained; a current feed cannot reconstruct its vintage.
3. Avoid adding more complex settlement logic until an independent *comparable* price and release-time record exists. New forecasts should preserve lawful source snapshots or verifiable manifests at issuance.

No changes to `main`; no live market feed is stored here. This is a definition check and a sensitivity experiment, not financial advice.
