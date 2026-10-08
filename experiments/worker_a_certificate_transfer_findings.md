# Worker A — Exact-certificate transfer to 0/1 knapsack (2026-10-08)

## Question
Does the cheap exact-certificate approach from unit-cost grid paths transfer to a different optimization task, and does its coverage survive changes in task distribution?

## Reproducibility
- Script: `experiments/worker_a_certificate_transfer.py`
- Run: `python experiments/worker_a_certificate_transfer.py` (standard library).
- Three domains, 30 items each: `packing` (value=weight), `mixed` (value correlated with weight), and `shift` (independent value, lower capacity).
- Fixed-seed evaluation: 1,500 tasks/domain; independent heldout: 4 seeds × 1,000 tasks/domain = **16,500 cases** total.
- Candidate: value/weight greedy. Independent truth: exact 0/1 dynamic programming. Certificate: if feasible candidate value equals floor of the fractional-knapsack upper bound, the candidate is **provably optimal**. Certificate does not inspect oracle labels.
- Audits: at most 10% of all tasks, selected among uncertified tasks. Compare random routing vs highest fractional upper-bound gap. Count **detected errors**, not corrected outputs.

## Heldout results (mean across four 1,000-task seeds)
| Domain | Greedy error rate | Certified fraction | Error recall: random audits | Error recall: largest-gap audits |
| --- | ---: | ---: | ---: | ---: |
| packing | 5.67% | 94.32% | 100.00%* | 100.00%* |
| mixed | 53.42% | 19.73% | 12.82% | 18.68% |
| shift | 56.05% | 9.85% | 11.07% | 17.81% |

*In packing, fewer than 10% of tasks remained uncertified, so the audit policies checked **all** uncertified tasks, using only about 5.68% of the incoming task count. The 100% recall is dataset-specific, not a general guarantee.

On the initial 1,500-task seeds, certification rates were 94.53%, 18.53%, and 11.73% respectively; the heldout seeds were independent.

## Independent checks
- Cross-checked the dynamic-programming optimum against exhaustive subset enumeration for **360** smaller (12-item) cases; all matched. In each case: greedy <= exact optimum <= fractional upper bound.
- No invalid certificates occurred across the generated samples; soundness also follows from the upper-bound proof.
- On one local Python benchmark (3,000 mixed-domain cases; five repeats), median time was ~0.040 s for greedy+certificate versus ~0.94 s for the exact DP oracle. These are implementation-specific CPU timings, not a device-level or end-to-end speedup guarantee; ranking/audit overhead is excluded.

## Interpretation
**The certificate transfers mathematically, but its *coverage* does not.** In the packing domain it proves most greedy decisions optimal, but in the shifted domain it proves fewer than 10%. This is a limitation of the relaxation/integrality gap, not evidence of false certificates. Largest-gap routing catches more errors than random routing at the same audit budget in both hard domains, but still misses >80% of all greedy errors at a 10% budget.

A safe certificate must be separated from an uncertain warning score. A lack of certificate is **not** proof of error. Avoid claiming that certificates alone solve general agent self-verification.

## Next high-value test
Investigate stronger **still-cheap** certificates (e.g. tighter admissible upper bounds or problem-specific constraints), with full compute accounting. Alternatively, test verification on tasks where the independent check is cheap but producing the solution is expensive. Pre-register failure conditions and include a distribution shift.
