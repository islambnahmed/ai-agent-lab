# Seshat Gold Cycle 28 — As-of data audit and October 2026 nowcast

Date: 2026-10-09. Research only, not investment advice.

## Verified correction
The World Bank's October 2, 2026 Pink Sheet reports September 2026 gold monthly average of **4319 USD/toz**. A forecast issued October 1 cannot use that published value. Earlier cycle 27 implicitly allowed previous-month prices at the beginning of each target month.

On the same 26-row historical dataset and 14 retrospective targets, publication-time sensitivity tests (hypothetical calendar: month M published day 2 of M+1) yield:

| Issue scenario | No-change MAE | Endpoint drift MAE | Drift versus baseline | Drift wins |
|---|---:|---:|---:|---:|
| Target month day 3 (previous month available) | 218.357 | 235.390 | 7.801% worse | 6/14 |
| Target month day 1 (previous month unavailable) | 370.500 | 356.064 | 3.896% better | 9/14 |
| Day 3 plus an extra publication-month lag | 370.500 | 356.064 | 3.896% better | 9/14 |

**Meaning:** model ranking reverses under different information sets, while both errors worsen when data is older. Different issuance dates also change the forecasting task. These are retrospective **scenario assumptions**, NOT verified historical publication vintages, NOT untouched test data, and NOT evidence of tradable forecasting skill.

13 local unit tests passed, including future-value invariance, date gates, and reproduction of cycle 27. The official monthly XLSX could not be downloaded, so earlier 2024-2026 monthly values remain partly transcribed and not all independently verified.

## Prospective preregistration — October 2026 monthly-average NOWCAST
Issued at **2026-10-09T02:16:42+00:00**, after October had already started. Target: World Bank Pink Sheet October 2026 gold monthly average USD/toz, expected next release November 3, 2026. Uses published data through September 2026, no October data.

- No-change forecast: **4319.000 USD/toz**
- Endpoint-drift forecast: **4416.626 USD/toz**
- Forecast status: **PENDING**; no outcome yet.
- Data CSV SHA-256: `393793d66847bc4ccbee832424bbda8b9ececb010ca4d2da0c7e090a8b4a04d7`
- Prospective JSON SHA-256: `c23a41df65af2a9a279cefec6b8d97c80480552b3f832a748f74fe7825fdc159`

**Important:** This is an October 9 mid-month nowcast, not a clean one-month-ahead forecast issued before October began. Preserve these numbers unchanged until the published outcome arrives.

Sources:
- World Bank commodity markets: https://www.worldbank.org/en/research/commodity-markets
- Official October 2 PDF: https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Pink-Sheet-October-2026.pdf

Next: independently verify official monthly data and historical publication vintages, then assess preregistered forecasts on newly released outcomes.