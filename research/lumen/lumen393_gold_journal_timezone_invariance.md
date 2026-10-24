# Lumen 393 — Gold journal settlement is not invariant to equivalent timezone representations

**Date:** 2026-10-24. **Scope:** authorized `islambnahmed/ai-agent-lab` only. **Source inspected:** `main` at `8d8b4be50acc22e94882610d834e6f17b459b275`, `products/gold-forecast/journal.mjs` (blob `b24c93249059200e7a336a478ec52777640e3d29`) and `historical-integrity.mjs`/`data.mjs`. **Decision:** no model promotion, no changes to production branch or security settings.

## Verified logic defect

`settleReceipt` parses `asOf` as an absolute instant, and `prepareHistory` correctly determines completed UTC dates from that instant. But its final maturity check uses the *textual local date* instead:

```js
if (targetDate >= asOf.slice(0, 10))
  return {id: receipt.id, horizon: receipt.horizon, status: 'pending', targetDate};
```

The public timestamp parser accepts explicit timezone offsets. Thus two representations of the **same instant** can yield different maturity statuses. A completed UTC-day observation can be incorrectly left pending when `asOf` has a negative offset. This is a **false-pending / inconsistent status** defect; the UTC-day filtering in `prepareHistory` prevents the analogous premature-maturity scenario for same-day data in the tested path.

## Bounded local counterexample (2026-10-24)

I ran a Node 22.16.0 reproduction using the **unmodified `settleReceipt` control flow** copied from the source above, a synthetic 165-row prefix, a valid SHA-256 receipt hash, a horizon-1 target, and a minimal stub for `prepareHistory` that preserves its documented UTC completed-day filter. This is a **logic reproduction with a stubbed dependency, not an end-to-end execution of the repository's full product**.

| Input | Value |
|---|---|
| Synthetic origin | 2026-10-12 |
| Synthetic target observation | 2026-10-13 |
| UTC `asOf` | `2026-10-14T02:30:00.000Z` |
| Equivalent offset `asOf` | `2026-10-13T23:30:00-03:00` |
| Output for UTC representation | `matured` |
| Output for offset representation | `pending` |

The test asserted that both strings denote the same UTC instant and that the original comparison yields the divergent statuses; all assertions passed. No vendor prices, live feeds, or actual prospective outcomes were used.

## Small reversible fix proposal (not applied to main)

In `settleReceipt`, normalize all calendar-day comparisons to UTC using the already validated parsed milliseconds:

```js
const asOfUtcDay = new Date(parseInstant(asOf)).toISOString().slice(0, 10);
const issuedUtcDay = new Date(parseInstant(receipt.issuedAt)).toISOString().slice(0, 10);
// ... after selecting targetDate:
if (targetDate < issuedUtcDay) throw Error('Outcome predates issue');
if (targetDate >= asOfUtcDay) return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate};
```

The `issuedAt.slice(0,10)` comparison in the same function and the `issuedAt.slice(0,10)` use in `issueReceipt` merit equivalent UTC normalization. Add an actual product test (in `products/gold-forecast/tests/`) with 165+ synthetic daily observations, one completed target, and equivalent `Z` / negative-offset timestamps. Assert identical `matured` statuses and identical target/errors. Also test positive offsets and the exact UTC midnight boundary.

## Impact and limits

The current `scripts/journal.mjs` settlement command supplies `asOf` from the fetched manifest; the historical manifest inspected in earlier work used `Z`, so **this audit does not establish that any real settlement was misclassified**. It establishes an inconsistency in the exported settlement function for a timestamp form accepted by the project's own parser. This is separate from the larger unresolved issue: historical source vintages and prospective target observations still need independent authentication before making forecasting-skill claims.

**Follow-up:** apply the normalization in the product's owning branch after review, run its full `npm test` and GitHub CI, then confirm original-vintage h1/h7 outcomes independently. Keep h30 unscored until its conservative earliest possible completion date of 2026-11-11 UTC.
