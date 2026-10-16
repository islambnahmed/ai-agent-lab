# Worker A cycle 160 — 2025 historical transfer test (2026-10-16)

Research-only, not trading advice. Fixed `worker-a-shadow-trend-v1` model (20-log-return drift, capped at +/-0.005, half drift times sqrt(h)) versus Persistence on Westmetall Gold London Fixing USD/ozt.

**Newly examined historical window:** 2025-07-01 to 2025-12-30, 128 manually transcribed published fixings. Start origin index 45, no coefficient changes, horizons count observed fixings rather than calendar days.

| Window | h | pairs | Persistence MAE | Shadow MAE | skill |
|---|---:|---:|---:|---:|---:|
| 2025 Jul-Dec | 1 | 82 | 42.697 | 42.628 | +0.16% |
| 2025 Jul-Dec | 7 | 76 | 129.388 | 123.021 | +4.92% |
| 2025 Jul-Dec | 30 | 53 | 272.193 | 253.972 | +6.69% |
| 2026 Jun-Oct | 1 | 52 | 44.389 | 44.762 | -0.84% |
| 2026 Jun-Oct | 7 | 46 | 127.580 | 125.197 | +1.87% |
| 2026 Jun-Oct | 30 | 23 | 245.887 | 284.902 | -15.87% |

2025 7-step paired mean gain +$6.37; circular moving-block bootstrap (block 7) [-$2.14,+$13.92], includes zero. 30-step mean gain +$18.22; block 17 interval [-$1.09,+$39.74], includes zero. These are descriptive sensitivity intervals, not calibrated CIs or p-values. Overlapping outcomes and nonstationarity remain.

Verification: 128 unique sorted rows; 211 2025 Python/Node.js matched gains, max difference 9.1e-13; 15/15 tests passed locally. 2025 JSON SHA256 `7fa3e049772116366be3c4100f6a325cef403648bfad891968388814c6235fb5`. Data manually transcribed, not independently ingested. The 2025 evaluation is retrospective and not prospective.

Source: https://www.westmetall.com/en/markdaten.php?action=table&field=USD_ozt_London&year=2025

Decision: **Do not promote** Shadow. Contradictory 2025/2026 30-step results motivate forward evaluation. The original 2026-10-16 prospective receipts are unchanged and pending; 2026 provider table still ended 2026-10-15 at $4,158.20 when checked 2026-10-16. No production code changes.
