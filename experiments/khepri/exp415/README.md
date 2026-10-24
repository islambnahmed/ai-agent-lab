# Khepri experiment 415 — Anytime-Valid Agent Evaluation

Date: 2026-10-24. Synthetic, reversible research; no live trading, external tool calls, or production rollout. Separate direction from experiments 411–414 (refresh scheduling): **sequential inference and optional stopping**.

## Question
Can an agent repeatedly inspect a benchmark and stop when it looks favorable without inflating false discoveries?

**Not with an unadjusted fixed-sample test.** We built a bounded-gain e-process to compare paired outcomes even when the agent decides when to stop.

## Protocol
For each time t, record a paired normalized gain X_t in [-1,1], where positive means candidate better. Predeclare the one-sided null:

    E[X_t | history through t-1] <= 0

For fixed lambda in [0,1), wealth E_t(lambda) = product_{i<=t}(1+lambda X_i) is a nonnegative supermartingale under this conditional null. A fixed equal-weight mixture over lambdas (.05,.1,.2,.4,.8) remains a nonnegative supermartingale. Ville's inequality ensures P(sup_t E_t >= 1/alpha) <= alpha. We use log-wealth to avoid underflow.

The comparison benchmark uses a one-sided normal-approximation p-value with known null variance 1 for Rademacher +/-1 gains, checked every five samples after n=20; this comparator is **deliberately invalid for repeated peeking** and is **not** a generic paired-data test.

## Reproduction
Python 3.10+, standard library only:

    python -m unittest -v test_anytime_eval.py
    python benchmark.py

Run in this directory. Fixed RNG seed 415, 3,000 replicates per setting, 200 sequential observations per replicate. 11/11 unit tests passed locally, including exact enumeration of all +/-1 paths through length 8 to verify expected wealth = 1.

## Results (synthetic, observed rates)
| Case | Fixed-horizon naive | Repeated-peek naive | Anytime-valid |
| --- | ---: | ---: | ---: |
| iid null, P(X=+1)=0.50 | 5.03% | 20.17% | 2.23% |
| iid beneficial, P(X=+1)=0.62 | 95.97% | 98.33% | 80.33% |

Second domain: paired binary tool success comparisons with independent Bernoulli draws each period (X = candidate success minus baseline success). At n=200: equal success .60/.60 => 1.57% rejection; candidate .72 vs baseline .52 => 91.87% rejection.

**Counterexample / invalid assumption:** A latent fair coin selects the sign for the *entire* run (all 200 gains equal +1 or all -1). The marginal mean of every X_t is zero, but the conditional mean after seeing X_1 is nonzero. The anytime rule rejects in **51.37%** of simulated runs. This does NOT refute the theorem: the conditional-null premise fails. Repeated measurements from one persistent event are not 200 independent or conditionally fair observations.

## Implications and limits
- This is a tested prototype for bounded paired agent evaluation with ongoing monitoring, **not** a universal significance test.
- Validity requires correct normalization, a prospectively fixed comparison, and the conditional mean null; adversarial selection, unobserved regime shifts, data reuse, and arbitrary retrospective selection can invalidate it.
- The mixture is conservative in finite samples; no guaranteed power advantage.
- The exact enumeration checks the martingale property under iid Rademacher; the theorem supplies validity under broader conditional-mean assumptions, not simulation alone.
- Production adoption would require domain-specific paired data contracts, pre-registration, and an audit of serial dependence and selection.

## Source integrity
Files in this branch were uploaded without changing main. Git blob SHA checks against locally tested copies:
- anytime_eval.py: ffdfcafc58435d876bf826a86efc99bee216a445
- benchmark.py: b75b62e09c53083d658e5d66e65ff1d49abcf400
- test_anytime_eval.py: 7ee0030d7f1f13852a403e6352cb9459aaa90fba
