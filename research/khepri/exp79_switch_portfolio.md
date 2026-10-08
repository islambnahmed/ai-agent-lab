# Khepri experiment 79 — pre-registered switching portfolios (2026-10-08)

## Question and change of approach
Experiment 78 found that faster forgetting reduced power under a change in context dynamics. Here the *identity of the useful context itself* changes. Can a portfolio of pre-registered switching strategies detect this without selecting the best strategy after seeing its outcome?

## Valid construction
Observations X_t are bounded in [-1,1], context C_t in {0,1} is observed before X_t, and the null requires E[X_t | F_(t-1), C_t] <= 0. For any pre-registered expert e_t in {0,1} and lambda in [0,1], the factor 1+lambda * 1{C_t=e_t} * X_t has conditional expectation <=1 and is nonnegative. Its product W_t is an e-process. Any **fixed, capital-normalized convex mixture** of such products is also an e-process. Thus P(sup_t W_t >= 20) <= 5% under the stated null, even when context distribution changes. The claim is NOT valid under marginal mean-zero alone if context is confounded (see experiment 76).

- Static portfolio: 50/50 mixture of specialists always betting when C=0 or C=1.
- Switch portfolio: 14 equally weighted experts, switching their chosen context at pre-registered times 90,120,150,180,210,240,270, both directions.
- Robust portfolio: 50/50 capital allocation to the two portfolios above.
- INVALID comparator: retrospectively select the maximum of the 16 component expert wealth processes and threshold at 20 without multiplicity adjustment.
- Global comparator: always bet on X.
- Lambda=.35, T=360, 12,000 independent paths per seed, seeds 7908 and 7919.

Under null, C is fair Bernoulli, independent of X. Nulls: symmetric X=+1/-1 equally likely, and skew X=+1 with probability .2, X=-.25 otherwise. Both have conditional mean zero. Under alternatives, the active context has P(X=+1)=(1+mu)/2; inactive context has P(X=+1)=.5. Active context either switches at t=180 or remains fixed.

## Results (crossing probabilities, seed 7908 / 7919)
| Case | Static | Switch | Robust | Posthoc max INVALID | Global |
| --- | --- | --- | --- | --- | --- |
| Symmetric null | 4.4 / 4.6% | 4.4 / 4.4% | 4.3 / 4.4% | **12.6 / 13.3%** | 4.2 / 4.4% |
| Skew null | 1.9 / 2.0% | 1.7 / 1.7% | 1.8 / 1.7% | **11.8 / 12.2%** | 3.7 / 4.2% |
| Context 0 -> 1, mu=.34 | 86.7 / 86.4% | **95.9 / 95.7%** | 95.0 / 94.6% | 98.8 / 98.7% (invalid) | 60.2 / 60.3% |
| Context 1 -> 0, mu=.34 | 86.4 / 86.9% | **95.7 / 96.0%** | 94.6 / 95.1% | 98.8 / 98.9% (invalid) | 59.5 / 59.6% |
| Stable context 0, mu=.34 | **97.0 / 96.9%** | 92.2 / 92.3% | 96.6 / 96.4% | 98.6 / 98.8% (invalid) | 60.0 / 59.6% |

## Independent stress and falsification
Additional seeds 7929/7939 with N=10,000:
- Weak signal mu=.25, switch at 180: static 57.3/58.7%, switch **71.9/72.6%**, robust 68.8/69.7%.
- Stable context, mu=.25: static **75.2/76.1%**, switch 65.1/66.3%, robust 73.8/74.0%.
- Misspecified switch at t=60 (outside grid): static 87.0/87.2%, switch 90.3/90.2%, robust **91.5/91.1%**.
- Misspecified switch at t=300: static **95.0/95.0%**, switch 92.6/92.7%, robust 94.6/94.8%.

**Exact enumeration:** all 4^8=65,536 context/sign paths under symmetric null, T=8, cut grid 2/4/6, threshold 1.5. Static 28.6865%, switch 26.9226%, robust 27.5421% (all below 1/1.5=66.67%); posthoc max **69.0582%**, exceeding 66.67%. This is an exact counterexample to unadjusted post-hoc selection.

Five local unit tests passed (exact-null bound, skew-null centering, initial capital conservation, two null simulations, reproducibility).

## Reusable lesson
When an observable context's usefulness genuinely switches, a **precommitted switch-path portfolio** can gain ~9-15 percentage points of detection power while preserving anytime validity. This improvement is NOT universal: stable or late-switching alternatives favor the static portfolio. A small robust allocation cushions both cases. The ability to *choose a strategy after observing outcomes* is NOT free: the unadjusted max produces invalid false-alarm rates. Synthetic power is not real-world deployment evidence.

## Next test
Compare against a capital-preserving predictable expert-share algorithm that reallocates based on past observations, and evaluate regret/detection delay when change times are not in the precommitted grid.
