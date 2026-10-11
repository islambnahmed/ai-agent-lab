# Worker A cycle 49 — market-session semantics correction (2026-10-11)

## Finding
Cycle 48's `prospective-capture.mjs` treats every UTC Saturday/Sunday as closed and any UTC Monday–Friday as potentially eligible. This is a **conservative approximation, not a verified dealer-market calendar**. Do not present it as proof that all gold instruments are closed on weekends.

## Cross-check (retrieved 2026-10-11)
- CME GC futures: Sunday 18:00 ET to Friday 17:00 ET, daily 17:00–18:00 ET maintenance; exchange holiday exceptions. Source: https://www.cmegroup.com/market-regulation/files/gold-futures-and-options-fact-card.pdf
- FOREX.com spot gold/silver: Sunday 22:00 UTC through Friday 21:00 UTC, daily 21:00–22:00 UTC maintenance (published hours at retrieval; holidays and DST can change). Source: https://www.forex.com/en/help-and-support/market-trading-hours/
- CME *1-Ounce Gold futures* are separately listed as 24/7 subject to maintenance, demonstrating that "gold market closed" is instrument-dependent. Source: https://www.cmegroup.com/markets/trade-24-7.html

## Implications
1. The `standardbullion.com` dealer-mid feed is **neither** a CME GC futures quote **nor** a verified FOREX.com spot quote. Neither calendar can be blindly imposed on it.
2. For dealer-mid observations, distinguish `session_unverified` from `provider_stale` and `blocked_known_closed`. Never infer trading activity from an API `updated` field.
3. The Sunday 2026-10-11 10:xx UTC sample remains **ineligible** for prospective scoring: it predates the stated FOREX.com Sunday opening, but that external schedule does not establish the dealer's own calendar.
4. The next high-value step is provider-specific schedule/terms verification plus first-seen capture infrastructure, not more synthetic win-rate tests.

## Readiness gates
- Provider confirms timestamp meaning and trading-session semantics for its dealer-mid quote.
- Raw response bytes and capture time retained; duplicate provider timestamps preserved as repeated polls, not fabricated independent price observations.
- Fixed protocol and full forecast ledger published **before** target; publication independently verifiable (a local hash or user-supplied Git timestamp alone is insufficient).
- At least 24 eligible, chronologically distinct historical observations; all issues and missing outcomes counted.
- Until then: **zero real prospective forecasts, zero demonstrated trading skill**.

No source or holiday calendar above is guaranteed to match the dealer feed; schedule policy must remain configurable and conservative.
