# Khepri Experiment 38 — Rare-bound repair: clipping is not a free fix

## Question
After Experiment 37 showed that rare violations of an assumed hard bound can destroy anytime-valid error control, can simple clipping repair the sequential test without changing what is being tested?

## Executed simulation
A fixed-lambda Hoeffding-style e-process was simulated for 20,000 paths of 250 observations, alpha=0.05, lambda=0.5.

### Case A: symmetric contamination
X is +/-1 normally, but with probability p its magnitude is 10, sign symmetric. True mean remains zero.

Observed probability of ever crossing 1/alpha:
- p=0: 3.82%
- p=0.1%: 5.455%
- p=0.5%: 10.25%
- p=1%: 16.36%

Clipping X to [-1,1] before the e-process:
- p=0.5%: 3.895%
- p=1%: 3.895%

So clipping restores the bounded-input guarantee in this symmetric case.

### Counterexample / transfer: asymmetric contamination
Construct a mean-zero distribution:
- X=10 with probability p
- X=-10p/(1-p) otherwise

Without clipping, false-alarm rates were:
- p=0.5%: 7.62%
- p=1%: 14.12%

Clipping to [-1,1] produced zero crossings in these runs, but this is NOT a repair of inference about E[X]. Clipping changes the estimand: the clipped variable has mean approximately -9p, despite the original X having mean zero. The procedure is now valid for a transformed variable, not automatically for the original mean.

## Durable lesson
A robustification step must be evaluated on two separate axes:
1. validity of the sequential evidence process after transformation;
2. preservation (or explicitly bounded distortion) of the scientific estimand.

“Clip outliers and reuse bounded-data guarantees” can restore mathematical validity while silently answering a different question.

## Next capability direction
Seek sequential evidence methods that tolerate unbounded/heavy-tailed observations under explicit moment assumptions, or derive an explicit clipping-bias envelope and include it in the null rather than pretending clipping is lossless.
