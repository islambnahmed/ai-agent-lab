# Lumen: live-history session gate (2026-10-11)

Confirmed on sandbox/lumen-gold-contract-20261009: source_quality.mjs validates 165 calendar-day points, then returns all rows to forecast(). CSV import instead removes weekend rows and requires 237 weekday sessions. Therefore the live feed and CSV use incompatible horizon units. A 237-calendar-row feed may be accepted as history while representing only 169 weekdays, and a 365-calendar-row feed contains 261 weekdays.

Proposed reversible fix: validate all raw provider rows first, filter Saturday/Sunday into a session series, reject if fewer than 237 weekday observations, compute latestDate and freshness from last retained weekday, return only weekday rows. Preserve spot-only state if history fails. Add regression tests for 365 calendar rows (261 weekdays) and 237 calendar rows (169 weekdays); update the older 180-day fixtures. Weekday filtering is only a proxy, not a market-holiday calendar.

Local JavaScript red/green check: original validator returned 365 calendar rows; patched validator returned 261 weekdays; patched validator rejected the 237-calendar-row case. No GitHub CI verification yet. GitHub source update attempt was blocked, so this report does not claim code integration.
