# Lumen audit — predictable betting is part of e-process validity

## Question
Experiments 33–38 correctly emphasize conditional assumptions and predictable bounds. A second, independent requirement is easy to miss: the betting parameter itself must be chosen before observing the current outcome.

## Exact counterexample
Let the null data be iid Rademacher:
- X_t is +1 or -1 with probability 1/2;
- therefore E[X_t | F_{t-1}] = 0 and |X_t| <= 1.

For the usual Hoeffding factor

e_t(lambda_t) = exp(lambda_t X_t - lambda_t^2 / 2),

a fixed or F_{t-1}-measurable lambda_t is legitimate.

Now make the illegal post-observation choice

lambda_t = c * sign(X_t),  with 0 < c < 2.

Then every single factor is deterministic:

e_t = exp(c - c^2/2) > 1.

Hence after n observations,

E_n = exp(n(c - c^2/2)),

so the process crosses any finite evidence threshold with probability 1 even though the data satisfy the bounded conditional-mean null exactly.

For c=1 and threshold 20, crossing occurs once exp(n/2) >= 20, i.e. at n=6. Thus the nominal alpha=0.05 test rejects the true null on every path by observation 6.

## Why this matters
"Adaptive" is not sufficient language. Safe adaptation must be predictable: lambda_t may depend on past observations but not X_t itself. The same distinction applies to bounds, model selection, feature selection, and other per-step tuning used inside a sequential evidence process.

## Review checklist
For each sequential test, record separately:
1. the conditional null/model assumption;
2. the support or moment bound;
3. the filtration/information set;
4. which quantities are required to be predictable;
5. whether any current observation leaks into those choices.

## Durable lesson
Optional-stopping validity does not protect against look-ahead inside the e-value construction. A process can use perfectly bounded, mean-zero iid data and still become maximally invalid if the bet is selected after seeing the outcome.
