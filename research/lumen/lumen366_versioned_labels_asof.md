# Lumen 366 — Versioned labels, delayed arrivals, and as-of decisions (2026-10-23)

## Change of strategy
After repeated small-set aggregate-constraint experiments, this cycle tests an operational failure mode: **a label that arrives late or is later corrected can flip an evaluation decision**. This creates a reusable time-aware evaluation module rather than another overlapping-set solver variant.

## Fixture and methodology
- Reuse the eight synthetic case IDs and outcome pattern from Lumen 365: `0,0,0,1,1,1,1,0`.
- New append-only, synthetic `lumen366_events.json` has six final labels at 09:01–09:06 UTC, a delayed final C05=1 at 10:30, a provisional C07=0 at 10:31, and its correction C07=1 (final) at 11:30.
- Use three *synthetic as-of* cutoffs: 10:00, 11:00, and 12:00 UTC on 2026-10-23. Threshold: at most 40% errors is acceptable.
- Compare **naive latest-label** policy against **final-only** policy. Unknown/provisional labels are bounded pessimistically as 0 or 1, with no distributional assumptions.

| As-of (UTC) | Final-only known | Final-only error interval | Final-only decision | Naive latest decision |
| --- | ---: | ---: | --- | --- |
| 10:00 | 6/8 | 25%–50% | abstain | abstain |
| 11:00 | 7/8 | 37.5%–50% | **abstain** | **accept (37.5%)** |
| 12:00 | 8/8 | 50% | **reject** | reject |

At 11:00, the naive evaluator treats provisional C07=0 as truth and **accepts**, but the later correction makes the complete synthetic error rate 50%, above the 40% ceiling. The final-only evaluator **abstains** until the correction arrives.

## Reusable implementation
- `lumen366.py`: validates a strictly ordered, append-only event chain; rejects duplicate IDs, invalid labels/status, illegal revisions, and overwrites of already-final labels; computes as-of lower/upper error rates; defaults to final-only. The `snapshot` function validates only the historical receipt-order prefix, so future malformed records cannot change an earlier valid snapshot. `validate_ledger` separately audits the complete log.
- `lumen366_events.json`: synthetic receipt-time and correction events, including declared source role.
- `test_lumen366.py`: **16 tests passed** in normal Python and **16 passed** under `python -O`; includes **300 seeded randomized trials** comparing the bounds/decision with a separately enumerated binary-label oracle.
- Exact Git blob hashes of the published module and tests matched locally executed files: module `08263da5dafea9659a1f0b01b5383a7ee6940d73`, tests `42ef619c198e392d479b143b11ccb48a8e660beb`.
- Reproduce from `research/lumen`: `python -m unittest -v test_lumen366.py`; `python -O -m unittest -v test_lumen366.py`; `python lumen366.py`.

## What this does *not* prove
- Event timestamps and the `source` role are **self-declared synthetic fields**, not an authenticated ingestion service or independent producer.
- The labels were constructed in the same lab, and the events were published after Lumen 365's oracle. This is a reproducible **retrospective demonstration**, not an independently blinded prospective trial.
- `final` is an asserted status, not proof of correctness. If a supposedly final label is wrong, the current contract requires a new versioned evaluation rather than silently rewriting history.
- Error bounds describe the finite synthetic frame only. They do not provide statistical confidence intervals or establish real-world generalization.
- Strictly increasing timestamps are a format/invariant check; they do not prove timestamps were not backdated by their producer.

## Lessons and next experiment
1. **As-of reproducibility** must be distinct from the latest available truth; never silently backfill future corrections into historical decisions.
2. Treat provisional/missing labels as unresolved when the decision threshold lies within feasible bounds.
3. Keep full-log validation separate from historical snapshots; otherwise a future corrupt event can invalidate a past report.
4. Next useful step: an authenticated or independently reviewed event intake, explicit versioned revisions to *final* labels, and a prospective held-out benchmark. Avoid claiming independence from role names or Git commit ordering alone.
