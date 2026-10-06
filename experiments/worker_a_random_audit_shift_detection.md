# Worker A — Random audits as shift detectors, not per-decision fixes

## Question
After the warning proxy collapses on confident-wrong distribution shift, can a small random independent-audit budget rescue the architecture?

## Setup
Reuse the measured stress-test regime from `worker_a_warning_proxy_shift.py`:
- shifted error prevalence: p = 5%
- warning-proxy TPR on shifted errors: 17.4%
- warning/escalation budget: 6.65% of decisions
- independent audit is treated as a correct oracle in this first bound test

The warning path therefore catches 0.05 * 0.174 = 0.0087 of all decisions, leaving 0.0413 shifted errors per decision outside the warning path. Since 93.35% of decisions are not warning-escalated, the hidden-error prevalence inside the non-warning pool is:

q = 0.0413 / 0.9335 = 4.4242%.

Now independently audit a fraction r of the non-warning pool.

## Exact detection frontier
Per incoming decision, probability that a random audit exposes one hidden shifted error is:

d = 0.0413 * r.

Expected decisions to first detection = 1/d.
Probability of detecting at least one hidden shifted error within N decisions = 1 - (1-d)^N.

| audit r (non-warning) | total extra audit cost | expected decisions to first detection | P(detect <= 1,000 decisions) |
|---:|---:|---:|---:|
| 0.5% | 0.467% | 4,843 | 18.7% |
| 1% | 0.934% | 2,421 | 33.8% |
| 2% | 1.867% | 1,211 | 56.2% |
| 5% | 4.668% | 484 | 87.3% |

(Extra audit cost is r * 93.35% of all decisions.)

## Result
Random audits do **not** cheaply repair the shifted decisions one by one. At a 1% non-warning audit rate, about 99% of the confident-wrong cases still pass unaudited before any adaptation. Their value is different: they provide an exploration channel that can eventually reveal a new failure mode that confidence-based routing cannot see.

This changes the architecture claim:
1. warning-based escalation = exploitation of known failure signatures;
2. random independent audits = exploration for unknown/confident failure signatures;
3. audit discoveries must feed an adaptation mechanism; otherwise audits only fix the tiny sampled subset.

A fixed random-audit rate therefore has a measurable **detection-delay vs cost frontier**. Calling a tiny audit budget a direct reliability fix is misleading.

## Next falsification target
Replace the perfect independent oracle with a noisy audit source and require repeated/heterogeneous confirmations. Measure false alarms, detection delay, and cost jointly. If noisy audits make reliable shift detection too expensive, the proposed hybrid architecture loses much of its appeal.
