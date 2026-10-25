# Khepri exp435 — backdated availability and ingestion provenance

2026-10-25. Offline synthetic experiment extending exp434's point-in-time feature evaluation.

## Question and method

A chronological backtest may still leak future data if a source backdates a revision's publication timestamp. We compare four feature gates:

1. **Declared**: publisher says available by decision.
2. **Ingest**: declared available and recorded ingestion by decision.
3. **Bounded-skew guard**: declared available and recorded ingestion + known maximum negative clock error (K=2) by decision.
4. **Oracle**: simulator-known true availability (not deployable).

All reject observations after decision. Walk-forward binary-stump evaluation trains only on labels mature at each fold cutoff. 360 synthetic decisions per domain/seed, 7 × 40 held-out decisions. The full offline bundle includes `audit.py`, `test_audit.py`, `stress.py`, and `results.json`; this branch also contains a small independently executable counterexample `minimal_repro.py`.

## Measured results

100 deterministic seeds × 2 domains (gold/SEO) × 4 scenarios = **800 datasets**; **224,000 held-out decisions per policy**. **13/13 unit tests passed**, including a 2,000-case bounded-skew property test. The deliberately late revisions are almost perfectly correlated with future labels.

| Domain | Backdated declared accuracy | Backdated guarded accuracy | Clock-skew unbuffered ingestion accuracy | Clock-skew guarded accuracy |
|---|---:|---:|---:|---:|
| Gold | 98.564% | 56.236% | 98.564% | 56.236% |
| SEO | 96.889% | 62.146% | 96.889% | 62.146% |

Across 100 seeds/domain, **36,000 future feature revisions** were selected by the declared-only policy in the backdated scenario; the guarded policy selected **zero**. In the clock-skew scenario, unbuffered ingestion also selected 36,000 future revisions/domain; the K=2 guard selected zero.

**Cost/counterexample:** When a revision was genuinely published before the decision but imported into the local archive afterward, the guard excluded **36,000 genuinely source-available revisions/domain**. In this scenario the gold oracle/declared score was 98.564% while the conservative guard scored 56.236%; for SEO 96.889% versus 62.146%. Whether the actual agent could have used the public data is a separate access-log question. Clean timestamp scenarios produced no difference between policies.

## Interpretation and limits

If the true ingestion time is at most K later than the recorded time, then `recorded + K <= decision` implies ingestion was not after decision. This elementary bound **does not** authenticate timestamps. Forged capture records, unbounded clock error, compromised clocks, or a falsely asserted K can defeat it. A test demonstrates forged ingestion defeats the guard. Larger K increases the rejection of legitimate recent information. This experiment uses simulated timestamps and intentionally hindsight-correlated labels, **not real SEO or gold datasets**; no production guarantees follow.

**Transferable lesson:** Track three distinct concepts—publisher-declared availability, independently witnessed ingestion, and what the agent could actually access. Report both leakage prevention and coverage loss. Reconstructing historical access requires trustworthy, append-only capture records, not a retrospective publisher timestamp alone.

Run the small on-branch counterexample: `python minimal_repro.py`.
