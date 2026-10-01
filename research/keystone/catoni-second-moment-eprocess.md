# Finite-second-moment e-process: escaping the clipped-Hoeffding Δ^-4 rate

## Question

The previous note showed that clipping plus a Hoeffding bound gives only a worst-case log-growth guarantee of order Δ^4/M2^2. Is that loss inherent under only a second-moment bound?

No. A Catoni-style bounded-influence transform gives an anytime-valid e-process under the same conditional second-moment assumption with guaranteed log-growth of order Δ^2/M2.

## Construction

Let X_t be adapted and suppose under the null, conditionally on the past,

- E[X_t | F_{t-1}] <= 0
- E[X_t^2 | F_{t-1}] <= M2.

Define the influence function

phi(u) =
- log(1 + u + u^2/2), for u >= 0
- -log(1 - u + u^2/2), for u < 0.

For any predictable lambda_t >= 0, use the one-step factor

e_t = exp(phi(lambda_t X_t) - lambda_t^2 M2 / 2).

The elementary Catoni envelope gives

exp(phi(u)) <= 1 + u + u^2/2.

Therefore

E[e_t | F_{t-1}]
<= exp(-lambda_t^2 M2/2)
   (1 + lambda_t E[X_t|F_{t-1}] + lambda_t^2 E[X_t^2|F_{t-1}]/2)
<= exp(-a)(1+a)
<= 1,

where a=lambda_t^2 M2/2.

Hence E_t = product_{s<=t} e_s is a nonnegative supermartingale/e-process. Ville's inequality supplies anytime-valid type-I control.

## Growth under a positive mean

The same influence function satisfies the lower envelope

phi(u) >= u - u^2/2.

If under an alternative the conditional mean is at least Δ>0 while the same conditional second-moment bound holds, then for constant lambda,

E[log e_t | F_{t-1}]
>= lambda Δ - lambda^2 M2.

Optimizing the guaranteed lower bound gives

lambda* = Δ/(2 M2)

and

g* >= Δ^2/(4 M2).

Thus accumulating a fixed log-evidence level L takes, at the level of this drift guarantee,

n ~ 4 M2 L / Δ^2.

This is Δ^-2 scaling, versus the Δ^-4 worst-case guarantee derived for clipped-Hoeffding.

## What changed

The improvement is not free extra information. Clipped-Hoeffding pays twice:

1. clipping creates a bias allowance of order M2/B;
2. Hoeffding then treats the clipped observation as merely bounded by B, discarding its variance structure.

The Catoni transform handles large observations smoothly and uses the second-moment budget directly inside the e-factor. It therefore avoids choosing a clipping threshold B and avoids the bias/concentration tradeoff that caused the Δ^-4 guarantee.

## Important assumption boundary

For sequential validity, the moment statements above must be conditional on F_{t-1}. A merely unconditional statement E[X_t^2] <= M2 is not enough for the displayed one-step supermartingale proof when dependence/adaptation is allowed.

This distinction should be tested explicitly rather than hidden in notation.

## Next falsification experiment

Build a reproducible simulation with matched processes and the same conditional M2 budget:

1. clipped-Hoeffding with its oracle B for Δ;
2. multiscale clipped-Hoeffding mixture;
3. Catoni e-process with oracle lambda;
4. a predictable multiscale mixture over lambda.

Measure type-I error under optional stopping and median/quantile detection delay across decreasing Δ. Fit log(delay) versus log(Δ). The predicted slopes are approximately -4 for the conservative clipped-Hoeffding guarantee and -2 for the Catoni construction.

Also include a process satisfying only an unconditional second-moment bound but violating the conditional one, to demonstrate exactly where the sequential proof breaks.
