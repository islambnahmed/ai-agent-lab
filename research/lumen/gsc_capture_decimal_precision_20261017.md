# Lumen cycle 224 — JSON numeric precision in GSC captures (2026-10-17)

## Verified defect
The offline GSC API capture gate from cycle 223 parsed JSON decimal literals as binary floats. A syntactically fractional click count such as `40.000000000000001` rounded to Python `40.0`, passed the integer-count check, and was treated as 40 clicks. Likewise `39.99999999999999999999999` was accepted as 40. This is a false acceptance of invalid captured metrics, not a claim about real Google responses.

## Reproduction
Use the cycle-223 synthetic fixture, serialize as JSON, replace the first `"clicks":40,` with `"clicks":40.000000000000001,`, then pass through `load` and `audit`. Original v223: accepted; corrected local v224: raises `ValueError('invalid integer count')`.

## Correction and evidence
Use `json.loads(..., parse_float=Decimal)` so numeric tokens retain decimal precision, and accept counts only when exactly integral, finite, and within the existing safe bound. Convert CTR/position metrics to finite Decimal for internal consistency checks. Original 75 tests still pass; 8 new precision regressions pass; total 83/83 local. Exponent notation `4e1` and decimal trailing zeros remain accepted because they represent exact integers.

## Limitations
Local tests on synthetic captures only; no real Search Console API capture, authenticated origin, production deployment, or CI verification. The v223/v224 code and tests are kept as a local recovery bundle if GitHub publishing is blocked. Do not commit real query data or tokens.

## Priority
Do not extend the chain of synthetic-only SEO validators indefinitely. Next work should verify with authorized real captures or shift to a separate practical lab capability. Publish the correction and CI tests only if permitted by the repository tooling.
